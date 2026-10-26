from __future__ import annotations

import json
from typing import Dict, List, Optional

from .models import THEMES, FeedbackRecord


class LLMAnalysisError(RuntimeError):
    """Raised when the model response cannot be validated."""


MAX_RECORDS_PER_REQUEST = 30
MAX_CHARS_PER_REQUEST = 12_000


SYSTEM_PROMPT = """你是资深用户研究分析师。你的任务是对用户反馈逐条分类，为产品团队提供可追溯的洞察。

只能使用以下主题：
稳定性与故障、使用体验、功能需求、价格与订阅、内容与效果、客户服务、隐私与安全、其他

规则：
1. 每条反馈恰好选择一个主题。
2. sentiment 只能是：正面、负面、中性、中性/建议。
3. severity 只能是：high、medium、low。数据丢失、账号安全、异常扣费、完全无法使用优先判为 high。
4. 不臆造用户没有表达的信息。
5. 只输出 JSON，不要 Markdown 代码块。

输出格式：
{
  "items": [
    {
      "id": "反馈ID",
      "theme": "主题",
      "sentiment": "负面",
      "severity": "high",
      "confidence": 0.85
    }
  ],
  "executive_summary": "不超过120字的总体结论"
}
"""


def _extract_json(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end <= start:
            raise LLMAnalysisError("模型没有返回 JSON 对象")
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMAnalysisError(f"JSON 解析失败：{exc}") from exc


def _validate_response(
    payload: dict,
    records: List[FeedbackRecord],
) -> Dict[str, Dict[str, object]]:
    items = payload.get("items")
    if not isinstance(items, list):
        raise LLMAnalysisError("响应缺少 items 数组")

    expected_ids = {record.id for record in records}
    labels: Dict[str, Dict[str, object]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        feedback_id = str(item.get("id", ""))
        theme = str(item.get("theme", ""))
        if feedback_id not in expected_ids or feedback_id in labels:
            continue
        if theme not in THEMES:
            continue
        sentiment = str(item.get("sentiment", "中性"))
        severity = str(item.get("severity", "medium"))
        try:
            confidence = float(item.get("confidence", 0.7))
        except (TypeError, ValueError):
            confidence = 0.7
        labels[feedback_id] = {
            "theme": theme,
            "sentiment": sentiment,
            "severity": severity,
            "confidence": min(max(confidence, 0), 1),
        }

    coverage = len(labels) / max(len(records), 1)
    if coverage < 0.6:
        raise LLMAnalysisError(f"有效分类覆盖不足：{coverage:.0%}")
    return labels


def _record_payload_size(record: FeedbackRecord) -> int:
    """Approximate the prompt bytes contributed by one feedback record."""
    return len(record.id) + len(record.text[:800]) + len(record.source) + 64


def _batch_records(records: List[FeedbackRecord]) -> List[List[FeedbackRecord]]:
    """Keep each model request below conservative record and character limits."""
    batches: List[List[FeedbackRecord]] = []
    batch: List[FeedbackRecord] = []
    batch_size = 0

    for record in records:
        record_size = _record_payload_size(record)
        exceeds_limits = (
            len(batch) >= MAX_RECORDS_PER_REQUEST
            or (batch and batch_size + record_size > MAX_CHARS_PER_REQUEST)
        )
        if exceeds_limits:
            batches.append(batch)
            batch = []
            batch_size = 0
        batch.append(record)
        batch_size += record_size

    if batch:
        batches.append(batch)
    return batches


def _is_payload_too_large(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    status_code = getattr(exc, "status_code", None)
    if status_code is None and response is not None:
        status_code = getattr(response, "status_code", None)
    message = str(exc).lower()
    return (
        status_code == 413
        or "payload too large" in message
        or "request entity too large" in message
        or "http 413" in message
    )


def _request_batch(
    client,
    records: List[FeedbackRecord],
    model: str,
) -> tuple[Dict[str, Dict[str, object]], Optional[str]]:
    compact_records = [
        {
            "id": record.id,
            "text": record.text[:800],
            "rating": record.rating,
            "source": record.source,
        }
        for record in records
    ]
    user_prompt = (
        "请逐条分析以下用户反馈，并严格按指定 JSON 格式返回。\n"
        + json.dumps(compact_records, ensure_ascii=False)
    )
    last_error: Optional[Exception] = None

    for attempt in range(2):
        retry_note = (
            "\n上一次输出未通过校验。请确保覆盖至少60%的反馈ID，且主题只能从给定列表选择。"
            if attempt
            else ""
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT + retry_note},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        try:
            payload = _extract_json(content)
            labels = _validate_response(payload, records)
            summary = str(payload.get("executive_summary", "")).strip() or None
            return labels, summary
        except LLMAnalysisError as exc:
            last_error = exc

    raise LLMAnalysisError(f"模型输出重试后仍无效：{last_error}")


def _analyze_batch_resiliently(
    client,
    records: List[FeedbackRecord],
    model: str,
) -> tuple[Dict[str, Dict[str, object]], Optional[str]]:
    try:
        return _request_batch(client, records, model)
    except Exception as exc:
        if not _is_payload_too_large(exc):
            raise
        if len(records) <= 1:
            raise LLMAnalysisError(
                "单条反馈仍超过模型网关的请求体限制，请缩短反馈正文后重试。"
            ) from exc

    midpoint = len(records) // 2
    left_labels, _ = _analyze_batch_resiliently(client, records[:midpoint], model)
    right_labels, _ = _analyze_batch_resiliently(client, records[midpoint:], model)
    left_labels.update(right_labels)
    return left_labels, None


def analyze_with_llm(
    records: List[FeedbackRecord],
    api_key: str,
    base_url: str = "https://api.deepseek.com",
    model: str = "deepseek-chat",
    timeout: float = 45.0,
) -> tuple[Dict[str, Dict[str, object]], Optional[str]]:
    if not api_key:
        raise LLMAnalysisError("未配置 API Key")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMAnalysisError("缺少 openai 依赖") from exc

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
    batches = _batch_records(records)
    labels: Dict[str, Dict[str, object]] = {}
    summaries: List[str] = []

    for batch in batches:
        batch_labels, summary = _analyze_batch_resiliently(client, batch, model)
        labels.update(batch_labels)
        if summary:
            summaries.append(summary)

    # Batch summaries only describe their own slice, so avoid presenting one as the
    # conclusion for the whole dataset. The caller builds a data-backed summary
    # after labels from every batch have been aggregated.
    summary = summaries[0] if len(batches) == 1 and summaries else None
    return labels, summary


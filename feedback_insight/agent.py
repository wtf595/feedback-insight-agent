from __future__ import annotations

import os
from collections import Counter
from typing import Dict, List, Optional

from .cleaning import clean_feedback
from .llm import LLMAnalysisError, analyze_with_llm
from .models import AnalysisRun, DataQuality, FeedbackRecord
from .rules import (
    analyze_with_rules,
    build_insights,
    classify_severity,
    classify_theme,
)


def _fallback_labels(records: List[FeedbackRecord]) -> Dict[str, Dict[str, object]]:
    labels: Dict[str, Dict[str, object]] = {}
    for record in records:
        theme, confidence = classify_theme(record.text)
        labels[record.id] = {
            "theme": theme,
            "confidence": confidence,
        }
    return labels


class FeedbackInsightAgent:
    """A small, auditable workflow agent with a deterministic fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        )
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    def analyze(
        self,
        records: List[FeedbackRecord],
        dataset_name: str,
        mode: str = "auto",
    ) -> AnalysisRun:
        if mode not in {"auto", "llm", "rules"}:
            raise ValueError("mode 必须是 auto、llm 或 rules")

        cleaned, dropped = clean_feedback(records)
        if not cleaned:
            raise ValueError("没有可分析的有效反馈")

        engine = "本地规则"
        engine_note = ""
        executive_summary = ""
        insights = []

        should_try_llm = mode in {"auto", "llm"} and bool(self.api_key)
        if should_try_llm:
            try:
                labels, model_summary = analyze_with_llm(
                    cleaned,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    model=self.model,
                )
                unassigned = [record for record in cleaned if record.id not in labels]
                labels.update(_fallback_labels(unassigned))
                insights = build_insights(cleaned, labels)
                engine = f"DeepSeek / {self.model}"
                engine_note = "语义分类由大模型完成；未覆盖记录用本地规则补齐。"
                executive_summary = model_summary or ""
            except (LLMAnalysisError, Exception) as exc:
                if mode == "llm":
                    engine = "本地规则（自动兜底）"
                    engine_note = f"大模型分析失败，已自动回退：{exc}"
                else:
                    engine = "本地规则"
                    engine_note = f"未使用大模型，采用可复现的本地规则：{exc}"
        elif mode == "llm":
            engine = "本地规则（自动兜底）"
            engine_note = "选择了大模型模式，但未配置 API Key，已自动回退。"
        else:
            engine_note = "当前为离线演示模式，不发送任何反馈数据。"

        if not insights:
            insights = analyze_with_rules(cleaned)

        sentiment_counts = Counter()
        for insight in insights:
            sentiment_counts[insight.sentiment] += insight.count

        ratings = [record.rating for record in cleaned if record.rating is not None]
        reviewed_evidence_ids = {
            evidence.feedback_id
            for insight in insights
            for evidence in insight.evidence
        }
        high_severity_count = sum(
            classify_severity(record, classify_theme(record.text)[0]) == "high"
            for record in cleaned
        )
        if not executive_summary:
            executive_summary = self._local_summary(
                insights, len(cleaned), high_severity_count
            )

        evidence_coverage = len(reviewed_evidence_ids) / len(cleaned)
        warnings = []
        if len(cleaned) < 10:
            warnings.append("样本少于 10 条，结论只适合作为探索性线索。")
        if len(ratings) / len(cleaned) < 0.5:
            warnings.append("评分字段覆盖不足，情绪判断主要依赖文本。")
        if any(insight.confidence < 0.5 for insight in insights):
            warnings.append("存在低置信度分类，建议人工复核证据原话。")

        review_reasons = []
        if any(insight.severity == "high" for insight in insights):
            review_reasons.append("检测到高严重度反馈，发布结论前需要人工确认。")
        if any(insight.confidence < 0.5 for insight in insights):
            review_reasons.append("部分主题置信度较低。")
        if len(cleaned) < 10:
            review_reasons.append("样本量较小。")

        return AnalysisRun(
            dataset_name=dataset_name.strip() or "未命名数据集",
            analysis_mode=mode,
            engine=engine,
            engine_note=engine_note,
            total_feedback=len(cleaned),
            sentiment_counts=dict(sentiment_counts),
            insights=insights,
            data_quality=DataQuality(
                input_count=len(records),
                valid_count=len(cleaned),
                dropped_count=dropped,
                rating_coverage=round(len(ratings) / max(len(cleaned), 1), 2),
                evidence_coverage=round(evidence_coverage, 2),
                high_severity_count=high_severity_count,
                warnings=warnings,
            ),
            executive_summary=executive_summary,
            review_required=bool(review_reasons),
            review_reasons=review_reasons,
        )

    @staticmethod
    def _local_summary(insights, total: int, high_severity_count: int) -> str:
        if not insights:
            return "当前没有形成稳定主题。"
        top = insights[0]
        risk = (
            f"，其中 {high_severity_count} 条为高严重度线索"
            if high_severity_count
            else ""
        )
        return (
            f"共分析 {total} 条有效反馈。当前最优先主题是“{top.theme}”，"
            f"占 {top.share:.0%}，优先级 {top.priority_score:.1f}/100{risk}。"
            "建议先核对代表性原话，再决定是否进入产品迭代。"
        )


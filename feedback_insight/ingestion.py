from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import FeedbackRecord


COLUMN_ALIASES = {
    "id": ["id", "反馈id", "编号", "feedback_id"],
    "text": ["text", "content", "反馈内容", "评论", "用户反馈", "内容"],
    "source": ["source", "来源", "渠道"],
    "rating": ["rating", "评分", "星级", "score"],
    "created_at": ["created_at", "date", "时间", "日期"],
    "segment": ["segment", "用户分层", "用户类型", "人群"],
}


def _find_column(fieldnames: Iterable[str], aliases: List[str]) -> Optional[str]:
    normalized = {
        str(name).strip().casefold(): name
        for name in fieldnames
        if name is not None
    }
    for alias in aliases:
        if alias.casefold() in normalized:
            return normalized[alias.casefold()]
    return None


def _decode_csv(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("无法识别 CSV 编码，请另存为 UTF-8 后重试")


def records_from_csv(data: bytes) -> List[FeedbackRecord]:
    text = _decode_csv(data)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV 缺少表头")

    mapping = {
        key: _find_column(reader.fieldnames, aliases)
        for key, aliases in COLUMN_ALIASES.items()
    }
    if not mapping["text"]:
        raise ValueError("CSV 至少需要一个“反馈内容”或 text 列")

    records = []
    for index, row in enumerate(reader):
        text_value = row.get(mapping["text"], "")
        if not str(text_value or "").strip():
            continue
        records.append(
            FeedbackRecord(
                id=row.get(mapping["id"] or "", "") or f"F{index + 1:03d}",
                text=text_value,
                source=row.get(mapping["source"] or "", "") or "未知渠道",
                rating=row.get(mapping["rating"] or "", None),
                created_at=row.get(mapping["created_at"] or "", None) or None,
                segment=row.get(mapping["segment"] or "", None) or None,
            )
        )
    return records


def records_from_lines(text: str, source: str = "手动粘贴") -> List[FeedbackRecord]:
    lines = [line.strip(" -\t") for line in str(text or "").splitlines()]
    lines = [line for line in lines if line]
    return [
        FeedbackRecord(id=f"M{index + 1:03d}", text=line, source=source)
        for index, line in enumerate(lines)
    ]


def load_csv_file(path: str | Path) -> List[FeedbackRecord]:
    return records_from_csv(Path(path).read_bytes())


from __future__ import annotations

import html
import re
from typing import Iterable, List, Tuple

from .models import FeedbackRecord


WHITESPACE_RE = re.compile(r"\s+")
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
ID_CARD_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")


def mask_pii(text: str) -> str:
    text = EMAIL_RE.sub("[邮箱已隐藏]", text)
    text = PHONE_RE.sub("[手机号已隐藏]", text)
    return ID_CARD_RE.sub("[证件号已隐藏]", text)


def clean_text(text: str) -> str:
    text = html.unescape(str(text or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = mask_pii(text)
    return WHITESPACE_RE.sub(" ", text).strip()[:2000]


def clean_feedback(records: Iterable[FeedbackRecord]) -> Tuple[List[FeedbackRecord], int]:
    cleaned: List[FeedbackRecord] = []
    seen = set()
    dropped = 0

    for index, record in enumerate(records):
        text = clean_text(record.text)
        feedback_id = record.id.strip() or f"F{index + 1:03d}"
        dedupe_key = text.casefold()
        if not text or dedupe_key in seen:
            dropped += 1
            continue
        seen.add(dedupe_key)
        cleaned.append(
            record.model_copy(
                update={
                    "id": feedback_id,
                    "text": text,
                    "source": clean_text(record.source) or "未知渠道",
                }
            )
        )

    return cleaned, dropped


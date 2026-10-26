from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


THEMES = [
    "稳定性与故障",
    "使用体验",
    "功能需求",
    "价格与订阅",
    "内容与效果",
    "客户服务",
    "隐私与安全",
    "其他",
]


class FeedbackRecord(BaseModel):
    id: str
    text: str
    source: str = "未知渠道"
    rating: Optional[float] = None
    created_at: Optional[str] = None
    segment: Optional[str] = None

    @field_validator("id", "text", "source", mode="before")
    @classmethod
    def stringify_required_fields(cls, value):
        return str(value).strip() if value is not None else ""

    @field_validator("rating", mode="before")
    @classmethod
    def parse_optional_rating(cls, value):
        if value in (None, ""):
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if 1 <= number <= 5 else None


class Evidence(BaseModel):
    feedback_id: str
    quote: str
    source: str
    rating: Optional[float] = None


class ThemeInsight(BaseModel):
    theme: str
    count: int
    share: float
    sentiment: str
    severity: str
    priority_score: float
    summary: str
    suggested_action: str
    confidence: float
    evidence: List[Evidence] = Field(default_factory=list)


class DataQuality(BaseModel):
    input_count: int
    valid_count: int
    dropped_count: int
    rating_coverage: float
    evidence_coverage: float
    high_severity_count: int = 0
    warnings: List[str] = Field(default_factory=list)


class AnalysisRun(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    dataset_name: str
    analysis_mode: str
    engine: str
    engine_note: str = ""
    total_feedback: int
    sentiment_counts: Dict[str, int]
    insights: List[ThemeInsight]
    data_quality: DataQuality
    executive_summary: str
    review_required: bool
    review_reasons: List[str] = Field(default_factory=list)
    review_status: str = "pending"
    review_note: str = ""


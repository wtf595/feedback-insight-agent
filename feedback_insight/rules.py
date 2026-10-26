from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .models import Evidence, FeedbackRecord, ThemeInsight


THEME_KEYWORDS: Dict[str, Sequence[str]] = {
    "稳定性与故障": [
        "闪退", "崩溃", "卡死", "卡顿", "打不开", "无法登录", "登录不了",
        "加载失败", "同步失败", "丢数据", "丢失", "报错", "无响应", "白屏",
        "黑屏", "加载慢", "很慢", "慢很多", "延迟", "断线", "转圈", "进度丢",
        "重新加载", "打开速度", "传不上去", "页面没有更新", "没有更新",
        "支付成功", "订单页面", "内容也没了", "同步一直失败", "失败", "空文档",
        "没有同步上去", "丢了很多",
        "BUG", "bug", "故障", "不稳定",
    ],
    "使用体验": [
        "难用", "不会用", "找不到", "看不懂", "步骤", "操作", "界面", "入口",
        "广告", "通知", "搜索", "排版", "复杂", "交互", "新手", "体验",
        "按钮", "页面", "更新后", "不方便", "字太小", "看不清", "没有引导",
        "新手引导", "不知道应该先做什么", "像迷宫", "手势操作", "挡住内容",
    ],
    "功能需求": [
        "希望增加", "能不能加", "建议增加", "缺少", "导出",
        "批量", "自动", "模板", "统计", "分类", "筛选", "自定义", "功能",
        "电脑版", "深色模式", "插件", "平板", "横屏", "手机布局", "适配",
        "扫描", "提醒时间", "共享", "search", "could",
    ],
    "价格与订阅": [
        "价格", "收费", "太贵", "会员", "订阅", "续费", "退款", "扣费",
        "自动续费", "免费", "优惠", "套餐", "付费", "性价比", "涨价",
        "年费", "原价扣", "试用期", "优惠券", "买错", "贵一倍", "免费额度",
        "取消会员",
    ],
    "内容与效果": [
        "推荐不准", "内容质量", "质量差", "内容", "模板", "结果", "不准",
        "没有效果", "效果", "答案", "生成", "错别字", "文案", "数据不对",
        "帮助不大", "很实用", "有用", "偏题", "关键决定", "没提到", "没有理解",
        "理解我的需求", "翻译", "专业术语", "结果差异", "太空洞", "全部重写",
        "实用", "清晰", "质量不错",
    ],
    "客户服务": [
        "客服", "人工", "售后", "回复慢", "没人回", "态度", "服务",
        "电话打不通", "反馈没人管", "工单", "沟通", "回复很慢", "没人处理",
        "在线咨询", "排队", "被直接断开", "回访", "处理问题", "反馈渠道",
        "联系你们", "答非所问",
    ],
    "隐私与安全": [
        "隐私", "权限", "泄露", "安全", "数据", "授权", "个人信息",
        "验证码", "账号被盗", "异地登录", "注销", "隐私政策", "共享给",
        "合作方", "删除账号", "历史数据", "清除",
    ],
}


POSITIVE_WORDS = [
    "好用", "喜欢", "满意", "方便", "流畅", "清晰", "高效", "省心", "实用",
    "不错", "推荐", "惊喜", "稳定", "快",
]
NEGATIVE_WORDS = [
    "难用", "失望", "生气", "恶心", "太差", "很差", "崩溃", "闪退", "卡顿",
    "失败", "不准", "太贵", "慢", "复杂", "找不到", "没人回", "扣费", "骗",
    "不稳定", "不好", "麻烦", "鸡肋", "退款",
]
URGENT_WORDS = [
    "崩溃", "闪退", "丢数据", "泄露", "被盗", "扣费", "无法登录", "打不开",
    "支付失败", "报警", "投诉", "退款", "严重", "紧急",
]


def _hits(text: str, words: Iterable[str]) -> List[str]:
    lowered = text.casefold()
    return [word for word in words if word.casefold() in lowered]


def classify_theme(text: str) -> Tuple[str, float]:
    scores = {}
    for theme, words in THEME_KEYWORDS.items():
        hits = _hits(text, words)
        scores[theme] = sum(2 if len(word) >= 3 else 1 for word in hits)

    if re.search(
        r"希望|能否|能不能|可不可以|如果.*(?:就|会).*|期待|建议|想要|wish i could",
        text,
        flags=re.IGNORECASE,
    ):
        scores["功能需求"] += 1

    best_theme = max(scores, key=scores.get)
    best_score = scores[best_theme]
    if best_score == 0:
        return "其他", 0.35
    ordered = sorted(scores.values(), reverse=True)
    margin = best_score - (ordered[1] if len(ordered) > 1 else 0)
    confidence = min(0.95, 0.55 + best_score * 0.04 + margin * 0.05)
    return best_theme, round(confidence, 2)


def classify_sentiment(record: FeedbackRecord) -> str:
    pos_count = len(_hits(record.text, POSITIVE_WORDS))
    neg_count = len(_hits(record.text, NEGATIVE_WORDS))

    if record.rating is not None:
        if record.rating <= 2:
            neg_count += 2
        elif record.rating >= 4:
            pos_count += 2

    if neg_count > pos_count:
        return "负面"
    if pos_count > neg_count:
        return "正面"

    has_question = bool(re.search(r"[?？]|建议|希望|能不能", record.text))
    return "中性/建议" if has_question else "中性"


def classify_severity(record: FeedbackRecord, theme: str) -> str:
    urgent_hits = _hits(record.text, URGENT_WORDS)
    if urgent_hits or (record.rating is not None and record.rating <= 1):
        return "high"
    if theme in {"稳定性与故障", "隐私与安全", "价格与订阅"}:
        return "medium"
    if record.rating is not None and record.rating <= 2:
        return "medium"
    return "low"


def _build_summary(theme: str, records: List[FeedbackRecord], negative_ratio: float) -> str:
    if len(records) == 1:
        return f"有 1 条反馈涉及{theme}，需要结合原话判断是否为个别问题。"
    tone = "集中出现负面声音" if negative_ratio >= 0.6 else "存在不同态度"
    return f"{len(records)} 条反馈涉及{theme}，{tone}，建议结合证据原话确认主要触发场景。"


def _action_for(theme: str, top_words: List[str]) -> str:
    actions = {
        "稳定性与故障": "按设备、版本和操作路径抽样复现；先建立故障清单与临时兜底方案。",
        "使用体验": "找到用户卡住的具体页面，做一次可用性走查并验证文案或入口调整。",
        "功能需求": "先访谈提出需求的用户，确认使用场景和频率，再评估投入产出。",
        "价格与订阅": "复核订阅告知、续费规则与退款路径，优先减少误解型投诉。",
        "内容与效果": "补充正反例与预期说明，抽样评估结果质量并建立人工验收标准。",
        "客户服务": "检查响应时效和转人工路径，抽取未解决对话复盘。",
        "隐私与安全": "升级为高优先级核查，确认授权范围、数据流向和账号安全记录。",
        "其他": "继续积累同类反馈，并人工标注具体问题后再决定是否立项。",
    }
    suffix = f" 当前高频线索：{'、'.join(top_words[:3])}。" if top_words else ""
    return actions.get(theme, actions["其他"]) + suffix


def _priority_score(
    theme_records: List[FeedbackRecord],
    total: int,
    sentiments: List[str],
    severities: List[str],
) -> float:
    frequency = len(theme_records) / max(total, 1) * 40
    negative_ratio = sum(s == "负面" for s in sentiments) / max(len(sentiments), 1)
    severity_ratio = sum(s == "high" for s in severities) / max(len(severities), 1)
    ratings = [r.rating for r in theme_records if r.rating is not None]
    low_rating_ratio = sum(r <= 2 for r in ratings) / len(ratings) if ratings else 0
    score = frequency + negative_ratio * 30 + severity_ratio * 20 + low_rating_ratio * 10
    return round(min(score, 100), 1)


def build_insights(
    records: List[FeedbackRecord],
    labels: Dict[str, Dict[str, object]],
) -> List[ThemeInsight]:
    buckets: Dict[str, List[FeedbackRecord]] = defaultdict(list)
    confidences: Dict[str, List[float]] = defaultdict(list)
    label_sentiments: Dict[str, str] = {}
    label_severities: Dict[str, str] = {}

    for record in records:
        label = labels.get(record.id, {})
        theme = str(label.get("theme", "其他"))
        if theme not in THEME_KEYWORDS and theme != "其他":
            theme = "其他"
        confidence = float(label.get("confidence", 0.5))
        buckets[theme].append(record)
        confidences[theme].append(confidence)
        label_sentiments[record.id] = str(label.get("sentiment", ""))
        label_severities[record.id] = str(label.get("severity", ""))

    insights: List[ThemeInsight] = []
    for theme, theme_records in buckets.items():
        sentiments = [
            label_sentiments.get(record.id) or classify_sentiment(record)
            for record in theme_records
        ]
        severities = [
            label_severities.get(record.id) or classify_severity(record, theme)
            for record in theme_records
        ]
        sentiments = [
            value if value in {"正面", "负面", "中性", "中性/建议"} else "中性"
            for value in sentiments
        ]
        severities = [
            value if value in {"high", "medium", "low"} else "medium"
            for value in severities
        ]
        sentiment = Counter(sentiments).most_common(1)[0][0]
        severity = "high" if "high" in severities else (
            "medium" if "medium" in severities else "low"
        )
        all_hits = []
        for record in theme_records:
            all_hits.extend(_hits(record.text, THEME_KEYWORDS.get(theme, [])))
        top_words = [word for word, _ in Counter(all_hits).most_common(5)]
        negative_ratio = sum(s == "负面" for s in sentiments) / len(sentiments)
        evidence = [
            Evidence(
                feedback_id=record.id,
                quote=record.text,
                source=record.source,
                rating=record.rating,
            )
            for record in sorted(
                theme_records,
                key=lambda item: (
                    classify_severity(item, theme) != "high",
                    item.rating if item.rating is not None else 6,
                ),
            )[:3]
        ]

        insights.append(
            ThemeInsight(
                theme=theme,
                count=len(theme_records),
                share=round(len(theme_records) / max(len(records), 1), 3),
                sentiment=sentiment,
                severity=severity,
                priority_score=_priority_score(
                    theme_records, len(records), sentiments, severities
                ),
                summary=_build_summary(theme, theme_records, negative_ratio),
                suggested_action=_action_for(theme, top_words),
                confidence=round(sum(confidences[theme]) / len(confidences[theme]), 2),
                evidence=evidence,
            )
        )

    return sorted(
        insights,
        key=lambda item: (item.priority_score, item.count),
        reverse=True,
    )


def analyze_with_rules(records: List[FeedbackRecord]) -> List[ThemeInsight]:
    labels: Dict[str, Dict[str, object]] = {}
    for record in records:
        theme, confidence = classify_theme(record.text)
        labels[record.id] = {
            "theme": theme,
            "confidence": confidence,
            "sentiment": classify_sentiment(record),
            "severity": classify_severity(record, theme),
        }
    return build_insights(records, labels)


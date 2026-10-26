from __future__ import annotations

import json

from .models import AnalysisRun


SEVERITY_LABELS = {"high": "高", "medium": "中", "low": "低"}


def to_json(run: AnalysisRun) -> str:
    return json.dumps(
        run.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
    )


def to_markdown(run: AnalysisRun) -> str:
    lines = [
        f"# 用户反馈洞察报告：{run.dataset_name}",
        "",
        f"- 运行编号：`{run.run_id}`",
        f"- 生成时间：{run.created_at}",
        f"- 分析引擎：{run.engine}",
        f"- 有效反馈：{run.data_quality.valid_count} 条",
        f"- 审核状态：{run.review_status}",
        "",
        "## 核心结论",
        "",
        run.executive_summary,
        "",
        "## 数据质量",
        "",
        f"- 原始输入：{run.data_quality.input_count} 条",
        f"- 清洗后：{run.data_quality.valid_count} 条",
        f"- 去重或丢弃：{run.data_quality.dropped_count} 条",
        f"- 评分覆盖率：{run.data_quality.rating_coverage:.0%}",
        f"- 证据覆盖率：{run.data_quality.evidence_coverage:.0%}",
        f"- 高严重度反馈：{run.data_quality.high_severity_count} 条",
    ]
    for warning in run.data_quality.warnings:
        lines.append(f"- 注意事项：{warning}")

    lines.extend(["", "## 优先级主题", ""])
    for index, insight in enumerate(run.insights, start=1):
        lines.extend(
            [
                f"### {index}. {insight.theme}",
                "",
                f"- 反馈数量：{insight.count}",
                f"- 占比：{insight.share:.0%}",
                f"- 主要情绪：{insight.sentiment}",
                f"- 严重度：{SEVERITY_LABELS.get(insight.severity, insight.severity)}",
                f"- 优先级：{insight.priority_score:.1f}/100",
                f"- 分类置信度：{insight.confidence:.0%}",
                "",
                f"**摘要：** {insight.summary}",
                "",
                f"**建议行动：** {insight.suggested_action}",
                "",
                "**代表原话：**",
            ]
        )
        if insight.evidence:
            for evidence in insight.evidence:
                lines.append(
                    f"> {evidence.quote}  \n"
                    f"> — {evidence.source} / {evidence.feedback_id}"
                )
        else:
            lines.append("> 当前没有可展示的代表原话。")
        lines.append("")

    lines.extend(
        [
            "## 人工审核",
            "",
            f"- 是否要求审核：{'是' if run.review_required else '否'}",
            f"- 审核状态：{run.review_status}",
            f"- 审核备注：{run.review_note or '无'}",
        ]
    )
    for reason in run.review_reasons:
        lines.append(f"- 审核原因：{reason}")

    lines.extend(
        [
            "",
            "## 边界说明",
            "",
            "本报告用于辅助发现问题和排序，不替代用户访谈或业务决策。"
            "低样本量、低置信度或高严重度结论必须经过人工复核。",
            "",
        ]
    )
    return "\n".join(lines)


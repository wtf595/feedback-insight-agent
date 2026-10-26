from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from feedback_insight.agent import FeedbackInsightAgent
from feedback_insight.ingestion import (
    load_csv_file,
    records_from_csv,
    records_from_lines,
)
from feedback_insight.models import AnalysisRun
from feedback_insight.report import to_json, to_markdown
from feedback_insight.storage import RunStore


ROOT = Path(__file__).resolve().parent
DEMO_PATH = ROOT / "data" / "demo_feedback.csv"
load_dotenv(ROOT / ".env")

st.set_page_config(
    page_title="反馈洞察 Agent",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    .hero {
        padding: 1.4rem 1.6rem;
        border: 1px solid #D9E2E8;
        border-radius: 16px;
        background: linear-gradient(120deg, #F7FAFC 0%, #ECFDF5 100%);
        margin-bottom: 1rem;
    }
    .hero h1 {font-size: 2.15rem; margin: 0 0 .35rem 0; color: #12343B;}
    .hero p {margin: 0; color: #4B6470; font-size: 1.02rem;}
    .status-card {
        border: 1px solid #DDE5EA;
        border-radius: 12px;
        background: #FFFFFF;
        padding: .9rem 1rem;
        height: 100%;
    }
    .status-label {color: #657985; font-size: .78rem; letter-spacing: .05em;}
    .status-value {color: #173D46; font-size: 1.25rem; font-weight: 700;}
    .quote {
        border-left: 3px solid #0F766E;
        padding: .35rem .75rem;
        margin: .45rem 0;
        color: #31464F;
        background: #F7FAFB;
    }
    .small-note {color: #647985; font-size: .86rem;}
    div[data-testid="stMetricValue"] {color: #123E46;}
    </style>
    """,
    unsafe_allow_html=True,
)


def get_config(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, "")
    except FileNotFoundError:
        value = ""
    return str(value or os.getenv(name, default))


def severity_label(value: str) -> str:
    return {"high": "高", "medium": "中", "low": "低"}.get(value, value)


@st.cache_data(show_spinner=False)
def load_demo_records():
    return load_csv_file(DEMO_PATH)


@st.cache_resource
def get_store():
    return RunStore()


store = get_store()
public_demo_only = get_config("PUBLIC_DEMO_ONLY").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
configured_api_key = get_config("DEEPSEEK_API_KEY")
api_key = "" if public_demo_only else configured_api_key
model = get_config("DEEPSEEK_MODEL", "deepseek-chat")
base_url = get_config("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

st.markdown(
    """
    <div class="hero">
      <h1>反馈洞察 Agent</h1>
      <p>把零散评论和客服反馈，转化为有证据、有优先级、可审核的产品行动建议。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("运行设置")
    if public_demo_only:
        mode_labels = {"本地规则（离线）": "rules"}
        mode_label = st.radio(
            "分析模式",
            list(mode_labels),
            help="公开演示已锁定为本地规则模式，不读取或调用任何模型 API。",
        )
    else:
        mode_labels = {
            "自动选择": "auto",
            "DeepSeek 语义分析": "llm",
            "本地规则（离线）": "rules",
        }
        mode_label = st.radio(
            "分析模式",
            list(mode_labels),
            help="自动选择会在有 Key 时使用 DeepSeek；失败时自动回退到本地规则。",
        )
    mode = mode_labels[mode_label]
    if public_demo_only:
        st.success("公开演示模式 · 不读取或调用任何模型 API")
    elif api_key:
        st.success(f"DeepSeek 已配置 · {model}")
    else:
        st.info("未配置 API Key，当前使用离线演示模式。")
    if public_demo_only:
        st.caption("反馈数据仅在当前本地规则流程中处理，不发送给外部模型服务。")
    else:
        st.caption("反馈数据仅在当前运行中处理；API 模式会将文本发送给模型服务。")
    st.divider()
    st.markdown("**项目边界**")
    st.caption("辅助发现问题和排序，不自动做产品决策，也不替代用户访谈。")

input_tab, insight_tab, review_tab, history_tab = st.tabs(
    ["1 · 导入反馈", "2 · 洞察报告", "3 · 人工审核", "4 · 历史记录"]
)

with input_tab:
    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.subheader("输入用户反馈")
        input_method = st.radio(
            "数据来源",
            ["使用演示数据", "上传 CSV", "粘贴文本"],
            horizontal=True,
        )
        records = []
        dataset_name = "拾光笔记 · 产品反馈演示"

        if input_method == "使用演示数据":
            records = load_demo_records()
            st.caption("演示数据为虚构产品“拾光笔记”的 36 条反馈，不含真实个人信息。")
        elif input_method == "上传 CSV":
            uploaded = st.file_uploader(
                "上传 CSV",
                type=["csv"],
                help="至少包含 text/反馈内容 列；可选 source、rating、created_at、segment。",
            )
            dataset_name = st.text_input(
                "数据集名称", value="我的用户反馈", max_chars=50
            )
            if uploaded is not None:
                try:
                    records = records_from_csv(uploaded.getvalue())
                except ValueError as exc:
                    st.error(str(exc))
        else:
            pasted = st.text_area(
                "每行一条反馈",
                height=220,
                placeholder="同步一直失败，换了网络也没用…\n希望增加批量导出功能。\n客服回复太慢了。",
            )
            dataset_name = st.text_input(
                "数据集名称", value="手动粘贴反馈", max_chars=50
            )
            records = records_from_lines(pasted)

        if records:
            preview = pd.DataFrame(
                [
                    {
                        "ID": record.id,
                        "反馈内容": record.text,
                        "来源": record.source,
                        "评分": record.rating,
                    }
                    for record in records
                ]
            )
            st.dataframe(
                preview,
                width="stretch",
                hide_index=True,
                height=310,
            )
            st.caption(f"当前可分析 {len(records)} 条反馈")

        analyze_clicked = st.button(
            "开始生成洞察",
            type="primary",
            width="stretch",
            disabled=not bool(records),
        )

        if analyze_clicked:
            with st.spinner("正在清洗反馈、识别主题并检查数据质量…"):
                try:
                    agent = FeedbackInsightAgent(
                        api_key=api_key,
                        base_url=base_url,
                        model=model,
                    )
                    run = agent.analyze(records, dataset_name, mode=mode)
                    store.save(run)
                    st.session_state["active_run_id"] = run.run_id
                    st.success(
                        f"分析完成：{len(run.insights)} 个主题，运行编号 {run.run_id}"
                    )
                except ValueError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"分析失败：{exc}")

    with right:
        st.subheader("工作流")
        st.markdown(
            """
            1. **清洗与去重**：隐藏手机号、邮箱等个人信息

            2. **主题识别**：区分故障、价格、需求等 7 类业务主题，无法归类时进入“其他”

            3. **情绪与严重度**：结合文本语义和用户评分

            4. **优先级计算**：频次、负面比例、严重度、低评分

            5. **质量门禁**：高严重度或低置信度结果进入人工审核

            6. **留痕导出**：保存版本、证据和审核意见
            """
        )
        st.divider()
        st.markdown("**为什么不是只看情感正负？**")
        st.write(
            "单纯判断“正面/负面”无法告诉团队先修什么。这个项目保留原话证据，"
            "把问题映射为产品主题，并给出可审核的优先级。"
        )

active_run_id = st.session_state.get("active_run_id")
active_run: AnalysisRun | None = store.get(active_run_id) if active_run_id else None

with insight_tab:
    if active_run is None:
        st.info("先在“导入反馈”中运行一次分析，或到“历史记录”打开已保存报告。")
    else:
        st.subheader(active_run.dataset_name)
        metric_cols = st.columns(4)
        metric_cols[0].metric("有效反馈", active_run.total_feedback)
        metric_cols[1].metric("识别主题", len(active_run.insights))
        metric_cols[2].metric(
            "最高优先级", f"{active_run.insights[0].priority_score:.1f}/100"
        )
        metric_cols[3].metric(
            "审核状态",
            {
                "pending": "待审核",
                "approved": "已通过",
                "needs_revision": "需修订",
            }.get(active_run.review_status, active_run.review_status),
        )

        st.markdown(
            f"""
            <div class="status-card">
              <div class="status-label">EXECUTIVE SUMMARY</div>
              <div style="font-size:1.05rem;margin-top:.45rem;line-height:1.75;">
                {active_run.executive_summary}
              </div>
              <div class="small-note" style="margin-top:.65rem;">
                引擎：{active_run.engine} · {active_run.engine_note}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        chart_col, quality_col = st.columns([1.25, 0.75], gap="large")
        with chart_col:
            chart_data = pd.DataFrame(
                [
                    {
                        "主题": insight.theme,
                        "优先级": insight.priority_score,
                    }
                    for insight in active_run.insights
                ]
            )
            st.markdown("**问题优先级**")
            st.bar_chart(
                chart_data.set_index("主题")["优先级"],
                width="stretch",
                height=360,
                color="#0F766E",
            )

        with quality_col:
            st.markdown("**数据质量检查**")
            st.write(
                f"评分覆盖 {active_run.data_quality.rating_coverage:.0%} · "
                f"高严重度 {active_run.data_quality.high_severity_count} 条"
            )
            if active_run.data_quality.warnings:
                for warning in active_run.data_quality.warnings:
                    st.warning(warning, icon="⚠️")
            else:
                st.success("未发现明显的数据质量风险。", icon="✅")
            if active_run.review_required:
                st.error("该结果需要人工审核后再发布。", icon="🔍")

        st.divider()
        st.subheader("按优先级查看洞察")
        for index, insight in enumerate(active_run.insights, start=1):
            title = (
                f"{index}. {insight.theme} · {insight.priority_score:.1f}/100 "
                f"· {insight.count} 条"
            )
            with st.expander(title, expanded=index <= 3):
                info_cols = st.columns(4)
                info_cols[0].caption(f"主要情绪\n\n**{insight.sentiment}**")
                info_cols[1].caption(
                    f"严重度\n\n**{severity_label(insight.severity)}**"
                )
                info_cols[2].caption(f"占比\n\n**{insight.share:.0%}**")
                info_cols[3].caption(f"置信度\n\n**{insight.confidence:.0%}**")
                st.write(insight.summary)
                st.info(f"建议行动：{insight.suggested_action}", icon="💡")
                st.markdown("**代表原话**")
                for evidence in insight.evidence:
                    quote = (
                        evidence.quote.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                    )
                    st.markdown(
                        f'<div class="quote">{quote}<br>'
                        f'<span class="small-note">— {evidence.source} / '
                        f"{evidence.feedback_id}</span></div>",
                        unsafe_allow_html=True,
                    )

        st.divider()
        download_cols = st.columns(2)
        download_cols[0].download_button(
            "下载 Markdown 报告",
            data=to_markdown(active_run),
            file_name=f"feedback-report-{active_run.run_id}.md",
            mime="text/markdown",
            width="stretch",
        )
        download_cols[1].download_button(
            "下载结构化 JSON",
            data=to_json(active_run),
            file_name=f"feedback-report-{active_run.run_id}.json",
            mime="application/json",
            width="stretch",
        )

with review_tab:
    if active_run is None:
        st.info("完成一次分析后，可在这里记录人工审核结果。")
    else:
        st.subheader("人工审核")
        st.caption(
            "AI 负责归纳和排序，人负责确认证据是否充分、行动是否合理。"
        )
        if active_run.review_reasons:
            for reason in active_run.review_reasons:
                st.warning(reason)
        else:
            st.success("本次结果未触发强制审核原因，仍建议进行抽样检查。")

        status_options = {
            "待审核": "pending",
            "审核通过": "approved",
            "需要修订": "needs_revision",
        }
        reverse_status = {value: key for key, value in status_options.items()}
        selected_status_label = st.radio(
            "审核结论",
            list(status_options),
            index=list(status_options.values()).index(active_run.review_status),
            horizontal=True,
        )
        review_note = st.text_area(
            "审核备注",
            value=active_run.review_note,
            placeholder="例如：故障主题证据充分；功能需求样本不足，暂不立项。",
        )
        if st.button("保存审核结果", type="primary"):
            updated = store.update_review(
                active_run.run_id,
                status_options[selected_status_label],
                review_note,
            )
            st.session_state["active_run_id"] = updated.run_id
            st.success("审核结果已保存。")
            st.rerun()

with history_tab:
    st.subheader("历史运行")
    runs = store.list(limit=30)
    if not runs:
        st.info("还没有历史记录。")
    else:
        history_table = pd.DataFrame(
            [
                {
                    "运行编号": run.run_id,
                    "数据集": run.dataset_name,
                    "时间": run.created_at.replace("T", " "),
                    "反馈数": run.total_feedback,
                    "引擎": run.engine,
                    "状态": {
                        "pending": "待审核",
                        "approved": "已通过",
                        "needs_revision": "需修订",
                    }.get(run.review_status, run.review_status),
                }
                for run in runs
            ]
        )
        st.dataframe(history_table, width="stretch", hide_index=True)
        run_ids = [run.run_id for run in runs]
        selected_run = st.selectbox(
            "打开一次历史运行",
            run_ids,
            format_func=lambda run_id: next(
                f"{run.dataset_name} · {run.created_at.replace('T', ' ')} · {run_id}"
                for run in runs
                if run.run_id == run_id
            ),
        )
        if st.button("打开所选报告"):
            st.session_state["active_run_id"] = selected_run
            st.success("已设为当前报告，请切换到“洞察报告”或“人工审核”。")

st.divider()
st.caption(
    "Feedback Insight Agent · 可复现规则兜底 · 证据追踪 · 人工审核 · "
    "结果仅用于辅助判断"
)


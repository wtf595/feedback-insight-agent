# 架构与设计取舍

## 目标

这个项目的首要目标不是证明复杂技术能力，而是验证一个 AI 产品运营判断：

> 大模型要进入反馈分析流程，必须同时解决归类、证据、优先级、质量门禁和人工审核，而不是只生成一段看起来合理的总结。

## 模块

| 模块 | 文件 | 职责 |
| --- | --- | --- |
| 界面 | `app.py` | 数据导入、报告展示、人工审核和历史记录 |
| 工作流 | `feedback_insight/agent.py` | 模式选择、异常兜底、质量门禁、结果组装 |
| 模型调用 | `feedback_insight/llm.py` | DeepSeek 请求、JSON 解析、结构校验和一次重试 |
| 规则兜底 | `feedback_insight/rules.py` | 关键词分类、情绪与严重度、主题聚合、优先级 |
| 数据清洗 | `feedback_insight/cleaning.py` | 去重、HTML 清理与 PII 脱敏 |
| 数据导入 | `feedback_insight/ingestion.py` | CSV 列映射与逐行文本转换 |
| 数据模型 | `feedback_insight/models.py` | 反馈、证据、洞察和运行记录 |
| 存储 | `feedback_insight/storage.py` | SQLite 持久化与审核状态变更 |
| 报告 | `feedback_insight/report.py` | Markdown 与 JSON 导出 |

## 数据流

```text
FeedbackRecord
    ↓ 清洗与脱敏
Clean FeedbackRecord[]
    ↓ DeepSeek 或规则分类
record_id → theme / sentiment / severity / confidence
    ↓ 主题聚合
ThemeInsight[]（包含代表性证据）
    ↓ 优先级与质量门禁
AnalysisRun
    ↓
SQLite / Markdown / JSON / Streamlit
```

## 模型输出校验

模型必须返回逐条分类，而不是自由生成报告：

```json
{
  "items": [
    {
      "id": "F001",
      "theme": "稳定性与故障",
      "sentiment": "负面",
      "severity": "high",
      "confidence": 0.88
    }
  ],
  "executive_summary": "总体结论"
}
```

校验规则：

1. 主题必须属于固定枚举。
2. 反馈 ID 必须存在且不能重复。
3. 有效分类覆盖率不能低于 60%。
4. 首次输出无效时，携带错误提示重试一次。
5. 第二次仍失败时，自动使用本地规则，并在界面说明原因。

## 优先级公式

```text
priority =
  frequency_share × 40
  + negative_ratio × 30
  + high_severity_ratio × 20
  + low_rating_ratio × 10
```

这是一个透明、可解释的启发式公式，不是经业务验证的因果模型。它的作用是把团队的讨论从“我感觉这个重要”推进到“我们为什么这样排序”。

## 为什么没有一开始上 LangGraph

当前流程阶段固定，重试和回退逻辑可以显式表达，使用普通 Python 更容易测试和解释。后续如果增加动态工具选择、多轮追问、跨批次重规划，再考虑引入图编排框架。

## 安全与隐私

- 本地规则模式不会向外部服务发送数据。
- 大模型模式会把清洗后的反馈文本发送给所配置的模型服务。
- 清洗阶段隐藏手机号、邮箱和身份证号，但不能替代企业级数据治理。
- `.env` 和 `.streamlit/secrets.toml` 已加入 `.gitignore`。

## 生产化前需要补的能力

- 数据接入层：客服系统、应用商店评论和问卷平台。
- 权限与租户隔离。
- 正式数据库、备份和审计。
- 异步批处理与限流。
- 主题体系配置化。
- 人工标注管理和大模型效果持续评测。


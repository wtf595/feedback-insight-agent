import unittest

from feedback_insight.agent import FeedbackInsightAgent
from feedback_insight.models import FeedbackRecord
from feedback_insight.rules import classify_theme


class AgentTests(unittest.TestCase):
    def test_theme_classifier_covers_key_cases(self):
        cases = {
            "同步失败以后数据丢了，只能重装。": "稳定性与故障",
            "更新以后入口藏在三层菜单里，很难找。": "使用体验",
            "希望增加批量导出和自定义模板。": "功能需求",
            "自动续费之前没有提醒，突然扣费了。": "价格与订阅",
            "AI 摘要总是写错重点，内容不准。": "内容与效果",
            "客服回复太慢，提交工单也没人回。": "客户服务",
            "我担心个人隐私泄露，要求通讯录权限不合理。": "隐私与安全",
        }
        for text, expected in cases.items():
            self.assertEqual(classify_theme(text)[0], expected)

    def test_agent_runs_offline_and_flags_high_severity(self):
        records = [
            FeedbackRecord(id="F1", text="同步失败，昨天的笔记全丢了。", rating=1),
            FeedbackRecord(id="F2", text="希望增加批量导出功能。", rating=4),
            FeedbackRecord(id="F3", text="界面挺清晰，用起来很方便。", rating=5),
        ]
        run = FeedbackInsightAgent(api_key="").analyze(records, "测试数据", mode="auto")

        self.assertEqual(run.total_feedback, 3)
        self.assertEqual(run.engine, "本地规则")
        self.assertTrue(run.review_required)
        self.assertEqual(run.insights[0].theme, "稳定性与故障")
        self.assertGreater(run.data_quality.evidence_coverage, 0)
        self.assertEqual(run.data_quality.high_severity_count, 1)

    def test_agent_falls_back_when_llm_requested_without_key(self):
        records = [FeedbackRecord(id="F1", text="客服一直不回复。", rating=1)]
        run = FeedbackInsightAgent(api_key="").analyze(records, "测试数据", mode="llm")

        self.assertIn("自动兜底", run.engine)
        self.assertIn("未配置 API Key", run.engine_note)


if __name__ == "__main__":
    unittest.main()


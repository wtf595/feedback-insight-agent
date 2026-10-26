import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from feedback_insight.agent import FeedbackInsightAgent
from feedback_insight.models import FeedbackRecord
from feedback_insight.report import to_json, to_markdown
from feedback_insight.storage import RunStore


def make_run():
    return FeedbackInsightAgent(api_key="").analyze(
        [
            FeedbackRecord(id="F1", text="打开就闪退，完全没法用。", rating=1),
            FeedbackRecord(id="F2", text="希望增加深色模式。", rating=4),
        ],
        "存储测试",
        mode="rules",
    )


class StorageReportTests(unittest.TestCase):
    def test_run_store_persists_and_updates_review(self):
        with TemporaryDirectory() as temp_dir:
            store = RunStore(Path(temp_dir) / "runs.db")
            run = make_run()
            store.save(run)

            loaded = store.get(run.run_id)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.dataset_name, "存储测试")

            updated = store.update_review(run.run_id, "approved", "证据已抽查")
            self.assertEqual(updated.review_status, "approved")
            self.assertEqual(store.list()[0].review_note, "证据已抽查")

    def test_markdown_and_json_export_are_traceable(self):
        run = make_run()
        markdown = to_markdown(run)
        json_report = to_json(run)

        self.assertIn("代表原话", markdown)
        self.assertIn("打开就闪退", markdown)
        self.assertIn('"review_required": true', json_report)


if __name__ == "__main__":
    unittest.main()


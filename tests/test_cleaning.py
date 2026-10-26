import unittest

from feedback_insight.cleaning import clean_feedback, clean_text
from feedback_insight.models import FeedbackRecord


class CleaningTests(unittest.TestCase):
    def test_clean_text_masks_pii_and_html(self):
        raw = "<p>联系我 13800138000 或 test@example.com</p>"
        cleaned = clean_text(raw)

        self.assertNotIn("13800138000", cleaned)
        self.assertNotIn("test@example.com", cleaned)
        self.assertNotIn("<p>", cleaned)
        self.assertIn("[手机号已隐藏]", cleaned)

    def test_clean_feedback_drops_empty_and_duplicate_rows(self):
        records = [
            FeedbackRecord(id="F1", text="同一个问题"),
            FeedbackRecord(id="F2", text="同一个问题"),
            FeedbackRecord(id="F3", text="   "),
            FeedbackRecord(id="F4", text="另一个问题"),
        ]
        cleaned, dropped = clean_feedback(records)

        self.assertEqual(len(cleaned), 2)
        self.assertEqual(dropped, 2)


if __name__ == "__main__":
    unittest.main()


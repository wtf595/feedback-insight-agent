import unittest
from unittest.mock import patch

from feedback_insight.llm import (
    MAX_CHARS_PER_REQUEST,
    _analyze_batch_resiliently,
    _batch_records,
    _is_payload_too_large,
)
from feedback_insight.models import FeedbackRecord


class LLMBatchingTests(unittest.TestCase):
    def test_batches_respect_record_limit(self):
        records = [
            FeedbackRecord(id=f"F{i}", text="反馈很短。")
            for i in range(75)
        ]

        batches = _batch_records(records)

        self.assertEqual([len(batch) for batch in batches], [30, 30, 15])
        self.assertEqual(
            [record.id for batch in batches for record in batch],
            [record.id for record in records],
        )

    def test_batches_respect_character_limit(self):
        records = [
            FeedbackRecord(id=f"F{i}", text="长" * 800)
            for i in range(20)
        ]

        batches = _batch_records(records)

        self.assertGreater(len(batches), 1)
        for batch in batches:
            approximate_size = sum(
                len(record.id) + len(record.text[:800]) + len(record.source) + 64
                for record in batch
            )
            self.assertLessEqual(approximate_size, MAX_CHARS_PER_REQUEST)

    def test_detects_payload_too_large_errors(self):
        class GatewayError(Exception):
            status_code = 413

        self.assertTrue(_is_payload_too_large(GatewayError("rejected")))
        self.assertTrue(
            _is_payload_too_large(Exception("HTTP 413 Payload Too Large"))
        )
        self.assertFalse(_is_payload_too_large(Exception("connection timeout")))

    def test_splits_a_batch_when_gateway_rejects_its_size(self):
        class GatewayError(Exception):
            status_code = 413

        records = [
            FeedbackRecord(id="F1", text="付款失败。"),
            FeedbackRecord(id="F2", text="客服不回复。"),
        ]

        def fake_request(_client, batch, _model):
            if len(batch) > 1:
                raise GatewayError("HTTP 413 Payload Too Large")
            record = batch[0]
            return {record.id: {"theme": "其他", "confidence": 0.8}}, None

        with patch("feedback_insight.llm._request_batch", side_effect=fake_request):
            labels, summary = _analyze_batch_resiliently(object(), records, "model")

        self.assertEqual(set(labels), {"F1", "F2"})
        self.assertIsNone(summary)


if __name__ == "__main__":
    unittest.main()

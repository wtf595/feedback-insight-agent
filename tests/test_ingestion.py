import unittest

from feedback_insight.ingestion import records_from_csv, records_from_lines


class IngestionTests(unittest.TestCase):
    def test_csv_supports_chinese_columns(self):
        data = "编号,反馈内容,来源,评分\n1,同步一直失败,客服,1\n".encode("utf-8")
        records = records_from_csv(data)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].id, "1")
        self.assertEqual(records[0].text, "同步一直失败")
        self.assertEqual(records[0].rating, 1)

    def test_lines_become_independent_records(self):
        records = records_from_lines("第一条反馈\n\n第二条反馈", source="访谈")

        self.assertEqual([record.id for record in records], ["M001", "M002"])
        self.assertTrue(all(record.source == "访谈" for record in records))


if __name__ == "__main__":
    unittest.main()


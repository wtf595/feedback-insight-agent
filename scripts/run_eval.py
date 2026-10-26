from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from feedback_insight.ingestion import records_from_csv  # noqa: E402
from feedback_insight.rules import classify_theme  # noqa: E402


def macro_f1(expected, predicted) -> float:
    labels = sorted(set(expected))
    scores = []
    for label in labels:
        tp = sum(e == label and p == label for e, p in zip(expected, predicted))
        fp = sum(e != label and p == label for e, p in zip(expected, predicted))
        fn = sum(e == label and p != label for e, p in zip(expected, predicted))
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        scores.append(f1)
    return sum(scores) / len(scores) if scores else 0


def main() -> None:
    relative_path = (
        sys.argv[1] if len(sys.argv) > 1 else "data/eval_feedback.csv"
    )
    path = ROOT / relative_path
    with path.open(encoding="utf-8") as handle:
        expected_by_id = {
            row["id"]: row["expected_theme"] for row in csv.DictReader(handle)
        }
    records = records_from_csv(path.read_bytes())
    expected = [expected_by_id[record.id] for record in records]
    predicted = [classify_theme(record.text)[0] for record in records]

    correct = sum(e == p for e, p in zip(expected, predicted))
    accuracy = correct / len(records)
    macro = macro_f1(expected, predicted)
    confusion = defaultdict(Counter)
    for e, p in zip(expected, predicted):
        confusion[e][p] += 1

    errors = [
        {
            "id": record.id,
            "text": record.text,
            "expected": expected_value,
            "predicted": predicted_value,
        }
        for record, expected_value, predicted_value in zip(records, expected, predicted)
        if expected_value != predicted_value
    ]
    result = {
        "dataset": relative_path,
        "sample_count": len(records),
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro, 4),
        "correct": correct,
        "errors": errors,
        "confusion": {
            expected_label: dict(counts)
            for expected_label, counts in confusion.items()
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


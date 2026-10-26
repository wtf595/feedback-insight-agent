from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import List, Optional

from .models import AnalysisRun


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "runs.db"


class RunStore:
    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        configured = db_path or os.getenv("FEEDBACK_DB_PATH") or DEFAULT_DB_PATH
        self.db_path = Path(configured)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    dataset_name TEXT NOT NULL,
                    total_feedback INTEGER NOT NULL,
                    engine TEXT NOT NULL,
                    review_status TEXT NOT NULL,
                    review_note TEXT NOT NULL DEFAULT '',
                    payload TEXT NOT NULL
                )
                """
            )

    def save(self, run: AnalysisRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO analysis_runs (
                    run_id, created_at, dataset_name, total_feedback,
                    engine, review_status, review_note, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.created_at,
                    run.dataset_name,
                    run.total_feedback,
                    run.engine,
                    run.review_status,
                    run.review_note,
                    run.model_dump_json(),
                ),
            )

    def get(self, run_id: str) -> Optional[AnalysisRun]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM analysis_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return AnalysisRun.model_validate_json(row["payload"]) if row else None

    def list(self, limit: int = 20) -> List[AnalysisRun]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload FROM analysis_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [AnalysisRun.model_validate_json(row["payload"]) for row in rows]

    def update_review(
        self,
        run_id: str,
        status: str,
        note: str,
    ) -> AnalysisRun:
        if status not in {"pending", "approved", "needs_revision"}:
            raise ValueError("不支持的审核状态")
        run = self.get(run_id)
        if run is None:
            raise KeyError(f"未找到运行记录：{run_id}")
        updated = run.model_copy(
            update={"review_status": status, "review_note": note.strip()}
        )
        self.save(updated)
        return updated


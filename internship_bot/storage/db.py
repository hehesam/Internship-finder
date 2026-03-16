"""SQLite storage layer for jobs and sent notifications."""

from __future__ import annotations

from datetime import datetime
import json
import logging
import sqlite3

from internship_bot.models.job import JobPosting
from internship_bot.utils.hashing import fingerprint_for_job


LOGGER = logging.getLogger(__name__)


class Database:
    """SQLite-backed storage for deduplicated jobs and notifications."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint TEXT NOT NULL UNIQUE,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    url TEXT NOT NULL,
                    posted_at TEXT,
                    collected_at TEXT,
                    description TEXT,
                    remote INTEGER NOT NULL DEFAULT 0,
                    source_type TEXT,
                    employment_type TEXT,
                    tags_json TEXT,
                    metadata_json TEXT,
                    score REAL NOT NULL DEFAULT 0,
                    is_match INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_is_match ON jobs(is_match);
                CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
                CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);

                CREATE TABLE IF NOT EXISTS sent_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_fingerprint TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    message_id TEXT,
                    sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_fingerprint, channel),
                    FOREIGN KEY(job_fingerprint) REFERENCES jobs(fingerprint) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sent_channel ON sent_notifications(channel);

                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT,
                    status TEXT,
                    summary_json TEXT,
                    error TEXT
                );
                """
            )
        LOGGER.info("Database initialized at %s", self.db_path)

    def save_job(self, job: JobPosting, is_match: bool) -> tuple[str, bool]:
        """Insert or update a job and return (fingerprint, is_new)."""
        fingerprint = job.fingerprint or fingerprint_for_job(job)
        job.fingerprint = fingerprint

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT 1 FROM jobs WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
            is_new = existing is None

            conn.execute(
                """
                INSERT INTO jobs (
                    fingerprint,
                    source,
                    title,
                    company,
                    location,
                    url,
                    posted_at,
                    collected_at,
                    description,
                    remote,
                    source_type,
                    employment_type,
                    tags_json,
                    metadata_json,
                    score,
                    is_match
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fingerprint) DO UPDATE SET
                    source = excluded.source,
                    title = excluded.title,
                    company = excluded.company,
                    location = excluded.location,
                    url = excluded.url,
                    posted_at = excluded.posted_at,
                    collected_at = excluded.collected_at,
                    description = excluded.description,
                    remote = excluded.remote,
                    source_type = excluded.source_type,
                    employment_type = excluded.employment_type,
                    tags_json = excluded.tags_json,
                    metadata_json = excluded.metadata_json,
                    score = excluded.score,
                    is_match = excluded.is_match,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    fingerprint,
                    job.source,
                    job.title,
                    job.company,
                    job.location,
                    job.url,
                    self._to_iso(job.posted_at),
                    self._to_iso(job.collected_at),
                    job.description,
                    int(job.remote),
                    job.source_type,
                    job.employment_type,
                    json.dumps(job.tags, ensure_ascii=False),
                    json.dumps(job.metadata, ensure_ascii=False),
                    float(job.score),
                    int(is_match),
                ),
            )

        return fingerprint, is_new

    def is_job_seen(self, fingerprint: str) -> bool:
        """Return True when a fingerprint already exists in jobs."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM jobs WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        return row is not None

    def was_notification_sent(self, fingerprint: str, channel: str = "telegram") -> bool:
        """Return True when the job was already notified on a channel."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM sent_notifications
                WHERE job_fingerprint = ? AND channel = ?
                """,
                (fingerprint, channel),
            ).fetchone()
        return row is not None

    def mark_notification_sent(
        self,
        fingerprint: str,
        channel: str = "telegram",
        message_id: str = "",
    ) -> bool:
        """Store sent notification marker.

        Returns True when a new marker is created, False when it already exists.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO sent_notifications (
                    job_fingerprint,
                    channel,
                    message_id
                )
                VALUES (?, ?, ?)
                """,
                (fingerprint, channel, message_id),
            )
            created = cursor.rowcount == 1
        return created

    def list_unsent_matching_jobs(
        self,
        channel: str = "telegram",
        limit: int = 50,
    ) -> list[JobPosting]:
        """Return matched jobs that were not sent on the given channel yet."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT j.*
                FROM jobs j
                LEFT JOIN sent_notifications s
                    ON s.job_fingerprint = j.fingerprint
                    AND s.channel = ?
                WHERE j.is_match = 1
                  AND s.id IS NULL
                ORDER BY j.score DESC, j.collected_at DESC
                LIMIT ?
                """,
                (channel, limit),
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def get_counts(self) -> dict[str, int]:
        """Return quick row counts for local debugging and smoke tests."""
        with self._connect() as conn:
            jobs_count = conn.execute("SELECT COUNT(*) AS count FROM jobs").fetchone()["count"]
            matched_count = conn.execute(
                "SELECT COUNT(*) AS count FROM jobs WHERE is_match = 1"
            ).fetchone()["count"]
            sent_count = conn.execute(
                "SELECT COUNT(*) AS count FROM sent_notifications"
            ).fetchone()["count"]
        return {
            "jobs": int(jobs_count),
            "matched_jobs": int(matched_count),
            "sent_notifications": int(sent_count),
        }

    @staticmethod
    def _to_iso(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat()

    @staticmethod
    def _from_iso(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _row_to_job(self, row: sqlite3.Row) -> JobPosting:
        tags = self._safe_json_list(row["tags_json"])
        metadata = self._safe_json_dict(row["metadata_json"])
        return JobPosting(
            source=row["source"],
            title=row["title"],
            company=row["company"],
            url=row["url"],
            location=row["location"] or "",
            posted_at=self._from_iso(row["posted_at"]),
            collected_at=self._from_iso(row["collected_at"]),
            description=row["description"] or "",
            remote=bool(row["remote"]),
            source_type=row["source_type"] or "unknown",
            employment_type=row["employment_type"] or "",
            tags=tags,
            fingerprint=row["fingerprint"],
            score=float(row["score"] or 0.0),
            metadata=metadata,
        )

    @staticmethod
    def _safe_json_list(value: str | None) -> list[str]:
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            return []
        return []

    @staticmethod
    def _safe_json_dict(value: str | None) -> dict[str, str]:
        if not value:
            return {}
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except json.JSONDecodeError:
            return {}
        return {}

"""Collector abstractions for internship sources."""

from abc import ABC, abstractmethod
import logging
from typing import Any

import requests

from internship_bot.models.job import JobPosting
from internship_bot.utils.dates import parse_datetime


LOGGER = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Defines the contract that all collectors must follow."""

    name: str = "base"

    def __init__(self, timeout_seconds: int = 20, user_agent: str | None = None) -> None:
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent or "internship-bot/1.0"

    @abstractmethod
    def collect(self) -> list[JobPosting]:
        """Fetch and normalize postings from a source."""
        raise NotImplementedError

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
            }
        )
        return session

    def _fetch_json(self, url: str) -> Any:
        with self._build_session() as session:
            response = session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.json()

    def _fetch_html(self, url: str) -> str:
        with self._build_session() as session:
            response = session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.text

    def _safe_job(
        self,
        *,
        source: str,
        title: str,
        company: str,
        location: str,
        url: str,
        posted_at_raw: str | None = None,
        description: str = "",
        remote: bool = False,
        source_type: str = "unknown",
        employment_type: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> JobPosting | None:
        try:
            return JobPosting(
                source=source,
                title=title,
                company=company,
                location=location,
                url=url,
                posted_at=parse_datetime(posted_at_raw),
                description=description,
                remote=remote,
                source_type=source_type,
                employment_type=employment_type,
                tags=tags or [],
                metadata=metadata or {},
            )
        except ValueError as error:
            LOGGER.warning("Skipping malformed job in %s: %s", self.name, error)
            return None

"""Collector for Lever-hosted job boards."""

from typing import List

from internship_bot.collectors.base import BaseCollector
from internship_bot.models.job import JobPosting


class LeverCollector(BaseCollector):
    """Collect internships from Lever endpoints."""

    name = "lever"

    def __init__(self, company_slug: str) -> None:
        self.company_slug = company_slug

    def collect(self) -> List[JobPosting]:
        """Return normalized jobs from Lever.

        TODO: Implement API fetch and normalization in Phase 6.
        """
        return []

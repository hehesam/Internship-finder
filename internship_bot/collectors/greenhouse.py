"""Collector for Greenhouse-hosted job boards."""

from typing import List

from internship_bot.collectors.base import BaseCollector
from internship_bot.models.job import JobPosting


class GreenhouseCollector(BaseCollector):
    """Collect internships from Greenhouse endpoints."""

    name = "greenhouse"

    def __init__(self, board_token: str) -> None:
        self.board_token = board_token

    def collect(self) -> List[JobPosting]:
        """Return normalized jobs from Greenhouse.

        TODO: Implement API fetch and normalization in Phase 6.
        """
        return []

"""Collector abstractions for internship sources."""

from abc import ABC, abstractmethod
from typing import List

from internship_bot.models.job import JobPosting


class BaseCollector(ABC):
    """Defines the contract that all collectors must follow."""

    name: str = "base"

    @abstractmethod
    def collect(self) -> List[JobPosting]:
        """Fetch and normalize postings from a source."""
        raise NotImplementedError

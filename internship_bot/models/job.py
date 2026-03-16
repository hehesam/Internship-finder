"""Normalized job posting model.

The full schema is finalized in Phase 3.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class JobPosting:
    """Common job data shape used across all collectors."""

    source: str
    title: str
    company: str
    url: str
    location: str = ""
    posted_at: datetime | None = None
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = ""
    remote: bool = False
    source_type: str = "unknown"
    employment_type: str = ""
    tags: list[str] = field(default_factory=list)
    fingerprint: str = ""
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.source = self.source.strip()
        self.title = self.title.strip()
        self.company = self.company.strip()
        self.location = self.location.strip()
        self.url = self.url.strip()
        self.description = self.description.strip()
        self.source_type = self.source_type.strip().lower()
        self.employment_type = self.employment_type.strip()
        self.tags = [tag.strip().lower() for tag in self.tags if tag.strip()]

        if not self.source:
            raise ValueError("JobPosting.source cannot be empty")
        if not self.title:
            raise ValueError("JobPosting.title cannot be empty")
        if not self.company:
            raise ValueError("JobPosting.company cannot be empty")
        if not self.url:
            raise ValueError("JobPosting.url cannot be empty")

    @property
    def search_blob(self) -> str:
        """Combined lowercase text used by filtering/scoring rules."""
        return " ".join(
            [
                self.title,
                self.company,
                self.location,
                self.description,
                " ".join(self.tags),
            ]
        ).lower()

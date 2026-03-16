"""Collector for Greenhouse-hosted job boards."""

import logging

from internship_bot.collectors.base import BaseCollector
from internship_bot.models.job import JobPosting


LOGGER = logging.getLogger(__name__)


class GreenhouseCollector(BaseCollector):
    """Collect internships from Greenhouse endpoints."""

    name = "greenhouse"

    def __init__(
        self,
        board_token: str,
        timeout_seconds: int = 20,
        user_agent: str | None = None,
    ) -> None:
        super().__init__(timeout_seconds=timeout_seconds, user_agent=user_agent)
        self.board_token = board_token

    def collect(self) -> list[JobPosting]:
        """Return normalized jobs from Greenhouse boards API."""
        api_url = (
            f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs?content=true"
        )
        try:
            payload = self._fetch_json(api_url)
        except Exception as error:  # noqa: BLE001
            LOGGER.warning("Greenhouse collector failed for %s: %s", self.board_token, error)
            return []
        jobs_data = payload.get("jobs", []) if isinstance(payload, dict) else []

        results: list[JobPosting] = []
        for item in jobs_data:
            if not isinstance(item, dict):
                continue

            title = item.get("title") or ""
            title_blob = title.lower()
            if "intern" not in title_blob and "research" not in title_blob:
                continue

            location = (item.get("location") or {}).get("name", "")
            metadata = {
                "greenhouse_id": str(item.get("id", "")),
                "updated_at": item.get("updated_at", ""),
            }

            job = self._safe_job(
                source=f"greenhouse:{self.board_token}",
                title=title,
                company=(item.get("company") or {}).get("name", self.board_token),
                location=location,
                url=item.get("absolute_url", ""),
                posted_at_raw=item.get("updated_at"),
                description=(item.get("content") or "")[:5000],
                remote="remote" in f"{title} {location}".lower(),
                source_type="greenhouse",
                employment_type="",
                tags=["internship", "greenhouse"],
                metadata=metadata,
            )
            if job is None:
                continue
            results.append(job)

        return results

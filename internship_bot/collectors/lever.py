"""Collector for Lever-hosted job boards."""

from datetime import datetime, timezone
import logging

from internship_bot.collectors.base import BaseCollector
from internship_bot.models.job import JobPosting


LOGGER = logging.getLogger(__name__)


class LeverCollector(BaseCollector):
    """Collect internships from Lever endpoints."""

    name = "lever"

    def __init__(
        self,
        company_slug: str,
        timeout_seconds: int = 20,
        user_agent: str | None = None,
    ) -> None:
        super().__init__(timeout_seconds=timeout_seconds, user_agent=user_agent)
        self.company_slug = company_slug

    def collect(self) -> list[JobPosting]:
        """Return normalized jobs from Lever postings API."""
        api_url = f"https://api.lever.co/v0/postings/{self.company_slug}?mode=json"
        try:
            payload = self._fetch_json(api_url)
        except Exception as error:  # noqa: BLE001
            LOGGER.warning("Lever collector failed for %s: %s", self.company_slug, error)
            return []
        if not isinstance(payload, list):
            return []

        results: list[JobPosting] = []
        for item in payload:
            if not isinstance(item, dict):
                continue

            title = item.get("text", "")
            title_blob = title.lower()
            if "intern" not in title_blob and "research" not in title_blob:
                continue

            categories = item.get("categories") or {}
            location = categories.get("location", "") if isinstance(categories, dict) else ""
            team = categories.get("team", "") if isinstance(categories, dict) else ""

            metadata = {
                "lever_id": str(item.get("id", "")),
                "team": team,
                "workplace_type": item.get("workplaceType", ""),
            }

            posted_at_raw = self._to_posted_at(item.get("createdAt"))

            job = self._safe_job(
                source=f"lever:{self.company_slug}",
                title=title,
                company=self.company_slug,
                location=location,
                url=item.get("hostedUrl", ""),
                posted_at_raw=posted_at_raw,
                description=item.get("descriptionPlain", "")[:5000],
                remote="remote" in f"{title} {location} {item.get('workplaceType', '')}".lower(),
                source_type="lever",
                employment_type=categories.get("commitment", "") if isinstance(categories, dict) else "",
                tags=["internship", "lever", team] if team else ["internship", "lever"],
                metadata=metadata,
            )
            if job is None:
                continue
            results.append(job)

        return results

    @staticmethod
    def _to_posted_at(value: object) -> str | None:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            seconds = float(value)
            if seconds > 1_000_000_000_000:
                seconds /= 1000.0
            try:
                return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
            except (ValueError, OSError, OverflowError):
                return None

        if isinstance(value, str):
            return value

        return None

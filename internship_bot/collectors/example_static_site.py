"""Example collector for static HTML internship pages."""

import logging
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from internship_bot.collectors.base import BaseCollector
from internship_bot.models.job import JobPosting


LOGGER = logging.getLogger(__name__)


class ExampleStaticSiteCollector(BaseCollector):
    """Generic collector for static HTML pages.

    Assumption: job links are available as <a href="..."> elements.
    """

    name = "example_static_site"

    def __init__(
        self,
        source_url: str,
        company_name: str = "Unknown Company",
        timeout_seconds: int = 20,
        user_agent: str | None = None,
    ) -> None:
        super().__init__(timeout_seconds=timeout_seconds, user_agent=user_agent)
        self.source_url = source_url
        self.company_name = company_name

    def collect(self) -> list[JobPosting]:
        """Return normalized jobs from a static HTML page.

        This generic implementation favors robustness over perfect extraction.
        Site-specific selectors can be added later when needed.
        """
        try:
            html = self._load_source_html(self.source_url)
        except Exception as error:  # noqa: BLE001
            LOGGER.warning("Static collector failed for %s: %s", self.source_url, error)
            return []

        soup = BeautifulSoup(html, "html.parser")

        postings: list[JobPosting] = []
        seen_urls: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href:
                continue

            absolute_url = self._resolve_job_url(href)
            url_lower = absolute_url.lower()

            if absolute_url in seen_urls:
                continue

            text = anchor.get_text(" ", strip=True)
            candidate_text = f"{text} {url_lower}".lower()
            if "intern" not in candidate_text and "research" not in candidate_text:
                continue

            parent_text = anchor.parent.get_text(" ", strip=True) if anchor.parent else ""
            title = text or parent_text or "Internship"
            location = self._extract_location_hint(parent_text)

            job = self._safe_job(
                source=f"static:{self.source_url}",
                title=title,
                company=self.company_name,
                location=location,
                url=absolute_url,
                posted_at_raw=None,
                description=parent_text,
                remote="remote" in candidate_text,
                source_type="static_html",
                tags=["internship"],
                metadata={"source_url": self.source_url},
            )
            if job is None:
                continue

            postings.append(job)
            seen_urls.add(absolute_url)

        return postings

    def _load_source_html(self, source: str) -> str:
        if self._is_local_source(source):
            source_path = self._to_local_path(source)
            return source_path.read_text(encoding="utf-8")
        return self._fetch_html(source)

    def _resolve_job_url(self, href: str) -> str:
        if href.startswith(("http://", "https://")):
            return href

        if self._is_local_source(self.source_url):
            base_path = self._to_local_path(self.source_url).parent
            local_href = href.lstrip("/")
            resolved = (base_path / local_href).resolve()
            return resolved.as_uri()

        return urljoin(self.source_url, href)

    @staticmethod
    def _is_local_source(source: str) -> bool:
        if source.startswith("file://"):
            return True
        parsed = urlparse(source)
        if parsed.scheme in {"http", "https"}:
            return False
        return Path(source).exists()

    @staticmethod
    def _to_local_path(source: str) -> Path:
        if source.startswith("file://"):
            return Path(source.replace("file://", "", 1)).resolve()
        return Path(source).resolve()

    @staticmethod
    def _extract_location_hint(text: str) -> str:
        if not text:
            return ""
        lowered = text.lower()
        candidates = [
            "remote",
            "germany",
            "switzerland",
            "netherlands",
            "europe",
            "eu",
        ]
        for candidate in candidates:
            if candidate in lowered:
                return candidate.title()
        return ""

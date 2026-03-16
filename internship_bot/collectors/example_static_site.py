"""Example collector for static HTML internship pages."""

from typing import List

from internship_bot.collectors.base import BaseCollector
from internship_bot.models.job import JobPosting


class ExampleStaticSiteCollector(BaseCollector):
    """Template collector using requests + BeautifulSoup in later phase."""

    name = "example_static_site"

    def __init__(self, source_url: str) -> None:
        self.source_url = source_url

    def collect(self) -> List[JobPosting]:
        """Return normalized jobs from a static HTML page.

        TODO: Implement real fetching/parsing in Phase 6.
        """
        return []

"""Telegram notification helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

import requests

from internship_bot.config import TelegramConfig
from internship_bot.models.job import JobPosting


LOGGER = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result object for one notification attempt."""

    success: bool
    message_id: str = ""
    error: str = ""


def format_job_message(job: JobPosting) -> str:
    """Build a clean text message for Telegram."""
    posted_at = _format_datetime(job.posted_at)
    location = job.location or "Unknown"
    source = job.source or "unknown"

    lines = [
        "🚀 New Internship Match",
        f"Title: {job.title}",
        f"Company: {job.company}",
        f"Location: {location}",
        f"Source: {source}",
        f"Posted: {posted_at}",
        f"Score: {job.score:.2f}",
        f"URL: {job.url}",
    ]
    return "\n".join(lines)


class TelegramNotifier:
    """Sends internship notifications to Telegram (or dry-run output)."""

    def __init__(
        self,
        telegram_config: TelegramConfig,
        timeout_seconds: int = 20,
    ) -> None:
        self.telegram_config = telegram_config
        self.timeout_seconds = timeout_seconds

    def send_job_notification(self, job: JobPosting) -> NotificationResult:
        """Send one job notification."""
        message = format_job_message(job)

        if self.telegram_config.dry_run:
            print("[dry-run][telegram] Message preview:")
            print(message)
            return NotificationResult(success=True, message_id="dry-run")

        endpoint = f"https://api.telegram.org/bot{self.telegram_config.bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_config.chat_id,
            "text": message,
            "disable_web_page_preview": False,
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as error:
            LOGGER.error("Telegram send failed: %s", error)
            return NotificationResult(success=False, error=str(error))

        if not data.get("ok"):
            description = str(data.get("description", "unknown Telegram API error"))
            LOGGER.error("Telegram API returned error: %s", description)
            return NotificationResult(success=False, error=description)

        message_id = str((data.get("result") or {}).get("message_id", ""))
        return NotificationResult(success=True, message_id=message_id)

    def send_job_notifications(self, jobs: list[JobPosting]) -> list[NotificationResult]:
        """Send multiple jobs in sequence."""
        return [self.send_job_notification(job) for job in jobs]


def send_job_notification(job: JobPosting, telegram_config: TelegramConfig) -> bool:
    """Compatibility helper returning only success boolean."""
    notifier = TelegramNotifier(telegram_config=telegram_config)
    return notifier.send_job_notification(job).success


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "Unknown"
    return value.strftime("%Y-%m-%d %H:%M UTC")

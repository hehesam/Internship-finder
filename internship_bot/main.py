"""Entry point for the internship monitoring pipeline."""

import logging

from internship_bot.collectors.base import BaseCollector
from internship_bot.collectors.example_static_site import ExampleStaticSiteCollector
from internship_bot.collectors.greenhouse import GreenhouseCollector
from internship_bot.collectors.lever import LeverCollector
from internship_bot.config import AppConfig, load_config
from internship_bot.filters.rules import evaluate_job
from internship_bot.filters.scoring import compute_job_score
from internship_bot.notifier.telegram import TelegramNotifier
from internship_bot.storage.db import Database
from internship_bot.utils.logging_config import setup_logging


LOGGER = logging.getLogger(__name__)


def build_collectors(config: AppConfig) -> list[BaseCollector]:
    """Build enabled collectors from app config."""
    collectors: list[BaseCollector] = []

    if config.toggles.enable_static_example:
        for source_url in config.sources.static_source_urls:
            collectors.append(
                ExampleStaticSiteCollector(
                    source_url=source_url,
                    timeout_seconds=config.collector_timeout_seconds,
                    user_agent=config.collector_user_agent,
                )
            )

    if config.toggles.enable_greenhouse:
        for board_token in config.sources.greenhouse_board_tokens:
            collectors.append(
                GreenhouseCollector(
                    board_token=board_token,
                    timeout_seconds=config.collector_timeout_seconds,
                    user_agent=config.collector_user_agent,
                )
            )

    if config.toggles.enable_lever:
        for company_slug in config.sources.lever_company_slugs:
            collectors.append(
                LeverCollector(
                    company_slug=company_slug,
                    timeout_seconds=config.collector_timeout_seconds,
                    user_agent=config.collector_user_agent,
                )
            )

    return collectors


def run_pipeline(config: AppConfig) -> None:
    """Run end-to-end internship pipeline orchestration."""
    LOGGER.info("Pipeline started")
    LOGGER.info("Database path: %s", config.database_path)
    LOGGER.info(
        "Sources enabled: static=%s greenhouse=%s lever=%s",
        config.toggles.enable_static_example,
        config.toggles.enable_greenhouse,
        config.toggles.enable_lever,
    )
    LOGGER.info(
        "Collector runtime: timeout=%ss user_agent=%s",
        config.collector_timeout_seconds,
        config.collector_user_agent,
    )
    LOGGER.info(
        "Telegram mode: %s",
        "dry-run" if config.telegram.dry_run else "live",
    )

    db = Database(config.database_path)
    db.initialize()

    collectors = build_collectors(config)
    LOGGER.info("Collectors built: %s", len(collectors))

    summary: dict[str, int] = {
        "collector_errors": 0,
        "collected_jobs": 0,
        "stored_jobs": 0,
        "new_jobs": 0,
        "matched_jobs": 0,
        "unsent_matches": 0,
        "notifications_attempted": 0,
        "notifications_sent": 0,
        "notifications_failed": 0,
    }

    for collector in collectors:
        try:
            jobs = collector.collect()
        except Exception as error:  # noqa: BLE001
            summary["collector_errors"] += 1
            LOGGER.exception("Collector crashed (%s): %s", collector.name, error)
            continue

        summary["collected_jobs"] += len(jobs)
        LOGGER.info("Collector %s returned %s jobs", collector.name, len(jobs))

        for job in jobs:
            decision = evaluate_job(job, config.filters)
            breakdown = compute_job_score(
                job,
                config.filters,
                config.scoring,
                decision=decision,
            )
            job.score = breakdown.total_score

            fingerprint, is_new = db.save_job(job, is_match=decision.is_match)
            job.fingerprint = fingerprint

            summary["stored_jobs"] += 1
            if is_new:
                summary["new_jobs"] += 1
            if decision.is_match:
                summary["matched_jobs"] += 1

    unsent_matches = db.list_unsent_matching_jobs(channel="telegram", limit=200)
    summary["unsent_matches"] = len(unsent_matches)
    LOGGER.info("Unsent matching jobs: %s", len(unsent_matches))

    notifier = TelegramNotifier(config.telegram, timeout_seconds=config.collector_timeout_seconds)
    for job in unsent_matches:
        summary["notifications_attempted"] += 1
        result = notifier.send_job_notification(job)
        if result.success:
            db.mark_notification_sent(
                job.fingerprint,
                channel="telegram",
                message_id=result.message_id,
            )
            summary["notifications_sent"] += 1
            LOGGER.info("Notification sent for %s (%s)", job.title, job.fingerprint)
        else:
            summary["notifications_failed"] += 1
            LOGGER.error(
                "Notification failed for %s (%s): %s",
                job.title,
                job.fingerprint,
                result.error,
            )

    counts = db.get_counts()
    LOGGER.info(
        "Run summary | collected=%s stored=%s new=%s matched=%s unsent=%s sent=%s failed=%s collector_errors=%s",
        summary["collected_jobs"],
        summary["stored_jobs"],
        summary["new_jobs"],
        summary["matched_jobs"],
        summary["unsent_matches"],
        summary["notifications_sent"],
        summary["notifications_failed"],
        summary["collector_errors"],
    )
    LOGGER.info(
        "DB totals | jobs=%s matched=%s sent_notifications=%s",
        counts["jobs"],
        counts["matched_jobs"],
        counts["sent_notifications"],
    )


def main() -> None:
    """Initialize config and logging, then execute pipeline."""
    config = load_config()
    setup_logging(config.log_level)
    run_pipeline(config)


if __name__ == "__main__":
    main()

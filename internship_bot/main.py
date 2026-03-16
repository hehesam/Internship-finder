"""Entry point for the internship monitoring pipeline."""

from internship_bot.config import AppConfig, load_config
from internship_bot.storage.db import Database
from internship_bot.utils.logging_config import setup_logging


def run_pipeline(config: AppConfig) -> None:
    """Run a placeholder pipeline for scaffold validation.

    Full orchestration is implemented in Phase 8.
    """
    print("[scaffold] Pipeline placeholder initialized.")
    print(f"[scaffold] Database path: {config.database_path}")
    print(f"[scaffold] Dry run mode: {config.telegram.dry_run}")
    print(
        "[scaffold] Sources enabled: "
        f"static={config.toggles.enable_static_example}, "
        f"greenhouse={config.toggles.enable_greenhouse}, "
        f"lever={config.toggles.enable_lever}"
    )
    print(
        "[scaffold] Filter keywords: "
        f"include={len(config.filters.include_keywords)}, "
        f"exclude={len(config.filters.exclude_keywords)}, "
        f"locations={len(config.filters.preferred_locations)}"
    )

    db = Database(config.database_path)
    db.initialize()
    counts = db.get_counts()
    print(
        "[scaffold] DB summary: "
        f"jobs={counts['jobs']}, "
        f"matched={counts['matched_jobs']}, "
        f"sent={counts['sent_notifications']}"
    )


def main() -> None:
    """Initialize config and logging, then execute pipeline."""
    config = load_config()
    setup_logging(config.log_level)
    run_pipeline(config)


if __name__ == "__main__":
    main()

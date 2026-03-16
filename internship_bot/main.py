"""Entry point for the internship monitoring pipeline."""

from internship_bot.config import AppConfig, load_config
from internship_bot.filters.rules import evaluate_job
from internship_bot.filters.scoring import compute_job_score
from internship_bot.models.job import JobPosting
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

    sample_jobs = [
        JobPosting(
            source="demo",
            title="AI Research Internship - Computer Vision",
            company="VisionLab",
            location="Zurich, Switzerland",
            url="https://example.org/jobs/ai-research-intern",
            description="Remote-friendly multimodal AI internship focused on research.",
            remote=True,
            tags=["ai", "research", "computer vision"],
        ),
        JobPosting(
            source="demo",
            title="Software Engineering Intern",
            company="GeneralApps",
            location="Berlin, Germany",
            url="https://example.org/jobs/se-intern",
            description="General backend internship.",
            remote=False,
            tags=["backend"],
        ),
        JobPosting(
            source="demo",
            title="Senior ML Engineer",
            company="BigAI",
            location="Amsterdam, Netherlands",
            url="https://example.org/jobs/senior-ml",
            description="Senior machine learning role (not internship).",
            remote=True,
            tags=["machine learning"],
        ),
    ]

    print("[scaffold] Filter/score demo:")
    for job in sample_jobs:
        decision = evaluate_job(job, config.filters)
        breakdown = compute_job_score(job, config.filters, config.scoring, decision=decision)
        job.score = breakdown.total_score
        print(
            "  - "
            f"{job.title} | match={decision.is_match} | score={job.score:.2f} "
            f"| include_hits={breakdown.include_keyword_hits} "
            f"| location_bonus={breakdown.preferred_location_bonus:.1f} "
            f"| remote_bonus={breakdown.remote_bonus:.1f} "
            f"| research_bonus={breakdown.research_bonus:.1f}"
        )


def main() -> None:
    """Initialize config and logging, then execute pipeline."""
    config = load_config()
    setup_logging(config.log_level)
    run_pipeline(config)


if __name__ == "__main__":
    main()

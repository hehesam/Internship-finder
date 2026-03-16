"""Telegram notification helper placeholders."""

from internship_bot.models.job import JobPosting


def send_job_notification(job: JobPosting, dry_run: bool = True) -> bool:
    """Send a notification for one job.

    TODO: Implement Telegram API sending in Phase 7.
    """
    if dry_run:
        print(f"[dry-run] Would send: {job.title} @ {job.company}")
        return True

    return False

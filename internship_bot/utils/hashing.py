"""Hashing helpers for stable job fingerprints."""

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from internship_bot.models.job import JobPosting


def stable_hash(value: str) -> str:
    """Return SHA256 hash for deterministic deduplication keys."""
    normalized = value.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_url(url: str) -> str:
    """Normalize URL for stable deduplication comparisons."""
    raw = (url or "").strip()
    if not raw:
        return ""

    try:
        parts = urlsplit(raw)
    except ValueError:
        return raw.lower().rstrip("/")

    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]

    normalized = urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            urlencode(filtered_query, doseq=True),
            "",
        )
    )
    return normalized


def fingerprint_for_job(job: JobPosting) -> str:
    """Prefer URL-based fingerprint; fallback to stable hash of core fields."""
    normalized_url = normalize_url(job.url)
    if normalized_url:
        return f"url:{normalized_url}"

    posted = job.posted_at.isoformat() if job.posted_at else ""
    fallback = "|".join(
        [
            job.source.strip().lower(),
            job.title.strip().lower(),
            job.company.strip().lower(),
            job.location.strip().lower(),
            posted,
        ]
    )
    return f"hash:{stable_hash(fallback)}"

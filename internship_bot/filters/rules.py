"""Rule-based filtering helpers.

Detailed include/exclude and location logic is implemented in Phase 5.
"""

from dataclasses import dataclass

from internship_bot.config import FilterConfig
from internship_bot.models.job import JobPosting


@dataclass
class FilterDecision:
    """Structured output for filter evaluation."""

    is_match: bool
    matched_include_keywords: list[str]
    matched_exclude_keywords: list[str]
    matched_locations: list[str]
    remote_detected: bool
    reasons: list[str]


def _match_keywords(text: str, keywords: list[str]) -> list[str]:
    normalized_text = text.lower()
    return [keyword for keyword in keywords if keyword.lower() in normalized_text]


def evaluate_job(job: JobPosting, filter_config: FilterConfig) -> FilterDecision:
    """Evaluate a job using include/exclude/location rules.

    Matching logic:
    1) Fail if any exclude keyword is present.
    2) Pass include rule when include list is empty OR at least one include keyword matches.
    3) Pass location rule when preferred location list is empty OR a location matches
       OR remote is detected.
    """
    text_blob = job.search_blob
    matched_include = _match_keywords(text_blob, filter_config.include_keywords)
    matched_exclude = _match_keywords(text_blob, filter_config.exclude_keywords)
    matched_locations = _match_keywords(text_blob, filter_config.preferred_locations)
    remote_detected = job.remote or "remote" in text_blob

    include_ok = not filter_config.include_keywords or bool(matched_include)
    exclude_ok = not matched_exclude
    location_ok = (
        not filter_config.preferred_locations
        or bool(matched_locations)
        or remote_detected
    )

    reasons: list[str] = []
    if include_ok:
        reasons.append("include-rule-pass")
    else:
        reasons.append("include-rule-fail")

    if exclude_ok:
        reasons.append("exclude-rule-pass")
    else:
        reasons.append("exclude-rule-fail")

    if location_ok:
        reasons.append("location-rule-pass")
    else:
        reasons.append("location-rule-fail")

    return FilterDecision(
        is_match=include_ok and exclude_ok and location_ok,
        matched_include_keywords=matched_include,
        matched_exclude_keywords=matched_exclude,
        matched_locations=matched_locations,
        remote_detected=remote_detected,
        reasons=reasons,
    )


def is_job_relevant(job: JobPosting, filter_config: FilterConfig) -> bool:
    """Backward-friendly helper that returns only pass/fail."""
    return evaluate_job(job, filter_config).is_match

"""Scoring helpers for ranking internships."""

from dataclasses import dataclass

from internship_bot.config import FilterConfig, ScoringConfig
from internship_bot.filters.rules import FilterDecision, evaluate_job
from internship_bot.models.job import JobPosting


@dataclass
class ScoreBreakdown:
    """Numeric explanation of a job score."""

    include_keyword_hits: int
    include_keyword_score: float
    preferred_location_bonus: float
    remote_bonus: float
    research_bonus: float
    total_score: float


def _has_research_signal(job: JobPosting) -> bool:
    text_blob = job.search_blob
    research_terms = ["research", "research internship", "thesis", "lab"]
    return any(term in text_blob for term in research_terms)


def compute_job_score(
    job: JobPosting,
    filter_config: FilterConfig,
    scoring_config: ScoringConfig,
    decision: FilterDecision | None = None,
) -> ScoreBreakdown:
    """Compute score using simple additive rules.

    Formula:
    total_score =
      (include_keyword_hits * include_keyword_weight)
      + preferred_location_bonus_if_matched
      + remote_bonus_if_remote
      + research_bonus_if_research_signal
    """
    filter_decision = decision or evaluate_job(job, filter_config)

    include_hits = len(filter_decision.matched_include_keywords)
    include_score = include_hits * scoring_config.include_keyword_weight
    location_bonus = (
        scoring_config.preferred_location_bonus
        if filter_decision.matched_locations
        else 0.0
    )
    remote_bonus = scoring_config.remote_bonus if filter_decision.remote_detected else 0.0
    research_bonus = (
        scoring_config.research_bonus if _has_research_signal(job) else 0.0
    )
    total = include_score + location_bonus + remote_bonus + research_bonus

    return ScoreBreakdown(
        include_keyword_hits=include_hits,
        include_keyword_score=include_score,
        preferred_location_bonus=location_bonus,
        remote_bonus=remote_bonus,
        research_bonus=research_bonus,
        total_score=round(total, 4),
    )


def score_job(
    job: JobPosting,
    filter_config: FilterConfig,
    scoring_config: ScoringConfig,
) -> float:
    """Compatibility helper returning only numeric score."""
    return compute_job_score(job, filter_config, scoring_config).total_score

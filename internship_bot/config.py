"""Application configuration loading.

This module keeps environment parsing centralized so the rest of the code can
work with typed settings objects.
"""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass
class TelegramConfig:
    """Telegram notification settings."""

    bot_token: str
    chat_id: str
    dry_run: bool


@dataclass
class FilterConfig:
    """Keyword and location preferences for matching jobs."""

    include_keywords: list[str]
    exclude_keywords: list[str]
    preferred_locations: list[str]


@dataclass
class ScoringConfig:
    """Simple score weights used to prioritize relevant jobs."""

    include_keyword_weight: float
    preferred_location_bonus: float
    remote_bonus: float
    research_bonus: float


@dataclass
class SourceToggleConfig:
    """Feature flags for source families."""

    enable_static_example: bool
    enable_greenhouse: bool
    enable_lever: bool


@dataclass
class SourcesConfig:
    """Collector-specific source settings."""

    static_source_urls: list[str]
    greenhouse_board_tokens: list[str]
    lever_company_slugs: list[str]


@dataclass
class AppConfig:
    """Top-level app settings used across the pipeline."""

    database_path: str
    log_level: str
    telegram: TelegramConfig
    filters: FilterConfig
    scoring: ScoringConfig
    toggles: SourceToggleConfig
    sources: SourcesConfig



def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_float(value: str | None, default: float) -> float:
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _to_csv_list(value: str | None) -> list[str]:
    if value is None or not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]



def load_config() -> AppConfig:
    """Load environment variables into a typed config object."""
    load_dotenv()

    include_keywords = _to_csv_list(
        os.getenv(
            "FILTER_INCLUDE_KEYWORDS",
            "ai,machine learning,deep learning,computer vision,multimodal,video generation,research internship",
        )
    )
    exclude_keywords = _to_csv_list(
        os.getenv("FILTER_EXCLUDE_KEYWORDS", "senior,staff,principal,phd required")
    )
    preferred_locations = _to_csv_list(
        os.getenv(
            "FILTER_PREFERRED_LOCATIONS",
            "remote,europe,germany,switzerland,netherlands,eu",
        )
    )

    telegram_config = TelegramConfig(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        dry_run=_to_bool(os.getenv("TELEGRAM_DRY_RUN", "true"), default=True),
    )

    if not telegram_config.dry_run and (
        not telegram_config.bot_token or not telegram_config.chat_id
    ):
        raise ValueError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set when TELEGRAM_DRY_RUN=false"
        )

    return AppConfig(
        database_path=os.getenv("DATABASE_PATH", "internships.db"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        telegram=telegram_config,
        filters=FilterConfig(
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
            preferred_locations=preferred_locations,
        ),
        scoring=ScoringConfig(
            include_keyword_weight=_to_float(
                os.getenv("SCORE_INCLUDE_KEYWORD_WEIGHT"),
                default=2.0,
            ),
            preferred_location_bonus=_to_float(
                os.getenv("SCORE_PREFERRED_LOCATION_BONUS"),
                default=1.5,
            ),
            remote_bonus=_to_float(
                os.getenv("SCORE_REMOTE_BONUS"),
                default=1.0,
            ),
            research_bonus=_to_float(
                os.getenv("SCORE_RESEARCH_BONUS"),
                default=1.0,
            ),
        ),
        toggles=SourceToggleConfig(
            enable_static_example=_to_bool(
                os.getenv("ENABLE_STATIC_EXAMPLE", "true"),
                default=True,
            ),
            enable_greenhouse=_to_bool(
                os.getenv("ENABLE_GREENHOUSE", "true"),
                default=True,
            ),
            enable_lever=_to_bool(
                os.getenv("ENABLE_LEVER", "true"),
                default=True,
            ),
        ),
        sources=SourcesConfig(
            static_source_urls=_to_csv_list(os.getenv("STATIC_SOURCE_URLS", "")),
            greenhouse_board_tokens=_to_csv_list(
                os.getenv("GREENHOUSE_BOARD_TOKENS", "")
            ),
            lever_company_slugs=_to_csv_list(os.getenv("LEVER_COMPANY_SLUGS", "")),
        ),
    )

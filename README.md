# Internship Finder MVP

A modular Python pipeline that monitors internship sources, filters relevant roles, deduplicates results, and sends notifications via Telegram.

## Status

- Phase 10 documentation and polish complete
- Local MVP runs end-to-end and is ready for scheduled execution

## Project Structure

```text
internship_bot/
  collectors/
  filters/
  notifier/
  storage/
  models/
  utils/
  config.py
  main.py
.env.example
requirements.txt
README.md
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill values.

## Configuration

Environment variables are loaded from `.env` via `python-dotenv`.

Current config groups:
- Runtime: `DATABASE_PATH`, `LOG_LEVEL`
- Collector runtime: `COLLECTOR_TIMEOUT_SECONDS`, `COLLECTOR_USER_AGENT`
- Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_DRY_RUN`
- Source toggles: `ENABLE_STATIC_EXAMPLE`, `ENABLE_GREENHOUSE`, `ENABLE_LEVER`
- Source values (CSV): `STATIC_SOURCE_URLS`, `GREENHOUSE_BOARD_TOKENS`, `LEVER_COMPANY_SLUGS`
- Filters (CSV): `FILTER_INCLUDE_KEYWORDS`, `FILTER_EXCLUDE_KEYWORDS`, `FILTER_PREFERRED_LOCATIONS`
- Scoring: `SCORE_INCLUDE_KEYWORD_WEIGHT`, `SCORE_PREFERRED_LOCATION_BONUS`, `SCORE_REMOTE_BONUS`, `SCORE_RESEARCH_BONUS`

Design note:
- CSV environment variables are used instead of JSON for simplicity in local `.env` editing.

## Usage

Run the pipeline:

- `python -m internship_bot.main`

Run collector-only smoke tests:

- `python tools/test_collectors.py`

Pipeline stages executed in order:
1. Initialize config and logging
2. Initialize SQLite schema
3. Build enabled collectors from config
4. Collect jobs from each source (isolated per collector)
5. Filter and score each job
6. Save/upsert jobs (deduplicated by fingerprint)
7. Query unsent matching jobs
8. Send Telegram notifications (or dry-run previews)
9. Mark successful notifications as sent
10. Print run summary logs

## Architecture Overview

Core modules:
- [internship_bot/main.py](internship_bot/main.py): end-to-end orchestration
- [internship_bot/config.py](internship_bot/config.py): environment-driven typed config
- [internship_bot/storage/db.py](internship_bot/storage/db.py): SQLite persistence and dedup state
- [internship_bot/collectors/](internship_bot/collectors/): source-specific collectors
- [internship_bot/filters/](internship_bot/filters/): relevance rules and scoring
- [internship_bot/notifier/telegram.py](internship_bot/notifier/telegram.py): notification delivery

Data flow:
1. Collectors fetch raw postings and normalize to `JobPosting`
2. Filter rules decide whether each job is relevant
3. Scoring computes ranking priority
4. Database upserts jobs by fingerprint (dedup)
5. Unsent matches are selected and passed to notifier
6. Successful sends are marked in `sent_notifications`

## Local Testing Support (Phase 9)

Added local-first test assets:
- Sample static source file: [sample_data/static_jobs_sample.html](sample_data/static_jobs_sample.html)
- Collector smoke runner: [tools/test_collectors.py](tools/test_collectors.py)

Local defaults are safe:
- `TELEGRAM_DRY_RUN=true`
- `ENABLE_STATIC_EXAMPLE=true`
- `ENABLE_GREENHOUSE=false`
- `ENABLE_LEVER=false`
- `STATIC_SOURCE_URLS=sample_data/static_jobs_sample.html`

This lets you test end-to-end behavior without credentials or external API calls.

## Storage (Phase 4)

SQLite tables are initialized automatically on startup:
- `jobs`: normalized postings with unique `fingerprint`
- `sent_notifications`: tracks already-sent messages per channel
- `pipeline_runs`: optional run metadata table for future use

Deduplication strategy:
- First choice: normalized URL fingerprint (`url:<normalized_url>`)
- Fallback: hash fingerprint from stable core fields (`hash:<sha256>`)

Available storage methods in `Database`:
- `initialize()`
- `save_job(job, is_match)`
- `is_job_seen(fingerprint)`
- `was_notification_sent(fingerprint, channel)`
- `mark_notification_sent(fingerprint, channel, message_id)`
- `list_unsent_matching_jobs(channel, limit)`

## Filtering and Scoring (Phase 5)

Filtering rules (`evaluate_job`):
- Include rule: pass when at least one include keyword is found (or include list is empty)
- Exclude rule: fail when any exclude keyword is found
- Location rule: pass when a preferred location matches, or the job is remote

Exact scoring formula (`compute_job_score`):

`total_score =`
- `(number_of_matched_include_keywords * SCORE_INCLUDE_KEYWORD_WEIGHT)`
- `+ SCORE_PREFERRED_LOCATION_BONUS` if location matched
- `+ SCORE_REMOTE_BONUS` if remote detected
- `+ SCORE_RESEARCH_BONUS` if research signal is present (`research`, `research internship`, `thesis`, `lab`)

Score is additive and transparent, with component breakdown available from `ScoreBreakdown`.

## Collectors (Phase 6)

Implemented collectors:
- `ExampleStaticSiteCollector`: generic static HTML collector (`requests` + `BeautifulSoup`)
- `GreenhouseCollector`: reads `boards-api.greenhouse.io` jobs endpoint
- `LeverCollector`: reads `api.lever.co` postings endpoint

Common behavior:
- All collectors return normalized `JobPosting` objects.
- Missing/invalid fields are handled defensively; malformed rows are skipped.
- Network/API errors are caught inside each collector and return an empty list.

Assumptions and placeholders:
- Static collector assumes internship links are present in anchor elements and filters links containing `intern` or `research`.
- Some websites will require selector tuning later (Phase 9/10 guidance).

## Telegram Notifier (Phase 7)

Implemented in [internship_bot/notifier/telegram.py](internship_bot/notifier/telegram.py):
- Clean message formatter with title, company, location, source, date, score, and URL
- Dry-run mode (`TELEGRAM_DRY_RUN=true`) that prints message previews instead of sending
- Real send mode through Telegram Bot API (`sendMessage`)

How to create credentials:
1. Open Telegram and start chat with `@BotFather`
2. Run `/newbot` and follow prompts to get `TELEGRAM_BOT_TOKEN`
3. Start a chat with your bot (or add it to a group)
4. Get `TELEGRAM_CHAT_ID` (personal chat ID or group ID)
5. Put both values in `.env`

Safe local testing:
- Keep `TELEGRAM_DRY_RUN=true`
- Run `python -m internship_bot.main`
- Verify message previews in terminal before enabling real sends

## Extending Collectors

Step-by-step:
1. Add a new module under [internship_bot/collectors/](internship_bot/collectors/), for example `my_source.py`
2. Create a class inheriting `BaseCollector`
3. Implement `collect()` and return `list[JobPosting]`
4. Normalize source fields using `_safe_job(...)` from `BaseCollector`
5. Add source toggles/values in [internship_bot/config.py](internship_bot/config.py) if needed
6. Register collector construction in `build_collectors(...)` inside [internship_bot/main.py](internship_bot/main.py)
7. Validate with `python tools/test_collectors.py`

Minimal template:

```python
from internship_bot.collectors.base import BaseCollector
from internship_bot.models.job import JobPosting


class MySourceCollector(BaseCollector):
    name = "my_source"

    def collect(self) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        # fetch data here
        job = self._safe_job(
            source="my_source",
            title="AI Internship",
            company="Example",
            location="Remote",
            url="https://example.org/jobs/ai-intern",
            source_type="custom",
        )
        if job:
            jobs.append(job)
        return jobs
```

## Scheduling & Deployment

### Cron (Linux VPS)

Run every 2 hours:

```cron
0 */2 * * * cd /opt/internship-finder && /opt/internship-finder/.venv/bin/python -m internship_bot.main >> /opt/internship-finder/logs/pipeline.log 2>&1
```

### GitHub Actions

Create `.github/workflows/run-internship-bot.yml` with a schedule and repository secrets:

```yaml
name: Run Internship Bot

on:
  schedule:
    - cron: "0 */6 * * *"
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python -m internship_bot.main
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          TELEGRAM_DRY_RUN: "false"
```

### Docker / VPS

This repository now includes:
- [Dockerfile](Dockerfile)
- [.dockerignore](.dockerignore)

Build image:

```bash
docker build -t internship-finder:latest .
```

Suggested approach:
1. Build the image once
2. Mount a persistent volume/folder for `internships.db`
3. Inject env vars at runtime (or via `--env-file`)
4. Run on schedule via host cron or orchestrator

Minimum runtime command example:

```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  -e DATABASE_PATH=/app/data/internships.db \
  -e TELEGRAM_DRY_RUN=true \
  --env-file .env \
  internship-finder:latest python -m internship_bot.main
```

## Troubleshooting

- Import error `No module named internship_bot`:
  - Run commands from repository root
  - Or use module mode: `python -m internship_bot.main`
- No jobs collected:
  - Confirm source toggles and source values in `.env`
  - Start with `STATIC_SOURCE_URLS=sample_data/static_jobs_sample.html`
- Notifications not sent:
  - Keep `TELEGRAM_DRY_RUN=true` for local tests
  - For live mode, set valid `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- Duplicate notifications:
  - Check `sent_notifications` table in SQLite
  - Ensure fingerprint stability (URL or fallback hash)
- Unexpected collector failures:
  - Increase `COLLECTOR_TIMEOUT_SECONDS`
  - Test collectors independently with `python tools/test_collectors.py`

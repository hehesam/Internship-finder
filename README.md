# Internship Finder MVP

A modular Python pipeline that monitors internship sources, filters relevant roles, deduplicates results, and sends notifications via Telegram.

## Status

- Phase 8 main pipeline orchestration complete
- Local MVP runs end-to-end with dry-run Telegram support

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

- Add a new class under `internship_bot/collectors/`
- Inherit from `BaseCollector`
- Implement `collect()` returning normalized `JobPosting` objects

## Scheduling & Deployment (later)

- cron
- GitHub Actions
- Docker / VPS

## Troubleshooting

- If imports fail, verify package structure and current working directory.
- If env values are missing, confirm `.env` exists and keys are set.

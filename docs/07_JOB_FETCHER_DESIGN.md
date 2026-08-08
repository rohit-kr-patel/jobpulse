# Job Fetchers

Sources:
- Greenhouse
- Lever
- Remotive
- Arbeitnow

Pipeline:
Fetch -> Normalize -> Deduplicate -> Store

## Implementation (Phase 4)

Module: `backend/app/fetchers/`. Every source is normalized into the
same `NormalizedJob` dataclass (`base.py`) before storage, regardless
of how different its raw API response is.

- **Greenhouse** (`greenhouse_fetcher.py`): `GET boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`. Greenhouse has no public directory of companies - board tokens to check are configured via `GREENHOUSE_BOARD_TOKENS` (comma-separated). A source with none configured is skipped, not treated as an error.
- **Lever** (`lever_fetcher.py`): `GET api.lever.co/v0/postings/{company}?mode=json`. Same per-company limitation - configured via `LEVER_COMPANY_SLUGS`.
- **Remotive** (`remotive_fetcher.py`): `GET remotive.com/api/remote-jobs?category=software-dev`. A general board covering many companies in one request; every listing is remote by definition. Category configurable via `REMOTIVE_CATEGORY`.
- **Arbeitnow** (`arbeitnow_fetcher.py`): `GET www.arbeitnow.com/api/job-board-api`, paginated (~100/page). Also a general multi-company board. Bounded by `ARBEITNOW_MAX_PAGES` (default 1) to stay a courteous user of a free public API.

Shared helpers (`utils.py`): HTML-to-plain-text (via BeautifulSoup, since Greenhouse/Lever/Remotive/Arbeitnow all return HTML descriptions), CSV settings parsing, a `location`-text remote heuristic, and defensive ISO/epoch-seconds/epoch-millis datetime parsing - all fail soft (return `None`/empty rather than raising) since these are third-party APIs outside our control.

### Deduplication

A unique constraint on `(source, external_id)` means re-fetching an
already-known job **updates it in place** (title, location,
description, etc. refreshed; `fetched_at` bumped) rather than
inserting a duplicate row. This is the only deduplication implemented.

**Known limitation:** cross-source duplicates - the same job posted on
two different boards (e.g. a company's own Greenhouse listing also
showing up on Remotive) - are **not** detected, since there's no
reliable shared identifier across sources. Fuzzy matching (e.g. on
title + company + location similarity) would be needed to catch this
and is a candidate for a future phase if it turns out to matter in
practice.

### Fetch orchestration and failure isolation

`app/services/job_service.fetch_and_store_all` runs all four fetchers
and commits each source's results independently. If one source fails
(network error, unexpected response shape, or any other exception),
it's caught, logged, and reported as `failed: true` in that source's
summary - it never blocks or rolls back the other three sources.

### Triggering a fetch

The scheduler (Phase 8) doesn't exist yet, so Phase 4 exposes a manual
trigger: `POST /jobs/fetch`, returning a per-source summary
(`fetched`/`created`/`updated`/`failed`). Phase 8 will call this same
pipeline automatically on a daily schedule instead of requiring a
manual call.

# Scheduler

## Implementation (Phase 8)

Module: `backend/app/scheduler/`. Uses APScheduler's `BackgroundScheduler` (a
separate thread, not the main asyncio event loop) since the daily
pipeline itself is synchronous (SQLAlchemy `Session`, `httpx.Client` -
the same code `POST /jobs/fetch` already used in Phase 4/5) and would
block the event loop if run directly on it.

### What runs daily

`app/scheduler/jobs.py:run_daily_pipeline`, on a cron trigger (daily at
`SCHEDULER_FETCH_HOUR:SCHEDULER_FETCH_MINUTE` in `SCHEDULER_TIMEZONE`):

1. **Fetch** - calls the existing `job_service.fetch_and_store_all` (no
   new fetch logic; Phase 4 built this, Phase 8 just triggers it
   automatically instead of requiring `POST /jobs/fetch`). Per-source
   results are logged and already persisted to `fetch_logs` (Phase 5).
2. **Refresh rankings** - calls `matching_service.get_top_matches`
   right after the fetch completes. `GET /matches` (Phase 7) always
   computes live, so there's no cache to invalidate; this step's value
   is exercising the full fetch-then-rank pipeline end-to-end as part
   of the daily run (so a break is caught here, not silently at the
   next API call) and logging today's top match for visibility.
   Skipped, not failed, if preferences haven't been set yet.

The whole function never raises - any failure is caught, logged, and
the run ends cleanly, so one bad day doesn't prevent tomorrow's run or
crash the scheduler thread.

### What Phase 8 does *not* do

**"Update notifications"** is listed in `tasks/PHASE_08_SCHEDULER.md`'s
task list, but there is no notifications system to update yet - that's
Phase 9's explicit scope (`tasks/PHASE_09_BROWSER_NOTIFICATIONS.md`).
Building it now would preempt that phase. Once Phase 9 exists, its
notification-creation logic is the natural next step to call from
`run_daily_pipeline`, after the ranking refresh.

### Configuration

All via `Settings` / `.env` (see `.env.example`):

| Setting | Default (code) | Default (`.env.example`) |
|---|---|---|
| `SCHEDULER_ENABLED` | `false` | `true` |
| `SCHEDULER_FETCH_HOUR` | `6` | `6` |
| `SCHEDULER_FETCH_MINUTE` | `0` | `0` |
| `SCHEDULER_TIMEZONE` | `UTC` | `UTC` |

The code-level default is intentionally `false`: importing the app (in
tests, or a fresh checkout with no `.env`) must never silently start a
background thread. `.env.example` - the template for real deployments -
defaults it to `true`, since automated daily fetching is the product's
core promise.

### Testing

No test waits on real wall-clock time. `run_daily_pipeline` is tested
directly (mocked fetchers, same pattern as `test_job_service.py`),
asserting on its log output for each branch (fetch summary, ranking
refresh, skipped-no-preferences, no-jobs-to-rank, and a broken source
never raising). The scheduler lifecycle (`build_scheduler`,
`start_scheduler`, `stop_scheduler`) is tested separately: confirms
the disabled case is a true no-op (no thread/scheduler object created,
verified by checking thread count doesn't increase), and that the
enabled case actually starts, registers the job with the configured
schedule, and shuts down cleanly.

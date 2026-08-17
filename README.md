# 🚀 JobPulse

> **Your personal job assistant.**
> Automatically fetches, ranks, and tracks software engineering jobs every day - so you spend minutes on your job search, not hours.

**Status: V1 complete.** All 11 planned phases are implemented, tested, and documented. See [Current Status](#-current-status) below.

---

## 📌 Problem

Job hunting as a fresher or early-career engineer is repetitive: visiting the same handful of job boards every day, re-reading duplicate postings, checking whether an opening is still live, and tracking applications by memory or in a spreadsheet. JobPulse automates all of that: one dashboard, refreshed daily, ranked against your actual resume and preferences.

**Target user:** a single person (no multi-tenant auth in V1) - a fresher or early-career software engineer running this for themselves.

---

## ✨ Features

Everything below is implemented and covered by automated tests, not aspirational.

- **Resume upload & parsing** (PDF, rule-based - no LLM): extracts skills, education, and years of experience via PyMuPDF text extraction + keyword/regex matching
- **Preferences**: target roles, skills, locations, experience, CTC range, and work mode (remote/hybrid/onsite/any)
- **Job fetching** from four free sources - **Greenhouse**, **Lever**, **Remotive**, **Arbeitnow** - normalized into one schema, deduplicated via `(source, external_id)`
- **Daily scheduler** (APScheduler): fetches, re-ranks, and creates notifications automatically at a configured time
- **Matching engine**: TF-IDF + cosine similarity (scikit-learn) combined with weighted rule-based factors (skills, role, location, experience-fit, remote-fit) into a single score, returning your top 20 matches
- **Dashboard**: stats, live filters (search/source/remote), job cards with a freshness indicator, all client-side and framework-free
- **Notifications**: an in-dashboard banner plus real browser `Notification` API integration (polling-based - see [Known Limitations](#-known-limitations--design-decisions))
- **Application tracker**: save / mark applied / mark rejected, optional notes, full history view
- **Expired-job detection**: jobs that stop reappearing in fetches are automatically marked expired (and un-expired if they come back)
- **Direct apply links** - no auto-apply, no cover-letter generation, no LLM anywhere in the pipeline

---

## 🏗 Architecture

```text
Frontend (HTML/CSS/vanilla JS)
        │
        ▼
     FastAPI ──────────────┐
        │                  │
        ▼                  ▼
  PostgreSQL      APScheduler (daily)
        ▲                  │
        │                  ▼
        │        Job Fetchers (Greenhouse/Lever/Remotive/Arbeitnow)
        │                  │
        │                  ▼
        └──────── Matching Engine (TF-IDF + weighted scoring)
                            │
                            ▼
                  Notifications (banner + browser)
```

Backend follows a layered structure throughout: **Routes → Services → Repositories → Database**. See `docs/02_SYSTEM_ARCHITECTURE.md`.

---

## 🛠 Tech Stack

| Layer | Choice |
|---|---|
| Frontend | HTML5, CSS3, vanilla JavaScript (no framework, no build step) |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL (SQLite in-memory for the test suite) |
| Scheduler | APScheduler (`BackgroundScheduler`) |
| Resume parsing | PyMuPDF |
| Matching | scikit-learn (TF-IDF + cosine similarity) - non-generative, no LLM |
| Job fetcher HTTP | httpx |
| HTML cleanup | BeautifulSoup4 |
| Dev tooling | pytest + respx, Black, Ruff (`backend/pyproject.toml`) |

---

## 📂 Project Structure

```text
JobPulse/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI routers (one per resource)
│   │   ├── services/         # Business logic
│   │   ├── repositories/     # Data access, no business logic
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── fetchers/         # Greenhouse/Lever/Remotive/Arbeitnow clients
│   │   ├── matching/         # TF-IDF + weighted scoring
│   │   ├── parsing/          # Resume PDF parsing
│   │   ├── scheduler/        # APScheduler setup + daily pipeline
│   │   ├── core/             # Config, logging, exceptions
│   │   └── db/                # Session, seeding
│   ├── alembic/               # Migrations (0001-0007)
│   ├── tests/                  # 124 tests, pytest
│   ├── requirements.txt
│   ├── requirements-dev.txt   # Black/Ruff only
│   └── pyproject.toml         # Black/Ruff config
├── frontend/
│   ├── dashboard.html          # Main entry point
│   ├── job-detail.html         # Job detail + application tracking
│   ├── applications.html       # Application history
│   ├── preferences.html
│   ├── resume-upload.html
│   ├── index.html              # Lightweight landing page
│   ├── css/
│   └── js/
├── docs/                       # Design docs, one per subsystem (00-18)
├── tasks/                      # Per-phase task specs (as given)
├── docker-compose.yml
└── .env.example
```

---

## 🚀 Getting Started

```bash
git clone <repository-url>
cd JobPulse
cp .env.example .env
```

### Option 1 - Docker Compose (recommended, runs Postgres + API together)

```bash
docker compose up --build
# in another terminal, apply migrations once the containers are up:
docker compose exec backend alembic upgrade head
```

### Option 2 - Run the backend directly (requires a local PostgreSQL matching your `.env`)

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Then check `http://localhost:8000/health`, and open `frontend/dashboard.html` in a browser (or `index.html` for a lightweight landing page linking to it).

### Pulling in your first jobs

1. Set your preferences at `preferences.html` - this lets the matching engine and notifications actually do something meaningful.
2. Set `GREENHOUSE_BOARD_TOKENS` and/or `LEVER_COMPANY_SLUGS` in `.env` if you want those sources (see the comments in `.env.example` - there's no public directory of companies on these ATSes, so you list the ones you care about). Remotive and Arbeitnow need no configuration.
3. With `SCHEDULER_ENABLED=true` (the `.env.example` default), a fetch + ranking refresh runs automatically every day at `SCHEDULER_FETCH_HOUR:SCHEDULER_FETCH_MINUTE`. To trigger one immediately: `curl -X POST http://localhost:8000/jobs/fetch`.

---

## ⚙️ Configuration

All configuration is via environment variables (`.env`, loaded by `pydantic-settings`) - see `.env.example` for the authoritative, commented list. Summary:

| Variable | Default | Purpose |
|---|---|---|
| `POSTGRES_*` | `jobpulse`/`jobpulse`/`jobpulse`/`db`/`5432` | Database connection |
| `GREENHOUSE_BOARD_TOKENS` | *(empty)* | Comma-separated Greenhouse company board tokens to fetch |
| `LEVER_COMPANY_SLUGS` | *(empty)* | Comma-separated Lever company slugs to fetch |
| `REMOTIVE_CATEGORY` | `software-dev` | Remotive category filter |
| `ARBEITNOW_MAX_PAGES` | `1` | Pages to fetch from Arbeitnow per run |
| `MATCH_WEIGHT_*` | sum to `1.0` | Matching engine factor weights (text/skills/role/location/experience/remote) |
| `MATCH_TOP_N` | `20` | How many ranked jobs `GET /matches` returns |
| `SCHEDULER_ENABLED` | `false` in code, `true` in `.env.example` | Whether the daily background scheduler runs - see [Known Limitations](#-known-limitations--design-decisions) |
| `SCHEDULER_FETCH_HOUR` / `_MINUTE` / `_TIMEZONE` | `6` / `0` / `UTC` | Daily fetch schedule |
| `JOB_EXPIRE_AFTER_DAYS` | `3` | Days without reappearing in a fetch before a job is marked expired |
| `RESUME_MAX_SIZE_MB` | `5` | Resume upload size limit |

---

## 📡 API Overview

Full request/response shapes are documented in `docs/05_API_SPECIFICATION.md`. Quick reference:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | API + database status |
| `POST` / `GET` | `/preferences` | Set/get job-search preferences |
| `POST` | `/resume/upload` | Upload + auto-parse a resume PDF |
| `GET` | `/jobs`, `/jobs/{id}` | List / view fetched jobs (excludes expired by default) |
| `POST` | `/jobs/fetch` | Manually trigger the fetch pipeline |
| `GET` | `/fetch-logs` | Fetch run history |
| `GET` | `/matches` | Top-N ranked jobs for your profile |
| `GET` | `/notifications` | List notifications; `PATCH /notifications/{id}/read`, `POST /notifications/mark-all-read` |
| `POST` / `PATCH` / `GET` | `/applications` | Save/update/list tracked applications |

Interactive docs (Swagger UI) are available at `http://localhost:8000/docs` once the backend is running.

---

## 🧪 Testing

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/
```

**124 tests**, all running against an in-memory SQLite database (no live Postgres required for the suite). Covers every route, every fetcher (mocked HTTP via `respx`), the matching engine's scoring logic, the scheduler's daily pipeline end-to-end, and every migration verified directly against a live engine. See `docs/13_TESTING_STRATEGY.md` for the full breakdown, including what's covered by frontend `jsdom` verification versus what still needs a manual look in an actual browser.

To check formatting/linting (also configured in `backend/pyproject.toml`):

```bash
pip install -r requirements-dev.txt
black --check app/ tests/
ruff check app/ tests/
```

---

## 🗺 Roadmap

- [x] Phase 1 – Project Setup
- [x] Phase 2 – User Profile
- [x] Phase 3 – Resume Parser
- [x] Phase 4 – Job Fetchers
- [x] Phase 5 – Database & APIs
- [x] Phase 6 – Dashboard
- [x] Phase 7 – Matching Engine
- [x] Phase 8 – Scheduler
- [x] Phase 9 – Browser Notifications
- [x] Phase 10 – Application Tracker
- [x] Phase 11 – Final Refactor

---

## 📌 Current Status

**Version: 1.0.0** - all 11 phases complete.

- 124 automated backend tests passing
- Backend formatted/linted clean (Black + Ruff, see `backend/pyproject.toml`)
- All 7 Alembic migrations verified against a live engine, and cross-checked to produce a schema that matches the ORM models exactly
- Frontend: 6 pages, verified via `jsdom` harnesses during development (not shipped) since no browser was available in the build environment - **a real visual pass in an actual browser is recommended before considering this fully production-ready**

---

## ⚠️ Known Limitations & Design Decisions

Honest tradeoffs made along the way, collected here from each phase's notes (full detail in `docs/TODO.md`):

- **No true push notifications.** "Browser notifications" means polling + the native `Notification` API while the dashboard tab is open - not Web Push (which would need a service worker, push subscription, and a VAPID-keyed push server; no such infrastructure exists in this project).
- **Job dedup is per-source only.** The same job posted on two different boards (e.g. a company's own Greenhouse listing and a Remotive repost) isn't detected as a duplicate - no cross-source fuzzy matching is implemented.
- **Expired-job detection is an absence heuristic**, not a confirmed-removal signal. A source that's been silently broken longer than `JOB_EXPIRE_AFTER_DAYS` would have its jobs marked expired even if they're still open (mitigated by `fetch_logs` giving visibility into fetch failures).
- **Resume parsing is intentionally rule-based and approximate** (no LLMs, per project scope) - it will miss skills/degrees outside its curated keyword lists, and its experience-years extraction is a best-effort regex, not a guarantee.
- **Greenhouse and Lever fetch nothing until configured** - there's no public directory of companies on either ATS, so you provide the specific companies you want checked.
- **Several endpoints exist beyond the original API spec** (`POST /jobs/fetch`, `GET /fetch-logs`, `GET /matches`, notification mark-as-read, `GET /applications`) - each was added because its phase's stated task genuinely needed somewhere to live; documented individually in `docs/05_API_SPECIFICATION.md`.
- **`SCHEDULER_ENABLED` defaults differently in code vs. `.env.example`** (`false` vs `true`) - deliberate, so tests and a fresh checkout with no `.env` never start a background thread unexpectedly, while a real deployment gets automated fetching out of the box.

---

## 🔮 Future Ideas (explicitly out of scope for V1)

- Email notifications, Telegram bot
- Company insights, referral tracker
- Resume optimization (would require an LLM - explicitly excluded from V1)
- Mobile application
- True Web Push (service worker + push subscription server)
- Multi-user support / authentication

---

## 📖 Documentation

Full design docs live in `docs/` (`00_PROJECT_OVERVIEW.md` through `18_APPLICATION_TRACKER.md`), plus `docs/CHANGELOG.md` (what shipped each phase) and `docs/TODO.md` (scope decisions and known limitations in full detail). Per-phase task specs are in `tasks/`.

---

## 📄 License

This project is developed for learning and portfolio purposes.

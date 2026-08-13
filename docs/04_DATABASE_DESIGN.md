# Database Design

Tables:
- users
- resumes
- preferences
- jobs
- applications
- notifications
- fetch_logs

Relationships:
User -> Resume
User -> Preferences
User -> Applications
Jobs -> Applications

## Schema (as implemented, Phase 2)

Introduced via `backend/alembic/versions/0001_initial_users_resumes_preferences.py`.

### users
| Column | Type | Notes |
|---|---|---|
| id | integer, PK | |
| full_name | varchar(255), not null | |
| email | varchar(255), not null, unique | |
| created_at | timestamptz, not null | server default now() |

V1 has exactly one row (no auth), seeded at startup - see `app/db/seed.py`.

### resumes
| Column | Type | Notes |
|---|---|---|
| id | integer, PK | |
| user_id | integer, FK -> users.id (ON DELETE CASCADE), indexed | |
| original_filename | varchar(255), not null | |
| stored_path | varchar(1024), not null | path on disk under `RESUME_UPLOAD_DIR` |
| content_type | varchar(100), not null | |
| size_bytes | integer, not null | |
| uploaded_at | timestamptz, not null | server default now() |
| parsed_skills | JSON (list[str]), nullable | rule-based extraction result, Phase 3 |
| parsed_education | JSON (list[str]), nullable | rule-based extraction result, Phase 3 |
| parsed_experience_years | float, nullable | rule-based extraction result, Phase 3 (approximate) |
| parsed_at | timestamptz, nullable | when parsing last ran for this resume |

Parsing runs automatically on upload (see `app/services/resume_service.py`); a parse failure leaves these fields null rather than failing the upload.

### preferences
| Column | Type | Notes |
|---|---|---|
| id | integer, PK | |
| user_id | integer, FK -> users.id (ON DELETE CASCADE), unique | one row per user |
| target_roles | JSON (list[str]), not null | |
| skills | JSON (list[str]), not null | |
| locations | JSON (list[str]), not null | |
| experience_years | integer, not null | 0-60 |
| min_ctc | integer, nullable | |
| max_ctc | integer, nullable | must be >= min_ctc when both set |
| work_mode | varchar(20), not null | one of: remote, hybrid, onsite, any |
| created_at | timestamptz, not null | server default now() |
| updated_at | timestamptz, not null | server default now(), updated on write |

Remaining tables (`jobs`, `applications`, `notifications`, `fetch_logs`) are introduced in Phase 5.

### jobs (Phase 4)
| Column | Type | Notes |
|---|---|---|
| id | integer, PK | |
| source | varchar(50), not null, indexed | one of: greenhouse, lever, remotive, arbeitnow |
| external_id | varchar(255), not null | the source's own id/slug for this job |
| title | varchar(500), not null | |
| company | varchar(255), not null | |
| location | varchar(255), nullable | |
| is_remote | boolean, not null | heuristic for Greenhouse/Lever; always true for Remotive; source-provided for Arbeitnow |
| description | text, not null | plain text (HTML stripped) |
| apply_url | varchar(2048), not null | |
| posted_at | timestamptz, nullable | when the source says the job was posted/updated |
| fetched_at | timestamptz, not null | when we last fetched this job; bumped on every re-fetch |
| created_at | timestamptz, not null | server default now() |
| updated_at | timestamptz, not null | server default now(), updated on write |

Unique constraint on `(source, external_id)` - the deduplication key. See `docs/07_JOB_FETCHER_DESIGN.md` for what this does and doesn't catch.

Remaining tables (`applications`, `notifications`, `fetch_logs`) are introduced in Phase 5.

### fetch_logs (Phase 5)
| Column | Type | Notes |
|---|---|---|
| id | integer, PK | |
| source | varchar(50), not null, indexed | one row per source per fetch run |
| fetched_count | integer, not null | jobs returned by the fetcher |
| created_count | integer, not null | new jobs inserted |
| updated_count | integer, not null | existing jobs updated in place |
| failed | boolean, not null | true if the source's fetch raised an exception |
| started_at | timestamptz, not null | |
| finished_at | timestamptz, not null | |
| created_at | timestamptz, not null | server default now() |

Written by `app/services/job_service.fetch_and_store_all` on every run (currently reachable via the manual `POST /jobs/fetch`, and automatically via the Phase 8 daily scheduler).

### notifications (Phase 9)
| Column | Type | Notes |
|---|---|---|
| id | integer, PK | |
| user_id | integer, FK -> users.id (ON DELETE CASCADE), indexed | |
| job_id | integer, FK -> jobs.id (ON DELETE CASCADE), indexed, nullable | for a "view job" link; nullable for future non-job notification types |
| message | varchar(500), not null | fully-formed, human-readable - no join needed to render |
| is_read | boolean, not null | default false |
| created_at | timestamptz, not null | server default now() |

Created by `notification_service.create_notifications_for_new_top_matches`, called from the scheduler's daily pipeline right after the ranking refresh - see `docs/10_NOTIFICATION_SYSTEM.md`.

**Note:** `applications` is *not* built yet, despite being listed in the original table list above and referenced (unassigned) in `docs/05_API_SPECIFICATION.md`. It's explicitly owned by Phase 10 ("Application Tracker": save/applied/rejected/expired/history) - see `tasks/PHASE_10_APPLICATION_TRACKER.md`.

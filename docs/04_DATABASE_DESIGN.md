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

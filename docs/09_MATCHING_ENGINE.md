# Matching Engine

Technique:
- TF-IDF / Sentence Embeddings (non-LLM)
- Cosine Similarity
- Weighted score

Factors:
- Skills
- Role
- Location
- Experience
- Remote preference

## Implementation (Phase 7)

**Technique chosen: TF-IDF** (not sentence embeddings) - this was locked in as the V1 default during initial project scoping (dependency-light, deterministic, easy to test), consistent with "no LLMs" throughout the project.

Module: `backend/app/matching/scoring.py`. Score is a weighted sum of six factors, each normalized to `[0, 1]`:

| Factor | Weight (default) | How it's computed |
|---|---|---|
| `text_similarity` | 0.35 | TF-IDF cosine similarity between the user's profile text (target roles + skills) and each job's title+description (scikit-learn `TfidfVectorizer` + `cosine_similarity`) |
| `skill_score` | 0.25 | Fraction of the user's skills (preferences + resume, deduped) found in the job text, via the same whole-token keyword matcher used by resume parsing |
| `role_score` | 0.15 | 1.0 if any target role phrase appears in the job title, else 0.0 |
| `location_score` | 0.10 | 1.0 if the job's location text matches one of the user's preferred locations, else 0.0 |
| `experience_score` | 0.10 | Compares the user's experience (resume-parsed, falling back to preferences) against a required-years figure extracted from the job text (same statement regex used by resume parsing). Neutral (0.5) if either side is unknown; full credit at/above the requirement; proportional partial credit below it |
| `remote_score` | 0.05 | Does the job's remote/non-remote status match the user's `work_mode`? `any` always matches |

Weights are configurable via `Settings` (`MATCH_WEIGHT_*` env vars) and default to summing to 1.0, so the total score stays in `[0, 1]`.

**Profile construction** (`build_profile`): skills are the union of `preferences.skills` and the latest resume's `parsed_skills` (deduped, order-preserving). Experience prefers the resume's parsed figure over the preferences-stated one, since it's closer to ground truth.

**Shared logic with resume parsing:** the whole-token keyword matcher and the "explicit years-of-experience statement" regex were factored out of `app/parsing/resume_parser.py` into `app/text_extraction.py` so both resume parsing and job matching use the same tested logic instead of duplicating it.

**Candidate pool:** all stored jobs, up to `MATCH_CANDIDATE_POOL_SIZE` (default 1000) - fine at V1's personal scale. No expiry filtering (that's Phase 10 scope).

**Endpoint:** `GET /matches` (not in the original API spec - see `docs/05_API_SPECIFICATION.md`), returning the top `MATCH_TOP_N` (default 20) jobs with their full score breakdown. 404s if the user hasn't set preferences yet, since there's no profile to match against; a missing resume is fine and just reduces signal (skills/experience come from preferences alone).

**Scope note:** this phase is backend-only per `tasks/PHASE_07_MATCHING_ENGINE.md`'s task list (TF-IDF, cosine similarity, weighted scoring, top 20) - the dashboard does not yet surface match scores or a "Top Matches" view. See `docs/TODO.md`.

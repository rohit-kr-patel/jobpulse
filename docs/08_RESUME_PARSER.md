# Resume Parser

Pipeline:
PDF -> Text Extraction -> Skill Extraction -> Experience -> Education -> Database

No LLMs.
Use PyMuPDF and rule-based extraction.

## Implementation (Phase 3)

Module: `backend/app/parsing/`

- **Text extraction** (`resume_parser.extract_text`): PyMuPDF (`fitz`) reads all pages of the uploaded PDF and concatenates their text.
- **Skills** (`resume_parser.extract_skills`): case-insensitive whole-token matching against a curated list (`skills_data.KNOWN_SKILLS`, ~70 entries covering languages, frameworks, databases, infra/DevOps, and testing tools). Matching guards against partial-word hits (e.g. "SQL" won't match inside "PostgreSQL") and suppresses a matched skill if it's a pure substring of another matched skill (e.g. "C" is dropped if "C++" also matched). A few short, common-word-colliding names (`Go`, `R`, `C`) are matched case-sensitively only, to avoid false positives from ordinary English text.
- **Education** (`resume_parser.extract_education`): same whole-token matching against a curated degree keyword list (`education_data.KNOWN_DEGREES`). `BE`/`ME` are matched case-sensitively only, to avoid colliding with the pronouns "be"/"me".
- **Experience** (`resume_parser.extract_experience_years`): first looks for an explicit statement like "5+ years of experience" (takes the largest such figure found). If none exists, falls back to the span between the earliest and latest 4-digit year mentioned anywhere in the text - a rough approximation of tenure, used only as a last resort.

## Known limitations

This is intentionally simple, heuristic extraction - not a guarantee. False negatives are expected for:
- Skills/degrees not in the curated keyword lists
- Non-English resumes or unconventional formatting (e.g. skills embedded in tables/columns that PyMuPDF may not extract in reading order)
- Experience phrased in a way neither extraction path catches (e.g. no explicit "X years" statement and no parseable years)

A parsing failure (e.g. a corrupt or unusually-encoded PDF that still passes upload validation) never fails the upload - it's logged server-side and the resume is stored with empty/null parsed fields.

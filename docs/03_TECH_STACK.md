# Tech Stack

Frontend:
- HTML
- CSS
- JavaScript

Backend:
- FastAPI
- SQLAlchemy
- Alembic
- APScheduler

Database:
- PostgreSQL

Libraries:
- PyMuPDF (resume PDF text extraction)
- scikit-learn (TF-IDF + cosine similarity for matching)
- httpx (job fetcher HTTP client - used instead of `requests`, since it has a
  cleaner sync/async story and integrates well with `respx` for testing)
- beautifulsoup4 (HTML-to-text cleanup for job descriptions)

Dev tooling:
- pytest (+ respx for HTTP mocking)
- Black, Ruff (formatting/linting - see `backend/pyproject.toml`)

"""Application configuration.

Settings are loaded from environment variables (and a local .env file in
development). No secrets are hardcoded anywhere in this module.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are populated from environment variables. See `.env.example`
    at the repository root for the full list of expected variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General
    app_name: str = "JobPulse"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # CORS
    cors_allow_origins: str = "*"

    # PostgreSQL
    postgres_user: str = "jobpulse"
    postgres_password: str = "jobpulse"
    postgres_db: str = "jobpulse"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # Single-user V1: no auth, one hardcoded user seeded at startup.
    default_user_id: int = 1
    default_user_full_name: str = "JobPulse User"
    default_user_email: str = "user@jobpulse.local"

    # Resume upload
    resume_upload_dir: str = "uploads/resumes"
    resume_max_size_mb: int = 5

    # Job fetchers (Phase 4). Greenhouse and Lever are per-company APIs with
    # no public directory, so the companies to check are configured here as
    # comma-separated slugs/board-tokens. Remotive and Arbeitnow are general
    # job boards and need no per-company configuration.
    greenhouse_board_tokens: str = ""
    lever_company_slugs: str = ""
    remotive_category: str = "software-dev"
    arbeitnow_max_pages: int = 1
    job_fetch_timeout_seconds: int = 15

    # Matching engine (Phase 7). Weights are combined into one score in
    # [0, 1] and should sum to 1.0 - see docs/09_MATCHING_ENGINE.md for
    # what each factor measures.
    match_weight_text_similarity: float = 0.35
    match_weight_skills: float = 0.25
    match_weight_role: float = 0.15
    match_weight_location: float = 0.10
    match_weight_experience: float = 0.10
    match_weight_remote: float = 0.05
    match_top_n: int = 20
    match_candidate_pool_size: int = 1000

    # Scheduler (Phase 8). Disabled by default at the code level so
    # importing the app (e.g. in tests, or a fresh checkout with no
    # .env) never starts a background thread unexpectedly. Real
    # deployments should set SCHEDULER_ENABLED=true in .env - see
    # .env.example, which defaults it on there since automated daily
    # fetching is the whole point of the product.
    scheduler_enabled: bool = False
    scheduler_fetch_hour: int = 6
    scheduler_fetch_minute: int = 0
    scheduler_timezone: str = "UTC"

    @property
    def database_url(self) -> str:
        """Build the SQLAlchemy database URL from discrete Postgres settings."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so environment parsing only happens once per process.
    """
    return Settings()

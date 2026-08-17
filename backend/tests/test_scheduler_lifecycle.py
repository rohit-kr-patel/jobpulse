"""Tests for app.scheduler.scheduler (build/start/stop lifecycle)."""

from app.core.config import Settings
from app.scheduler.scheduler import build_scheduler, start_scheduler, stop_scheduler


def test_start_scheduler_is_a_noop_when_disabled():
    settings = Settings(scheduler_enabled=False)
    scheduler = start_scheduler(settings)
    assert scheduler is None


def test_start_scheduler_starts_and_registers_the_daily_job_when_enabled():
    settings = Settings(
        scheduler_enabled=True,
        scheduler_fetch_hour=6,
        scheduler_fetch_minute=30,
        scheduler_timezone="UTC",
    )

    scheduler = start_scheduler(settings)
    try:
        assert scheduler is not None
        assert scheduler.running is True
        job_ids = [job.id for job in scheduler.get_jobs()]
        assert "daily_job_fetch_and_rank" in job_ids
    finally:
        stop_scheduler(scheduler)


def test_build_scheduler_uses_configured_hour_and_minute():
    settings = Settings(
        scheduler_fetch_hour=14, scheduler_fetch_minute=45, scheduler_timezone="UTC"
    )

    scheduler = build_scheduler(settings)
    job = scheduler.get_job("daily_job_fetch_and_rank")

    assert "hour='14'" in str(job.trigger)
    assert "minute='45'" in str(job.trigger)


def test_stop_scheduler_is_safe_to_call_with_none():
    stop_scheduler(None)  # should not raise


def test_stop_scheduler_actually_stops_a_running_scheduler():
    settings = Settings(scheduler_enabled=True)
    scheduler = start_scheduler(settings)

    stop_scheduler(scheduler)

    assert scheduler.running is False

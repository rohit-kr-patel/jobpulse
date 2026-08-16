"""Tests for app.services.application_service."""

import pytest

from app.core.config import Settings
from app.core.exceptions import ApplicationNotFoundError, DuplicateApplicationError, JobNotFoundError
from app.models.application import ApplicationStatus
from app.models.job import Job
from app.schemas.application import ApplicationCreateRequest, ApplicationUpdateRequest
from app.services import application_service


@pytest.fixture()
def db_session(client):  # noqa: ARG001 - reuse the `client` fixture's DB setup
    from app.db import session as db_session_module

    session = db_session_module.SessionLocal()
    yield session
    session.close()


def _seed_job(db_session, external_id: str = "1") -> Job:
    job = Job(
        source="greenhouse",
        external_id=external_id,
        title="Backend Engineer",
        company="Acme",
        location="Remote",
        is_remote=True,
        description="Python required.",
        apply_url="https://example.com",
        posted_at=None,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def test_save_job_creates_application_with_default_saved_status(db_session):
    job = _seed_job(db_session)
    payload = ApplicationCreateRequest(job_id=job.id)

    application = application_service.save_job(db_session, Settings(), payload)

    assert application.status == ApplicationStatus.SAVED
    assert application.job_id == job.id
    assert application.applied_at is None
    assert application.rejected_at is None


def test_save_job_raises_for_missing_job(db_session):
    payload = ApplicationCreateRequest(job_id=999999)
    with pytest.raises(JobNotFoundError):
        application_service.save_job(db_session, Settings(), payload)


def test_save_job_raises_for_already_tracked_job(db_session):
    job = _seed_job(db_session)
    payload = ApplicationCreateRequest(job_id=job.id)
    application_service.save_job(db_session, Settings(), payload)

    with pytest.raises(DuplicateApplicationError):
        application_service.save_job(db_session, Settings(), payload)


def test_save_job_with_applied_status_sets_applied_at(db_session):
    job = _seed_job(db_session)
    payload = ApplicationCreateRequest(job_id=job.id, status=ApplicationStatus.APPLIED)

    application = application_service.save_job(db_session, Settings(), payload)

    assert application.applied_at is not None


def test_update_application_changes_status_and_sets_timestamp(db_session):
    job = _seed_job(db_session)
    application = application_service.save_job(db_session, Settings(), ApplicationCreateRequest(job_id=job.id))

    updated = application_service.update_application(
        db_session,
        Settings(),
        application.id,
        ApplicationUpdateRequest(status=ApplicationStatus.APPLIED),
        notes_provided=False,
    )

    assert updated.status == ApplicationStatus.APPLIED
    assert updated.applied_at is not None
    assert updated.rejected_at is None


def test_update_application_notes_omitted_leaves_notes_unchanged(db_session):
    job = _seed_job(db_session)
    application = application_service.save_job(
        db_session, Settings(), ApplicationCreateRequest(job_id=job.id, notes="original note")
    )

    updated = application_service.update_application(
        db_session,
        Settings(),
        application.id,
        ApplicationUpdateRequest(status=ApplicationStatus.APPLIED),
        notes_provided=False,
    )

    assert updated.notes == "original note"


def test_update_application_notes_explicitly_null_clears_notes(db_session):
    job = _seed_job(db_session)
    application = application_service.save_job(
        db_session, Settings(), ApplicationCreateRequest(job_id=job.id, notes="original note")
    )

    updated = application_service.update_application(
        db_session,
        Settings(),
        application.id,
        ApplicationUpdateRequest(notes=None),
        notes_provided=True,
    )

    assert updated.notes is None


def test_update_application_raises_for_missing_id(db_session):
    with pytest.raises(ApplicationNotFoundError):
        application_service.update_application(
            db_session, Settings(), 999999, ApplicationUpdateRequest(), notes_provided=False
        )


def test_list_applications_filters_by_status(db_session):
    job1 = _seed_job(db_session, "1")
    job2 = _seed_job(db_session, "2")
    application_service.save_job(
        db_session, Settings(), ApplicationCreateRequest(job_id=job1.id, status=ApplicationStatus.SAVED)
    )
    application_service.save_job(
        db_session, Settings(), ApplicationCreateRequest(job_id=job2.id, status=ApplicationStatus.APPLIED)
    )

    all_apps = application_service.list_applications(db_session, Settings())
    assert len(all_apps) == 2

    applied_only = application_service.list_applications(
        db_session, Settings(), status=ApplicationStatus.APPLIED
    )
    assert len(applied_only) == 1
    assert applied_only[0].job_id == job2.id

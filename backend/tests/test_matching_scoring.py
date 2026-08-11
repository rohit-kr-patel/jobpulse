"""Tests for app.matching.scoring."""

from app.core.config import Settings
from app.matching.scoring import (
    MatchProfile,
    _experience_score,
    _location_score,
    _remote_score,
    _role_score,
    _skill_score,
    build_profile,
    rank_jobs,
)
from app.models.job import Job
from app.models.preferences import Preferences, WorkMode
from app.models.resume import Resume


def _make_job(job_id: int, title: str, description: str, *, location: str | None, is_remote: bool) -> Job:
    return Job(
        id=job_id,
        source="greenhouse",
        external_id=str(job_id),
        title=title,
        company="Acme",
        location=location,
        is_remote=is_remote,
        description=description,
        apply_url=f"https://example.com/{job_id}",
        posted_at=None,
    )


def _make_profile(**overrides) -> MatchProfile:
    defaults = dict(
        target_roles=["Backend Engineer"],
        skills=["Python", "Docker"],
        locations=["Remote"],
        experience_years=3.0,
        work_mode=WorkMode.REMOTE,
    )
    defaults.update(overrides)
    return MatchProfile(**defaults)


# ---- individual factor scores ----


def test_skill_score_is_fraction_of_matched_skills():
    score = _skill_score(["Python", "Docker", "Kubernetes"], "We use Python and Docker heavily.")
    assert score == 2 / 3


def test_skill_score_is_zero_with_no_profile_skills():
    assert _skill_score([], "Some job text") == 0.0


def test_role_score_matches_substring_case_insensitively():
    assert _role_score(["Backend Engineer"], "Senior Backend Engineer") == 1.0
    assert _role_score(["Backend Engineer"], "Frontend Designer") == 0.0


def test_location_score_matches_preferred_location():
    assert _location_score(["Bangalore", "Remote"], "Remote - US") == 1.0
    assert _location_score(["Bangalore"], "Berlin, Germany") == 0.0
    assert _location_score(["Bangalore"], None) == 0.0


def test_remote_score_any_always_matches():
    assert _remote_score(WorkMode.ANY, True) == 1.0
    assert _remote_score(WorkMode.ANY, False) == 1.0


def test_remote_score_remote_mode_requires_remote_job():
    assert _remote_score(WorkMode.REMOTE, True) == 1.0
    assert _remote_score(WorkMode.REMOTE, False) == 0.0


def test_remote_score_onsite_mode_requires_non_remote_job():
    assert _remote_score(WorkMode.ONSITE, False) == 1.0
    assert _remote_score(WorkMode.ONSITE, True) == 0.0


def test_experience_score_neutral_when_user_experience_unknown():
    assert _experience_score(None, "5+ years of experience required") == 0.5


def test_experience_score_neutral_when_job_states_no_requirement():
    assert _experience_score(3.0, "Great team, no specific experience mentioned") == 0.5


def test_experience_score_full_credit_when_meeting_requirement():
    assert _experience_score(5.0, "3+ years of experience required") == 1.0
    assert _experience_score(3.0, "3+ years of experience required") == 1.0


def test_experience_score_partial_credit_when_under_qualified():
    assert _experience_score(1.0, "4 years of experience required") == 0.25


# ---- build_profile ----


def test_build_profile_combines_preferences_and_resume_skills():
    preferences = Preferences(
        user_id=1,
        target_roles=["Backend Engineer"],
        skills=["Python", "SQL"],
        locations=["Remote"],
        experience_years=2,
        work_mode=WorkMode.REMOTE,
    )
    resume = Resume(
        user_id=1,
        original_filename="resume.pdf",
        stored_path="/tmp/resume.pdf",
        content_type="application/pdf",
        size_bytes=100,
        parsed_skills=["Python", "Docker"],
        parsed_experience_years=4.0,
    )

    profile = build_profile(preferences, resume)

    assert profile.skills == ["Python", "SQL", "Docker"]  # deduped, order preserved
    assert profile.experience_years == 4.0  # resume figure preferred over preferences
    assert profile.target_roles == ["Backend Engineer"]


def test_build_profile_falls_back_to_preferences_experience_without_resume():
    preferences = Preferences(
        user_id=1,
        target_roles=["Backend Engineer"],
        skills=["Python"],
        locations=["Remote"],
        experience_years=2,
        work_mode=WorkMode.REMOTE,
    )

    profile = build_profile(preferences, None)

    assert profile.skills == ["Python"]
    assert profile.experience_years == 2.0


# ---- rank_jobs (integration of all factors) ----


def test_rank_jobs_orders_best_match_first():
    profile = _make_profile()
    strong_match = _make_job(
        1,
        "Backend Engineer",
        "Python, Docker, FastAPI. 3+ years of experience required.",
        location="Remote - US",
        is_remote=True,
    )
    weak_match = _make_job(
        2,
        "Frontend Designer",
        "Figma and CSS skills needed. 5+ years of experience required.",
        location="Berlin, Germany",
        is_remote=False,
    )

    results = rank_jobs(profile, [weak_match, strong_match], Settings())

    assert [r.job.id for r in results] == [1, 2]
    assert results[0].score > results[1].score


def test_rank_jobs_returns_empty_list_for_no_jobs():
    assert rank_jobs(_make_profile(), [], Settings()) == []


def test_rank_jobs_scores_are_bounded_between_0_and_1():
    profile = _make_profile()
    job = _make_job(1, "Backend Engineer", "Python Docker FastAPI", location="Remote", is_remote=True)

    results = rank_jobs(profile, [job], Settings())

    assert 0.0 <= results[0].score <= 1.0

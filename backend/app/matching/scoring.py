"""Job matching and ranking.

Score = weighted sum of six factors, each in [0, 1]:
- text_similarity: TF-IDF cosine similarity between the user's profile
  (target roles + skills) and each job's title+description
- skill_score: fraction of the user's skills found in the job text
- role_score: does the job title mention one of the user's target roles
- location_score: does the job's location match one of the user's
  preferred locations
- experience_score: how well the user's experience meets the job's
  stated requirement (if any)
- remote_score: does the job's remote-ness match the user's work_mode

Weights are configured in Settings (default sum to 1.0) so the balance
is tunable without a code change. No LLMs - see docs/09_MATCHING_ENGINE.md.
"""

import logging
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import Settings
from app.models.job import Job
from app.models.preferences import Preferences, WorkMode
from app.models.resume import Resume
from app.text_extraction import contains_keyword, extract_years_statement

logger = logging.getLogger(__name__)


@dataclass
class MatchProfile:
    """The user's combined matching signal: preferences + (optional) resume."""

    target_roles: list[str]
    skills: list[str]
    locations: list[str]
    experience_years: float | None
    work_mode: WorkMode


@dataclass
class JobMatchResult:
    """One job's score against a profile, with the per-factor breakdown."""

    job: Job
    score: float
    text_similarity: float
    skill_score: float
    role_score: float
    location_score: float
    experience_score: float
    remote_score: float


def build_profile(preferences: Preferences, resume: Resume | None) -> MatchProfile:
    """Combine preferences and (if present) the latest resume into one profile.

    Skills are the union of preference-stated skills and resume-parsed
    skills. Experience prefers the resume's parsed figure (closer to
    ground truth) and falls back to the preferences-stated figure.
    """
    resume_skills = resume.parsed_skills if resume and resume.parsed_skills else []
    combined_skills = list(dict.fromkeys([*preferences.skills, *resume_skills]))

    if resume and resume.parsed_experience_years is not None:
        experience_years = resume.parsed_experience_years
    else:
        experience_years = float(preferences.experience_years)

    return MatchProfile(
        target_roles=preferences.target_roles,
        skills=combined_skills,
        locations=preferences.locations,
        experience_years=experience_years,
        work_mode=WorkMode(preferences.work_mode),
    )


def _profile_text(profile: MatchProfile) -> str:
    return " ".join([*profile.target_roles, *profile.skills])


def _job_text(job: Job) -> str:
    return f"{job.title} {job.description}"


def _compute_text_similarities(profile_text: str, job_texts: list[str]) -> list[float]:
    """TF-IDF-vectorize the profile and every job, then cosine-compare.

    Fails soft (all zeros) if vectorization produces an empty
    vocabulary - e.g. the profile and every job text are blank or
    contain only English stop words.
    """
    if not job_texts:
        return []

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform([profile_text, *job_texts])
    except ValueError:
        logger.warning("TF-IDF produced an empty vocabulary; text similarity scores default to 0")
        return [0.0] * len(job_texts)

    similarities = cosine_similarity(matrix[0:1], matrix[1:])[0]
    return [float(value) for value in similarities]


def _skill_score(profile_skills: list[str], job_text: str) -> float:
    """Fraction of the user's skills mentioned in the job text."""
    if not profile_skills:
        return 0.0
    matched = sum(1 for skill in profile_skills if contains_keyword(job_text, skill))
    return matched / len(profile_skills)


def _role_score(target_roles: list[str], job_title: str) -> float:
    """1.0 if any target role phrase appears in the job title, else 0.0.

    Plain substring match (not the stricter word-boundary check used
    for skills) since role phrases are multi-word and a job title like
    "Engineering Manager" matching a target role of "Engineer" is a
    reasonable, not a false, positive.
    """
    if not target_roles:
        return 0.0
    title_lower = job_title.lower()
    return 1.0 if any(role.lower() in title_lower for role in target_roles) else 0.0


def _location_score(locations: list[str], job_location: str | None) -> float:
    """1.0 if the job's location text matches one of the user's preferred locations."""
    if not locations or not job_location:
        return 0.0
    location_lower = job_location.lower()
    return 1.0 if any(loc.lower() in location_lower for loc in locations) else 0.0


def _remote_score(work_mode: WorkMode, is_remote: bool) -> float:
    """Does the job's remote-ness match the user's preferred work mode?

    "any" always matches. For onsite/hybrid, a non-remote job is
    treated as compatible - the schema only has a remote/not-remote
    boolean per job, not a distinct onsite-vs-hybrid signal.
    """
    if work_mode == WorkMode.ANY:
        return 1.0
    if work_mode == WorkMode.REMOTE:
        return 1.0 if is_remote else 0.0
    return 1.0 if not is_remote else 0.0


def _experience_score(user_years: float | None, job_text: str) -> float:
    """How well the user's experience meets the job's stated requirement.

    Returns a neutral 0.5 (neither rewarded nor penalized) whenever
    either side of the comparison is unknown: no resume/preference
    experience figure, or the job posting doesn't state a requirement.
    Full credit at or above the requirement; partial, proportional
    credit below it.
    """
    if user_years is None:
        return 0.5

    required_years = extract_years_statement(job_text)
    if required_years is None:
        return 0.5
    if required_years <= 0 or user_years >= required_years:
        return 1.0
    return max(0.0, user_years / required_years)


def rank_jobs(profile: MatchProfile, jobs: list[Job], settings: Settings) -> list[JobMatchResult]:
    """Score every job against the profile and return them best-first.

    Callers wanting only the top N should slice the result
    (settings.match_top_n is the configured default for that slice).
    """
    if not jobs:
        return []

    job_texts = [_job_text(job) for job in jobs]
    text_similarities = _compute_text_similarities(_profile_text(profile), job_texts)

    results = []
    for job, job_text, text_similarity in zip(jobs, job_texts, text_similarities):
        skill_score = _skill_score(profile.skills, job_text)
        role_score = _role_score(profile.target_roles, job.title)
        location_score = _location_score(profile.locations, job.location)
        remote_score = _remote_score(profile.work_mode, job.is_remote)
        experience_score = _experience_score(profile.experience_years, job_text)

        score = (
            settings.match_weight_text_similarity * text_similarity
            + settings.match_weight_skills * skill_score
            + settings.match_weight_role * role_score
            + settings.match_weight_location * location_score
            + settings.match_weight_experience * experience_score
            + settings.match_weight_remote * remote_score
        )

        results.append(
            JobMatchResult(
                job=job,
                score=score,
                text_similarity=text_similarity,
                skill_score=skill_score,
                role_score=role_score,
                location_score=location_score,
                experience_score=experience_score,
                remote_score=remote_score,
            )
        )

    results.sort(key=lambda result: result.score, reverse=True)
    return results

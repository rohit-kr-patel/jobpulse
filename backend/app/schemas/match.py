"""Response schema for GET /matches."""

from pydantic import BaseModel, ConfigDict

from app.schemas.job import JobResponse


class JobMatchResponse(BaseModel):
    """A single job's rank result: the job itself plus its score breakdown."""

    model_config = ConfigDict(from_attributes=True)

    job: JobResponse
    score: float
    text_similarity: float
    skill_score: float
    role_score: float
    location_score: float
    experience_score: float
    remote_score: float

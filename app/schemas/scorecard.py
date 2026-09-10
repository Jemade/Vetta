from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator


def compute_overall_score(coding_score: float, communication_rating: float) -> float:
    """Canonical composite score formula: (Coding + Communication) / 2.0."""
    return round((coding_score + communication_rating) / 2.0, 2)


def compute_recommendation(overall_score: float) -> str:
    """Canonical recommendation decision boundaries:
    >= 7.50: Strong Hire
    5.50 - 7.49: Leaning Hire
    < 5.50: Do Not Hire
    """
    if overall_score >= 7.50:
        return "Strong Hire"
    elif overall_score >= 5.50:
        return "Leaning Hire"
    else:
        return "Do Not Hire"


def compute_radar_scores(coding_score: float, communication_rating: float) -> Dict[str, float]:
    """Canonical 5-axis competency radar geometry formulas."""
    arch = min(10.0, max(0.0, coding_score + 0.3))
    code = min(10.0, max(0.0, coding_score))
    comm = min(10.0, max(0.0, communication_rating))
    prob = min(10.0, max(0.0, 0.6 * coding_score + 0.4 * communication_rating))
    own = min(10.0, max(0.0, 0.4 * coding_score + 0.6 * communication_rating))
    return {
        "architecture_and_systems": round(arch, 2),
        "code_quality_and_syntax": round(code, 2),
        "communication_and_clarity": round(comm, 2),
        "problem_solving_depth": round(prob, 2),
        "ownership_and_resilience": round(own, 2),
    }


class Scorecard(BaseModel):
    coding_score: float = Field(..., ge=0.0, le=10.0, description="Technical and coding assessment score (0-10)")
    communication_rating: float = Field(..., ge=0.0, le=10.0, description="Communication and articulation rating (0-10)")
    technical_gaps_identified: List[str] = Field(default_factory=list, description="Identified technical deficiencies")
    follow_up_questions_to_ask: List[str] = Field(default_factory=list, description="Recommended follow-up questions")
    summary: str = Field(..., description="Executive summary of the candidate's interview performance")
    technical_notes: Optional[str] = Field(default=None, description="Detailed technical review remarks")
    communication_notes: Optional[str] = Field(default=None, description="Detailed communication review remarks")
    overall_score: Optional[float] = Field(default=None, description="Authoritative composite score")
    recommendation: Optional[str] = Field(default=None, description="Authoritative recommendation")
    radar_scores: Optional[Dict[str, float]] = Field(default=None, description="5-axis competency radar scores")

    @model_validator(mode="after")
    def populate_authoritative_metrics(self):
        if self.overall_score is None:
            self.overall_score = compute_overall_score(self.coding_score, self.communication_rating)
        if self.recommendation is None:
            self.recommendation = compute_recommendation(self.overall_score)
        if self.radar_scores is None:
            self.radar_scores = compute_radar_scores(self.coding_score, self.communication_rating)
        return self


class InterviewCreateRequest(BaseModel):
    candidate_name: str = Field(..., min_length=1, max_length=255)
    candidate_email: Optional[EmailStr] = Field(default=None)
    role_title: str = Field(..., min_length=1, max_length=255)
    transcript: Optional[str] = Field(default=None, max_length=500000, description="Interview transcript text")
    media_storage_key: Optional[str] = Field(default=None, max_length=512, description="S3 or local storage key of audio/video/document")

    @field_validator("candidate_name", "role_title")
    @classmethod
    def check_not_empty_whitespace(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or solely whitespace.")
        return cleaned


class InterviewCreateResponse(BaseModel):
    task_id: str
    status: str


class InterviewResponse(BaseModel):
    task_id: str
    candidate_name: str
    candidate_email: Optional[str] = None
    role_title: str
    status: str
    scorecard: Optional[Scorecard] = None
    error_message: Optional[str] = None
    media_storage_key: Optional[str] = None
    media_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class InterviewListResponse(BaseModel):
    items: List[InterviewResponse]
    total: int
    page: int
    size: int


class PresignedUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1)
    content_type: str = Field(default="text/plain")


class PresignedUploadResponse(BaseModel):
    upload_url: str
    storage_key: str

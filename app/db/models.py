import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class InterviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    candidate_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[InterviewStatus] = mapped_column(
        SAEnum(InterviewStatus), default=InterviewStatus.PENDING, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    scorecard: Mapped[Optional["ScorecardRecord"]] = relationship(
        "ScorecardRecord",
        back_populates="interview",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ScorecardRecord(Base):
    __tablename__ = "scorecards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    coding_score: Mapped[float] = mapped_column(Float, nullable=False)
    communication_rating: Mapped[float] = mapped_column(Float, nullable=False)
    technical_gaps: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    follow_up_questions: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    technical_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    communication_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, nullable=False
    )

    interview: Mapped["Interview"] = relationship("Interview", back_populates="scorecard")

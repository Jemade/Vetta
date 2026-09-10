import asyncio
import logging
from celery import Celery
from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session_factory
from app.db.models import Interview, ScorecardRecord, InterviewStatus
from app.agents.pipeline import pipeline

logger = logging.getLogger(__name__)

celery_app = Celery(
    "vetta_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


async def execute_interview_assessment(interview_id: str) -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalars().first()
        if not interview:
            logger.error("Interview with ID %s not found for processing", interview_id)
            return

        interview.status = InterviewStatus.PROCESSING
        await session.commit()

        try:
            scorecard = pipeline.run(
                candidate_name=interview.candidate_name,
                role_title=interview.role_title,
                transcript=interview.transcript,
                media_storage_key=interview.media_storage_key,
            )

            scorecard_rec = ScorecardRecord(
                interview_id=interview.id,
                coding_score=scorecard.coding_score,
                communication_rating=scorecard.communication_rating,
                technical_gaps=scorecard.technical_gaps_identified,
                follow_up_questions=scorecard.follow_up_questions_to_ask,
                summary=scorecard.summary,
                technical_notes=scorecard.technical_notes,
                communication_notes=scorecard.communication_notes,
            )
            session.add(scorecard_rec)
            interview.status = InterviewStatus.COMPLETED
            await session.commit()
            logger.info("Successfully assessed interview %s", interview_id)
        except Exception as e:
            logger.exception("Error assessing interview %s: %s", interview_id, e)
            interview.status = InterviewStatus.FAILED
            interview.error_message = str(e)
            await session.commit()


@celery_app.task(name="vetta.process_interview")
def process_interview_task(interview_id: str):
    logger.info("Celery task started for interview %s", interview_id)
    asyncio.run(execute_interview_assessment(interview_id))
    logger.info("Celery task finished for interview %s", interview_id)

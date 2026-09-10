import logging
from typing import Optional

from app.agents.code_reviewer import technical_reviewer
from app.agents.soft_skills import soft_skills_assessor
from app.agents.scorecard import scorecard_synthesizer
from app.schemas.scorecard import Scorecard
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


class AssessmentPipeline:
    """Coordinates multi-agent interview assessment."""

    def run(
        self,
        candidate_name: str,
        role_title: str,
        transcript: Optional[str] = None,
        media_storage_key: Optional[str] = None,
    ) -> Scorecard:
        # Resolve transcript text
        content = transcript
        if not content and media_storage_key:
            try:
                raw_bytes = storage_service.download_bytes(media_storage_key)
                content = raw_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                logger.error("Failed to load transcript from storage key %s: %s", media_storage_key, e)
                content = f"Transcript file loaded from storage {media_storage_key}."

        if not content:
            content = f"Interview transcript for candidate {candidate_name} applying for {role_title}."

        logger.info("Executing assessment pipeline for %s (%s)", candidate_name, role_title)

        # 1. Technical competence review
        tech_result = technical_reviewer.evaluate(content, role_title)

        # 2. Soft skills and articulation review
        soft_result = soft_skills_assessor.evaluate(content, role_title)

        # 3. Scorecard synthesis
        scorecard = scorecard_synthesizer.synthesize(
            candidate_name=candidate_name,
            role_title=role_title,
            tech_result=tech_result,
            soft_result=soft_result,
        )

        logger.info("Assessment pipeline completed successfully for %s", candidate_name)
        return scorecard


pipeline = AssessmentPipeline()

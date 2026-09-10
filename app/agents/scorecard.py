import json
import logging
from typing import List
import httpx

from app.core.config import settings
from app.schemas.scorecard import Scorecard
from app.agents.code_reviewer import TechnicalReviewResult
from app.agents.soft_skills import SoftSkillsReviewResult

logger = logging.getLogger(__name__)


class ScorecardSynthesizer:
    """Synthesizes agent evaluations into a unified scorecard."""

    def synthesize(
        self,
        candidate_name: str,
        role_title: str,
        tech_result: TechnicalReviewResult,
        soft_result: SoftSkillsReviewResult,
    ) -> Scorecard:
        if settings.google_api_key and settings.google_api_key != "your_gemini_api_key_here":
            try:
                return self._synthesize_with_gemini(candidate_name, role_title, tech_result, soft_result)
            except Exception as e:
                logger.warning("Gemini scorecard synthesis failed, using fallback synthesizer: %s", e)

        return self._heuristic_synthesis(candidate_name, role_title, tech_result, soft_result)

    def _synthesize_with_gemini(
        self,
        candidate_name: str,
        role_title: str,
        tech_result: TechnicalReviewResult,
        soft_result: SoftSkillsReviewResult,
    ) -> Scorecard:
        prompt = f"""
Candidate: {candidate_name}
Target Role: {role_title}
Technical Score: {tech_result.score}/10
Technical Notes: {tech_result.notes}
Technical Gaps: {json.dumps(tech_result.gaps)}
Communication Rating: {soft_result.rating}/10
Communication Notes: {soft_result.notes}

Synthesize this data into an executive interview scorecard.
Provide a structured JSON output with:
- "follow_up_questions_to_ask": list of 3-4 deep technical or behavioral follow-up questions targeted to their gaps
- "summary": 2-3 sentence executive recommendation summarizing candidate strengths, fit for {role_title}, and hiring risk

Return ONLY valid JSON:
{{"follow_up_questions_to_ask": ["...", "..."], "summary": "..."}}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.llm_model}:generateContent?key={settings.google_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)
            follow_ups = [str(q) for q in parsed.get("follow_up_questions_to_ask", [])]
            summary = str(parsed.get("summary", f"Evaluation completed for {candidate_name}."))

            return Scorecard(
                coding_score=tech_result.score,
                communication_rating=soft_result.rating,
                technical_gaps_identified=tech_result.gaps,
                follow_up_questions_to_ask=follow_ups,
                summary=summary,
                technical_notes=tech_result.notes,
                communication_notes=soft_result.notes,
            )

    def _heuristic_synthesis(
        self,
        candidate_name: str,
        role_title: str,
        tech_result: TechnicalReviewResult,
        soft_result: SoftSkillsReviewResult,
    ) -> Scorecard:
        questions: List[str] = []
        if tech_result.gaps:
            for gap in tech_result.gaps[:2]:
                questions.append(f"Can you walk through an instance where you addressed: {gap.lower()}?")
        questions.append(f"How do you approach architectural trade-offs when scaling for {role_title} workloads?")
        questions.append("Describe a complex technical conflict you resolved within your engineering team.")

        overall_avg = (tech_result.score + soft_result.rating) / 2
        recommendation = "Recommended for hire" if overall_avg >= 7.5 else ("Proceed with follow-up validation" if overall_avg >= 5.5 else "Does not meet role bar")

        summary = (
            f"{candidate_name} demonstrated a solid foundation for the {role_title} position. "
            f"Technical rating is {tech_result.score}/10 and communication rating is {soft_result.rating}/10. "
            f"Overall assessment: {recommendation}."
        )

        return Scorecard(
            coding_score=tech_result.score,
            communication_rating=soft_result.rating,
            technical_gaps_identified=tech_result.gaps,
            follow_up_questions_to_ask=questions,
            summary=summary,
            technical_notes=tech_result.notes,
            communication_notes=soft_result.notes,
        )


scorecard_synthesizer = ScorecardSynthesizer()

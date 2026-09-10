import json
import logging
from typing import List
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SoftSkillsReviewResult:
    def __init__(self, rating: int, notes: str):
        self.rating = rating
        self.notes = notes


class SoftSkillsAssessor:
    """Evaluates communication clarity, structured thinking, and collaboration."""

    def evaluate(self, transcript: str, role_title: str) -> SoftSkillsReviewResult:
        if settings.google_api_key and settings.google_api_key != "your_gemini_api_key_here":
            try:
                return self._evaluate_with_gemini(transcript, role_title)
            except Exception as e:
                logger.warning("Gemini soft skills evaluation failed, using fallback evaluator: %s", e)

        return self._heuristic_evaluation(transcript, role_title)

    def _evaluate_with_gemini(self, transcript: str, role_title: str) -> SoftSkillsReviewResult:
        prompt = f"""
You are an expert talent interviewer assessing communication and soft skills for: {role_title}.
Analyze the following interview transcript:
---
{transcript}
---

Provide a structured JSON output with:
- "rating": integer from 0 to 10 (communication rating)
- "notes": string (concise review notes on articulation, structure, and responsiveness)

Return ONLY valid JSON:
{{"rating": 8, "notes": "..."}}
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
            rating = max(0, min(10, int(parsed.get("rating", 7))))
            notes = str(parsed.get("notes", "Communication assessment completed."))
            return SoftSkillsReviewResult(rating=rating, notes=notes)

    def _heuristic_evaluation(self, transcript: str, role_title: str) -> SoftSkillsReviewResult:
        text = transcript.lower()
        words = text.split()
        word_count = len(words)

        filler_words = ["um", "uh", "like", "you know", "sort of", "kind of"]
        filler_count = sum(text.count(fw) for fw in filler_words)

        positive_traits = [
            "specifically", "for example", "in summary", "firstly", "secondly",
            "collaborated", "team", "mentored", "impact", "result", "user", "stakeholder"
        ]
        positive_matches = sum(1 for pt in positive_traits if pt in text)

        base_rating = 7
        if word_count < 30:
            base_rating -= 2
        elif word_count > 100:
            base_rating += 1

        if positive_matches >= 2:
            base_rating += 1

        if filler_count > 5:
            base_rating -= 1

        final_rating = max(1, min(10, base_rating))
        notes = (
            f"Candidate showed {'articulate, structured' if final_rating >= 7 else 'adequate'} "
            f"communication suitable for a {role_title}. "
            f"Demonstrated a communication rating of {final_rating}/10."
        )
        return SoftSkillsReviewResult(rating=final_rating, notes=notes)


soft_skills_assessor = SoftSkillsAssessor()

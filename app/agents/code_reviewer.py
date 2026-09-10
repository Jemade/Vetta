import json
import logging
import re
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class TechnicalReviewResult:
    def __init__(self, score: int, gaps: List[str], notes: str):
        self.score = score
        self.gaps = gaps
        self.notes = notes


class TechnicalReviewer:
    """Evaluates technical competence, system design, and coding knowledge."""

    def evaluate(self, transcript: str, role_title: str) -> TechnicalReviewResult:
        if settings.google_api_key and settings.google_api_key != "your_gemini_api_key_here":
            try:
                return self._evaluate_with_gemini(transcript, role_title)
            except Exception as e:
                logger.warning("Gemini evaluation failed, using fallback evaluator: %s", e)

        return self._heuristic_evaluation(transcript, role_title)

    def _evaluate_with_gemini(self, transcript: str, role_title: str) -> TechnicalReviewResult:
        prompt = f"""
You are an expert technical interviewer evaluating a candidate for the role: {role_title}.
Analyze the following interview transcript:
---
{transcript}
---

Provide a structured JSON output with:
- "score": integer from 0 to 10 (technical competency)
- "gaps": list of strings (technical gaps or weaknesses observed)
- "notes": string (concise technical review notes)

Return ONLY valid JSON:
{{"score": 8, "gaps": ["...", "..."], "notes": "..."}}
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
            score = max(0, min(10, int(parsed.get("score", 7))))
            gaps = [str(g) for g in parsed.get("gaps", [])]
            notes = str(parsed.get("notes", "Technical assessment completed."))
            return TechnicalReviewResult(score=score, gaps=gaps, notes=notes)

    def _heuristic_evaluation(self, transcript: str, role_title: str) -> TechnicalReviewResult:
        text = transcript.lower()
        length = len(text.split())

        positive_indicators = [
            "architecture", "distributed", "scalability", "complexity", "database",
            "concurrency", "algorithm", "tradeoff", "latency", "async", "cache",
            "microservices", "testing", "ci/cd", "kubernetes", "docker", "pipeline",
            "optimization", "security", "design pattern", "api", "framework"
        ]
        matched_indicators = [w for w in positive_indicators if w in text]

        gap_indicators = [
            ("not sure", "Hesitation on core technical fundamentals"),
            ("forgot", "Gaps in recollection of specific frameworks or syntax"),
            ("never used", "Lack of direct production experience with mentioned tools"),
            ("slow", "Possible latency or efficiency bottlenecks in proposed approach"),
            ("monolith", "Limited modern distributed systems pattern articulation"),
        ]
        detected_gaps = [reason for phrase, reason in gap_indicators if phrase in text]

        base_score = 6
        bonus = min(3, len(matched_indicators) // 2)
        penalty = min(3, len(detected_gaps))

        if length < 40:
            base_score = 4
            detected_gaps.append("Interview transcript is too short to fully verify technical depth")

        final_score = max(1, min(10, base_score + bonus - penalty))
        notes = (
            f"Candidate evaluated for {role_title}. Identified familiarity with "
            f"{', '.join(matched_indicators[:4]) if matched_indicators else 'general concepts'}. "
            f"Demonstrated {final_score}/10 technical domain mastery."
        )

        if not detected_gaps:
            detected_gaps = ["Further probing required for advanced edge cases and failure modes"]

        return TechnicalReviewResult(score=final_score, gaps=detected_gaps, notes=notes)


technical_reviewer = TechnicalReviewer()

import pytest
from app.agents.code_reviewer import technical_reviewer
from app.agents.soft_skills import soft_skills_assessor
from app.agents.scorecard import scorecard_synthesizer
from app.agents.pipeline import pipeline


def test_technical_reviewer_heuristic():
    transcript = (
        "Interviewer: How do you design a scalable cache? "
        "Candidate: In our distributed architecture, we used Redis for caching to reduce latency. "
        "We analyzed the complexity of our database queries and introduced asynchronous workers."
    )
    result = technical_reviewer.evaluate(transcript, "Backend Engineer")
    assert 1 <= result.score <= 10
    assert isinstance(result.gaps, list)
    assert len(result.notes) > 0


def test_soft_skills_assessor_heuristic():
    transcript = (
        "Candidate: Firstly, I collaborated with our product manager and team. "
        "Specifically, for example, we reduced customer friction and improved stakeholder alignment. "
        "In summary, clear communication was key."
    )
    result = soft_skills_assessor.evaluate(transcript, "Engineering Lead")
    assert 1 <= result.rating <= 10
    assert "Engineering Lead" in result.notes


def test_scorecard_synthesizer():
    tech_res = technical_reviewer.evaluate(
        "I built distributed microservices with docker and kubernetes.", "DevOps Engineer"
    )
    soft_res = soft_skills_assessor.evaluate(
        "I collaborated with the team to improve deployment pipelines.", "DevOps Engineer"
    )

    scorecard = scorecard_synthesizer.synthesize(
        candidate_name="Jane Doe",
        role_title="DevOps Engineer",
        tech_result=tech_res,
        soft_result=soft_res,
    )

    assert 0 <= scorecard.coding_score <= 10
    assert 0 <= scorecard.communication_rating <= 10
    assert len(scorecard.follow_up_questions_to_ask) > 0
    assert "Jane Doe" in scorecard.summary


def test_full_pipeline_execution():
    transcript = (
        "Interviewer: Can you explain your experience with concurrency? "
        "Candidate: We used asyncio and worker queues to optimize database throughput and minimize latency."
    )
    scorecard = pipeline.run(
        candidate_name="Alex Rivera",
        role_title="Senior Python Architect",
        transcript=transcript,
    )
    assert scorecard.coding_score >= 5
    assert len(scorecard.technical_gaps_identified) >= 1
    assert len(scorecard.follow_up_questions_to_ask) >= 1
    assert "Alex Rivera" in scorecard.summary


def test_scorecard_mathematics_and_boundary_thresholds():
    from app.schemas.scorecard import (
        compute_overall_score,
        compute_recommendation,
        compute_radar_scores,
        Scorecard,
    )

    # 1. Test exact composite score
    assert compute_overall_score(8.0, 6.0) == 7.0
    assert compute_overall_score(5.49, 5.49) == 5.49
    assert compute_overall_score(10.0, 10.0) == 10.0
    assert compute_overall_score(0.0, 0.0) == 0.0

    # 2. Test boundary recommendation thresholds: 5.49, 5.50, 7.49, 7.50, 10.0, 0.0
    assert compute_recommendation(0.0) == "Do Not Hire"
    assert compute_recommendation(5.49) == "Do Not Hire"
    assert compute_recommendation(5.50) == "Leaning Hire"
    assert compute_recommendation(6.50) == "Leaning Hire"
    assert compute_recommendation(7.49) == "Leaning Hire"
    assert compute_recommendation(7.50) == "Strong Hire"
    assert compute_recommendation(10.0) == "Strong Hire"

    # 3. Test radar formulas across boundary values
    radar_max = compute_radar_scores(10.0, 10.0)
    assert radar_max["architecture_and_systems"] == 10.0  # capped at 10.0
    assert radar_max["code_quality_and_syntax"] == 10.0
    assert radar_max["communication_and_clarity"] == 10.0
    assert radar_max["problem_solving_depth"] == 10.0
    assert radar_max["ownership_and_resilience"] == 10.0

    radar_zero = compute_radar_scores(0.0, 0.0)
    assert radar_zero["architecture_and_systems"] == 0.3
    assert radar_zero["code_quality_and_syntax"] == 0.0
    assert radar_zero["communication_and_clarity"] == 0.0
    assert radar_zero["problem_solving_depth"] == 0.0
    assert radar_zero["ownership_and_resilience"] == 0.0

    radar_mid = compute_radar_scores(7.0, 9.0)
    assert radar_mid["architecture_and_systems"] == 7.3
    assert radar_mid["code_quality_and_syntax"] == 7.0
    assert radar_mid["communication_and_clarity"] == 9.0
    assert radar_mid["problem_solving_depth"] == round(0.6 * 7.0 + 0.4 * 9.0, 2)  # 7.8
    assert radar_mid["ownership_and_resilience"] == round(0.4 * 7.0 + 0.6 * 9.0, 2)  # 8.2

    # 4. Test Scorecard model validator auto-computes metrics
    sc = Scorecard(
        coding_score=7.5,
        communication_rating=7.5,
        summary="Test candidate evaluation.",
    )
    assert sc.overall_score == 7.5
    assert sc.recommendation == "Strong Hire"
    assert sc.radar_scores["code_quality_and_syntax"] == 7.5


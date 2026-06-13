"""
Unit tests for the scoring system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.profile_parser import parse_candidate, CandidateProfile
from src.feature_extractor import extract_features, check_honeypot
from src.scoring import score_candidate, ScoreBreakdown
from src.behavioral import process_behavioral_signals


def test_parse_candidate():
    """Test candidate parsing."""
    data = {
        "candidate_id": "CAND_0000001",
        "profile": {
            "anonymized_name": "Test User",
            "headline": "ML Engineer",
            "summary": "Test summary",
            "location": "Pune",
            "country": "India",
            "years_of_experience": 7.0,
            "current_title": "ML Engineer",
            "current_company": "TechCorp",
            "current_company_size": "201-500",
            "current_industry": "Technology",
        },
        "career_history": [],
        "education": [],
        "skills": [],
        "redrob_signals": {
            "profile_completeness_score": 80.0,
            "open_to_work_flag": True,
            "notice_period_days": 30,
            "recruiter_response_rate": 0.7,
            "interview_completion_rate": 0.8,
        },
    }

    profile = parse_candidate(data)
    assert profile.candidate_id == "CAND_0000001"
    assert profile.years_of_experience == 7.0
    assert profile.current_title == "ML Engineer"
    assert profile.redrob_signals.open_to_work_flag is True


def test_extract_features():
    """Test feature extraction."""
    data = {
        "candidate_id": "CAND_0000001",
        "profile": {
            "anonymized_name": "Test User",
            "headline": "ML Engineer",
            "summary": "Machine learning engineer with 7 years experience",
            "location": "Pune",
            "country": "India",
            "years_of_experience": 7.0,
            "current_title": "ML Engineer",
            "current_company": "TechCorp",
            "current_company_size": "201-500",
            "current_industry": "Technology",
        },
        "career_history": [],
        "education": [],
        "skills": [
            {"name": "Python", "proficiency": "expert", "endorsements": 10},
            {"name": "Machine Learning", "proficiency": "advanced", "endorsements": 5},
        ],
        "redrob_signals": {
            "profile_completeness_score": 80.0,
            "open_to_work_flag": True,
        },
    }

    profile = parse_candidate(data)
    features = extract_features(profile)

    assert features.candidate_id == "CAND_0000001"
    assert features.years_of_experience == 7.0
    assert features.experience_in_range is True
    assert features.ai_skill_count >= 2


def test_score_candidate():
    """Test candidate scoring."""
    data = {
        "candidate_id": "CAND_0000001",
        "profile": {
            "anonymized_name": "Test User",
            "headline": "ML Engineer",
            "summary": "Machine learning engineer",
            "location": "Pune",
            "country": "India",
            "years_of_experience": 7.0,
            "current_title": "ML Engineer",
            "current_company": "TechCorp",
            "current_company_size": "201-500",
            "current_industry": "Technology",
        },
        "career_history": [],
        "education": [],
        "skills": [
            {"name": "Python", "proficiency": "expert", "endorsements": 10},
            {"name": "Machine Learning", "proficiency": "advanced", "endorsements": 5},
        ],
        "redrob_signals": {
            "profile_completeness_score": 80.0,
            "open_to_work_flag": True,
            "notice_period_days": 30,
            "recruiter_response_rate": 0.7,
            "interview_completion_rate": 0.8,
        },
    }

    profile = parse_candidate(data)
    score, breakdown = score_candidate(profile)

    assert 0 <= score <= 1
    assert isinstance(breakdown, ScoreBreakdown)
    assert breakdown.raw_score >= 0


def test_honeypot_detection():
    """Test honeypot detection."""
    # Normal candidate
    normal_data = {
        "candidate_id": "CAND_0000001",
        "profile": {
            "anonymized_name": "Normal User",
            "headline": "Engineer",
            "summary": "Test",
            "location": "Pune",
            "country": "India",
            "years_of_experience": 7.0,
            "current_title": "Engineer",
            "current_company": "TechCorp",
            "current_company_size": "201-500",
            "current_industry": "Technology",
        },
        "career_history": [],
        "education": [],
        "skills": [],
        "redrob_signals": {},
    }

    normal_profile = parse_candidate(normal_data)
    assert check_honeypot(normal_profile) is False


def test_behavioral_signals():
    """Test behavioral signal processing."""
    data = {
        "candidate_id": "CAND_0000001",
        "profile": {
            "anonymized_name": "Test User",
            "headline": "Engineer",
            "summary": "Test",
            "location": "Pune",
            "country": "India",
            "years_of_experience": 7.0,
            "current_title": "Engineer",
            "current_company": "TechCorp",
            "current_company_size": "201-500",
            "current_industry": "Technology",
        },
        "career_history": [],
        "education": [],
        "skills": [],
        "redrob_signals": {
            "open_to_work_flag": True,
            "notice_period_days": 30,
            "last_active_date": "2026-06-14",
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 12,
            "interview_completion_rate": 0.9,
            "profile_completeness_score": 85.0,
        },
    }

    profile = parse_candidate(data)
    scores = process_behavioral_signals(profile)

    assert 0 <= scores.availability_score <= 1
    assert 0 <= scores.engagement_score <= 1
    assert 0 <= scores.quality_score <= 1
    assert 0.3 <= scores.composite_modifier <= 1.0


if __name__ == "__main__":
    test_parse_candidate()
    test_extract_features()
    test_score_candidate()
    test_honeypot_detection()
    test_behavioral_signals()
    print("All tests passed!")

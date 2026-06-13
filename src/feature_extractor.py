"""
Feature Extractor for Redrob AI Challenge.
Extracts numerical features from candidate profiles for scoring.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Set, Tuple
import re

from .profile_parser import CandidateProfile, Skill, CareerEntry
from .jd_parser import (
    JobRequirements,
    get_job_requirements,
    calculate_title_relevance,
    calculate_company_type_score,
)


# AI/ML skill keywords for matching
AI_SKILL_KEYWORDS = {
    "machine learning", "deep learning", "neural network", "nlp",
    "natural language processing", "computer vision", "reinforcement learning",
    "transformer", "bert", "gpt", "llm", "large language model",
    "embedding", "vector", "retrieval", "search", "ranking",
    "fine-tuning", "finetuning", "lora", "qlora", "peft",
    "rag", "retrieval augmented generation",
    "pytorch", "tensorflow", "keras", "jax",
    "scikit-learn", "sklearn", "xgboost", "lightgbm",
    "huggingface", "hugging face", "transformers",
    "faiss", "pinecone", "weaviate", "qdrant", "milvus",
    "elasticsearch", "opensearch",
    "airflow", "spark", "kafka",
    "docker", "kubernetes", "k8s",
    "aws", "gcp", "azure",
    "python", "sql", "scala", "java",
    "data pipeline", "etl", "data engineering",
    "mlops", "ml ops", "model deployment",
    "a/b testing", "ab testing", "experiment",
    "ndcg", "mrr", "map", "precision", "recall",
    "recommendation system", "recommendation engine",
    "speech recognition", "text to speech", "tts", "asr",
    "image classification", "object detection", "segmentation",
    "generative ai", "gen ai", "stable diffusion", "dall-e",
    "langchain", "llamaindex", "llama index",
}


# Location tier mapping for India
INDIA_LOCATION_TIERS = {
    # Tier 1 (preferred by JD)
    "pune": 1.0,
    "noida": 1.0,
    "delhi": 0.9,
    "ncr": 0.9,
    "gurgaon": 0.9,
    "gurugram": 0.9,
    "faridabad": 0.85,
    "ghaziabad": 0.85,

    # Tier 1 (other major metros)
    "bangalore": 0.85,
    "bengaluru": 0.85,
    "hyderabad": 0.85,
    "mumbai": 0.85,
    "chennai": 0.8,
    "kolkata": 0.75,

    # Tier 2
    "ahmedabad": 0.7,
    "jaipur": 0.7,
    "lucknow": 0.65,
    "chandigarh": 0.7,
    "indore": 0.65,
    "bhopal": 0.65,
    "coimbatore": 0.65,
    "kochi": 0.65,
    "thiruvananthapuram": 0.65,
}


@dataclass
class CandidateFeatures:
    """Extracted features for a candidate."""
    candidate_id: str

    # Experience features
    years_of_experience: float = 0.0
    experience_in_range: bool = False  # 5-9 years
    recent_coding_active: bool = False  # Code in last 18 months

    # Title and career features
    title_relevance: float = 0.0
    company_type_score: float = 0.0
    avg_tenure_months: float = 0.0
    job_hopping_score: float = 0.0  # Negative if hopping
    product_company_ratio: float = 0.0

    # Skills features
    ai_skill_count: int = 0
    core_ai_skill_score: float = 0.0
    skill_proficiency_score: float = 0.0
    has_production_skills: bool = False

    # Location features
    location_score: float = 0.0
    willing_to_relocate: bool = False

    # Education features
    education_tier_score: float = 0.0
    relevant_field: bool = False

    # Behavioral features
    open_to_work: bool = False
    notice_period_days: int = 0
    recruiter_response_rate: float = 0.0
    interview_completion_rate: float = 0.0
    profile_completeness: float = 0.0
    github_score: float = -1.0

    # Summary text for reasoning
    summary_text: str = ""


def extract_ai_skills(skills: List[Skill], text: str) -> Tuple[int, float, bool]:
    """Extract AI-related skills from skill list and text.

    Args:
        skills: List of Skill objects.
        text: All text content from profile.

    Returns:
        Tuple of (skill_count, proficiency_score, has_production_skills).
    """
    skill_count = 0
    total_proficiency = 0.0
    proficiency_map = {
        "beginner": 0.25,
        "intermediate": 0.5,
        "advanced": 0.75,
        "expert": 1.0,
    }
    has_production = False

    text_lower = text.lower()

    for skill in skills:
        skill_name_lower = skill.name.lower()
        # Check if skill is AI-related
        if any(keyword in skill_name_lower for keyword in AI_SKILL_KEYWORDS):
            skill_count += 1
            total_proficiency += proficiency_map.get(skill.proficiency, 0.5)

            # Check for production-related skills
            if any(prod in skill_name_lower for prod in [
                "production", "deploy", "pipeline", "mlops", "kubernetes",
                "docker", "airflow", "spark", "kafka", "elasticsearch",
                "faiss", "pinecone", "weaviate", "qdrant"
            ]):
                has_production = True

    # Also check text for AI keywords not in skills
    text_ai_count = sum(1 for kw in AI_SKILL_KEYWORDS if kw in text_lower)
    skill_count = max(skill_count, text_ai_count)

    avg_proficiency = total_proficiency / max(skill_count, 1)
    return skill_count, avg_proficiency, has_production


def extract_location_score(location: str, country: str, willing_to_relocate: bool) -> float:
    """Calculate location match score.

    Args:
        location: Candidate's location.
        country: Candidate's country.
        willing_to_relocate: Whether candidate is willing to relocate.

    Returns:
        Score between 0.0 and 1.0.
    """
    location_lower = location.lower()

    # Check India locations
    if country.lower() == "india":
        for city, score in INDIA_LOCATION_TIERS.items():
            if city in location_lower:
                return score

    # International candidates
    if country.lower() != "india":
        if willing_to_relocate:
            return 0.5
        return 0.2

    # Unknown location in India
    if willing_to_relocate:
        return 0.6

    return 0.4


def calculate_tenure_features(career_history: List[CareerEntry]) -> Tuple[float, float, float]:
    """Calculate tenure-related features.

    Args:
        career_history: List of CareerEntry objects.

    Returns:
        Tuple of (avg_tenure, job_hopping_score, product_company_ratio).
    """
    if not career_history:
        return 0.0, 0.0, 0.0

    total_months = sum(entry.duration_months for entry in career_history)
    avg_tenure = total_months / len(career_history)

    # Job hopping detection (avg < 18 months is bad)
    if avg_tenure < 12:
        job_hopping_score = -0.5
    elif avg_tenure < 18:
        job_hopping_score = -0.2
    elif avg_tenure < 24:
        job_hopping_score = 0.0
    elif avg_tenure < 48:
        job_hopping_score = 0.2
    else:
        job_hopping_score = 0.3

    # Product company ratio
    product_count = 0
    for entry in career_history:
        industry_lower = entry.industry.lower()
        if any(ind in industry_lower for ind in [
            "technology", "ai", "ml", "software", "saas", "platform", "product"
        ]):
            product_count += 1
        # Also check for consulting firms (negative)
        if any(firm in entry.company.lower() for firm in [
            "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini"
        ]):
            product_count -= 0.5

    product_ratio = max(0, product_count / len(career_history))

    return avg_tenure, job_hopping_score, product_ratio


def check_recent_coding(career_history: List[CareerEntry], current_title: str) -> bool:
    """Check if candidate has been coding recently (last 18 months).

    Args:
        career_history: List of CareerEntry objects.
        current_title: Current job title.

    Returns:
        True if candidate has been active in coding.
    """
    current_date = date.today()
    eighteen_months_ago = date(
        current_date.year - 1,
        (current_date.month - 6) % 12 + 1,
        current_date.day
    )

    # Check current role
    title_lower = current_title.lower()
    coding_titles = [
        "engineer", "developer", "scientist", "architect",
        "ml", "ai", "data", "software", "backend", "frontend",
        "fullstack", "full stack", "devops", "sre",
    ]

    if any(term in title_lower for term in coding_titles):
        return True

    # Check recent career entries
    for entry in career_history:
        if entry.end_date is None:  # Current role
            if any(term in entry.title.lower() for term in coding_titles):
                return True

    return False


def check_honeypot(profile: CandidateProfile) -> bool:
    """Check if a candidate profile is a honeypot (fake/suspicious).

    Args:
        profile: CandidateProfile to check.

    Returns:
        True if profile appears to be a honeypot.
    """
    # Check for impossible experience
    if profile.years_of_experience > 10:
        # Check if any company existed before candidate could have worked there
        for entry in profile.career_history:
            if entry.start_year and entry.start_year < 1990:
                return True

    # Check for too many expert skills with 0 duration
    expert_skills_with_zero_duration = sum(
        1 for s in profile.skills
        if s.proficiency == "expert" and s.duration_months == 0
    )
    if expert_skills_with_zero_duration > 5:
        return True

    # Check for inconsistent dates
    for entry in profile.career_history:
        if entry.start_date and entry.end_date:
            if entry.start_date > entry.end_date:
                return True

    return False


def extract_features(profile: CandidateProfile) -> CandidateFeatures:
    """Extract all features from a candidate profile.

    Args:
        profile: CandidateProfile object.

    Returns:
        CandidateFeatures with all extracted features.
    """
    requirements = get_job_requirements()

    # Basic info
    years = profile.years_of_experience
    experience_in_range = requirements.min_years <= years <= requirements.max_years

    # Title relevance
    title_rel = calculate_title_relevance(profile.current_title)

    # Company type
    company_score = calculate_company_type_score(
        profile.current_company,
        profile.current_industry,
        profile.current_company_size,
    )

    # Tenure features
    avg_tenure, job_hopping, product_ratio = calculate_tenure_features(
        profile.career_history
    )

    # Recent coding activity
    recent_coding = check_recent_coding(profile.career_history, profile.current_title)

    # AI skills
    all_text = profile.all_text
    ai_skill_count, skill_proficiency, has_production = extract_ai_skills(
        profile.skills, all_text
    )

    # Location
    location_score = extract_location_score(
        profile.location, profile.country, profile.redrob_signals.willing_to_relocate
    )

    # Education
    edu_tier_score = 0.0
    relevant_field = False
    for edu in profile.education:
        if edu.tier == "tier_1":
            edu_tier_score = max(edu_tier_score, 0.1)
        elif edu.tier == "tier_2":
            edu_tier_score = max(edu_tier_score, 0.05)

        field_lower = edu.field_of_study.lower()
        if any(field in field_lower for field in [
            "computer science", "computer", "software", "ai", "ml",
            "machine learning", "data science", "electrical", "electronics"
        ]):
            relevant_field = True

    # Core AI skill score (normalized)
    core_ai_score = min(ai_skill_count / 10.0, 1.0)

    return CandidateFeatures(
        candidate_id=profile.candidate_id,
        years_of_experience=years,
        experience_in_range=experience_in_range,
        recent_coding_active=recent_coding,
        title_relevance=title_rel,
        company_type_score=company_score,
        avg_tenure_months=avg_tenure,
        job_hopping_score=job_hopping,
        product_company_ratio=product_ratio,
        ai_skill_count=ai_skill_count,
        core_ai_skill_score=core_ai_score,
        skill_proficiency_score=skill_proficiency,
        has_production_skills=has_production,
        location_score=location_score,
        willing_to_relocate=profile.redrob_signals.willing_to_relocate,
        education_tier_score=edu_tier_score,
        relevant_field=relevant_field,
        open_to_work=profile.redrob_signals.open_to_work_flag,
        notice_period_days=profile.redrob_signals.notice_period_days,
        recruiter_response_rate=profile.redrob_signals.recruiter_response_rate,
        interview_completion_rate=profile.redrob_signals.interview_completion_rate,
        profile_completeness=profile.redrob_signals.profile_completeness_score,
        github_score=profile.redrob_signals.github_activity_score,
        summary_text=f"{profile.current_title} at {profile.current_company} with {years:.1f} years",
    )

"""
Reasoning Generator for Redrob AI Challenge.
Generates human-readable reasoning for each candidate ranking.
"""

from typing import List

from .profile_parser import CandidateProfile
from .feature_extractor import CandidateFeatures, extract_features
from .behavioral import BehavioralScores, process_behavioral_signals
from .scoring import ScoreBreakdown


def generate_reasoning(
    profile: CandidateProfile,
    features: CandidateFeatures,
    behavioral: BehavioralScores,
    breakdown: ScoreBreakdown,
    rank: int,
    score: float,
) -> str:
    """Generate reasoning for a candidate's ranking.

    Args:
        profile: CandidateProfile object.
        features: CandidateFeatures object.
        behavioral: BehavioralScores object.
        breakdown: ScoreBreakdown object.
        rank: Candidate's rank (1-100).
        score: Final score.

    Returns:
        1-2 sentence reasoning string.
    """
    # Collect key factors
    strengths = []
    concerns = []

    # Title and role match
    if features.title_relevance >= 0.8:
        strengths.append(f"{profile.current_title} with strong role alignment")
    elif features.title_relevance >= 0.5:
        strengths.append(f"{profile.current_title} with relevant background")
    elif features.title_relevance < 0:
        concerns.append(f"Title '{profile.current_title}' has low relevance")

    # Experience
    if features.experience_in_range:
        strengths.append(f"{features.years_of_experience:.1f} yrs experience (in target range)")
    elif features.years_of_experience > 9:
        concerns.append(f"{features.years_of_experience:.1f} yrs (above target range)")
    elif features.years_of_experience < 5:
        concerns.append(f"{features.years_of_experience:.1f} yrs (below target range)")

    # AI skills
    if features.ai_skill_count >= 8:
        strengths.append(f"{features.ai_skill_count} AI core skills")
    elif features.ai_skill_count >= 5:
        strengths.append(f"{features.ai_skill_count} AI skills")
    elif features.ai_skill_count >= 3:
        strengths.append(f"{features.ai_skill_count} AI skills")
    else:
        concerns.append(f"Only {features.ai_skill_count} AI skills")

    # Production experience
    if features.has_production_skills:
        strengths.append("production ML experience")

    # Company type
    if features.product_company_ratio > 0.6:
        strengths.append("product company background")
    elif features.company_type_score < -0.3:
        concerns.append("consulting/services background")

    # Behavioral signals
    if behavioral.availability_score >= 0.7:
        strengths.append("high availability")
    elif behavioral.availability_score < 0.4:
        concerns.append("limited availability")

    if features.recruiter_response_rate >= 0.6:
        strengths.append(f"response rate {features.recruiter_response_rate:.0%}")

    if features.open_to_work:
        strengths.append("open to work")

    # Location
    if features.location_score >= 0.85:
        strengths.append("preferred location")
    elif features.location_score < 0.5:
        concerns.append("location mismatch")

    # Education
    if features.relevant_field:
        strengths.append("relevant degree")

    # GitHub activity
    if features.github_score >= 70:
        strengths.append("strong GitHub activity")
    elif features.github_score >= 40:
        strengths.append("active GitHub")

    # Build reasoning
    parts = []

    # Main fit statement
    if score >= 0.8:
        parts.append(f"Strong fit")
    elif score >= 0.6:
        parts.append(f"Good fit")
    elif score >= 0.4:
        parts.append(f"Moderate fit")
    else:
        parts.append(f"Lower fit")

    # Add key details
    if strengths:
        parts.append(f"– {'; '.join(strengths[:3])}")

    if concerns and score < 0.6:
        parts.append(f"– {'; '.join(concerns[:2])}")

    # Combine into 1-2 sentences
    reasoning = " ".join(parts)

    # Ensure reasonable length
    if len(reasoning) > 200:
        reasoning = reasoning[:197] + "..."

    return reasoning


def generate_reasoning_batch(
    profiles: List[CandidateProfile],
    scored_candidates: List[tuple],
) -> List[str]:
    """Generate reasoning for a batch of scored candidates.

    Args:
        profiles: List of CandidateProfile objects.
        scored_candidates: List of (candidate_id, score, breakdown, rank) tuples.

    Returns:
        List of reasoning strings in the same order as scored_candidates.
    """
    # Create lookup by candidate_id
    profile_lookup = {p.candidate_id: p for p in profiles}

    reasoning_list = []

    for candidate_id, score, breakdown, rank in scored_candidates:
        profile = profile_lookup.get(candidate_id)
        if profile is None:
            reasoning_list.append("Profile not found")
            continue

        features = extract_features(profile)
        behavioral = process_behavioral_signals(profile)

        reasoning = generate_reasoning(
            profile=profile,
            features=features,
            behavioral=behavioral,
            breakdown=breakdown,
            rank=rank,
            score=score,
        )

        reasoning_list.append(reasoning)

    return reasoning_list

"""
Scoring Engine for Redrob AI Challenge.
Combines all features into a final candidate score.
"""

from dataclasses import dataclass
from typing import List, Tuple

from .profile_parser import CandidateProfile
from .feature_extractor import CandidateFeatures, extract_features, check_honeypot
from .behavioral import BehavioralScores, process_behavioral_signals
from .jd_parser import get_job_requirements


@dataclass
class ScoringWeights:
    """Weights for different scoring components."""
    skills_weight: float = 0.35
    career_weight: float = 0.30
    experience_weight: float = 0.20
    location_weight: float = 0.10
    education_weight: float = 0.05


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of how a score was calculated."""
    skills_score: float = 0.0
    career_score: float = 0.0
    experience_score: float = 0.0
    location_score: float = 0.0
    education_score: float = 0.0
    raw_score: float = 0.0
    behavioral_modifier: float = 1.0
    final_score: float = 0.0
    is_honeypot: bool = False


def calculate_skills_score(features: CandidateFeatures) -> float:
    """Calculate skills match score (0-1).

    Components:
    - Core AI skill score (0.5 weight)
    - Skill proficiency (0.3 weight)
    - Production skills bonus (0.2 weight)

    Args:
        features: CandidateFeatures object.

    Returns:
        Score between 0.0 and 1.0.
    """
    score = 0.0

    # Core AI skill score (already normalized 0-1)
    score += features.core_ai_skill_score * 0.5

    # Skill proficiency
    score += features.skill_proficiency_score * 0.3

    # Production skills bonus
    if features.has_production_skills:
        score += 0.2

    return min(score, 1.0)


def calculate_career_score(features: CandidateFeatures) -> float:
    """Calculate career trajectory score (0-1).

    Components:
    - Title relevance (0.4 weight, normalized to 0-1)
    - Company type (0.3 weight, normalized to 0-1)
    - Product company ratio (0.2 weight)
    - Job hopping penalty (0.1 weight)

    Args:
        features: CandidateFeatures object.

    Returns:
        Score between 0.0 and 1.0.
    """
    score = 0.0

    # Title relevance (normalize -1 to 1 -> 0 to 1)
    title_norm = (features.title_relevance + 1.0) / 2.0
    score += title_norm * 0.4

    # Company type (normalize -1 to 1 -> 0 to 1)
    company_norm = (features.company_type_score + 1.0) / 2.0
    score += company_norm * 0.3

    # Product company ratio
    score += features.product_company_ratio * 0.2

    # Job hopping (normalize -0.5 to 0.3 -> 0 to 1)
    hopping_norm = (features.job_hopping_score + 0.5) / 0.8
    hopping_norm = max(0, min(1, hopping_norm))
    score += hopping_norm * 0.1

    return min(score, 1.0)


def calculate_experience_score(features: CandidateFeatures) -> float:
    """Calculate experience level score (0-1).

    Components:
    - Years in range (0.5 weight)
    - Recent coding activity (0.5 weight)

    Args:
        features: CandidateFeatures object.

    Returns:
        Score between 0.0 and 1.0.
    """
    score = 0.0

    # Years in range
    if features.experience_in_range:
        score += 0.5
    else:
        # Partial credit for being close to range
        years = features.years_of_experience
        if 3 <= years <= 11:
            score += 0.25
        elif 1 <= years <= 13:
            score += 0.1

    # Recent coding activity
    if features.recent_coding_active:
        score += 0.5

    return min(score, 1.0)


def calculate_location_score(features: CandidateFeatures) -> float:
    """Calculate location match score (0-1).

    Args:
        features: CandidateFeatures object.

    Returns:
        Score between 0.0 and 1.0.
    """
    return features.location_score


def calculate_education_score(features: CandidateFeatures) -> float:
    """Calculate education score (0-1).

    Components:
    - Institution tier (0.6 weight)
    - Relevant field (0.4 weight)

    Args:
        features: CandidateFeatures object.

    Returns:
        Score between 0.0 and 1.0.
    """
    score = 0.0

    # Institution tier
    score += features.education_tier_score * 6.0  # Normalize to 0-0.6

    # Relevant field
    if features.relevant_field:
        score += 0.4

    return min(score, 1.0)


def calculate_raw_score(
    features: CandidateFeatures,
    weights: ScoringWeights = None,
) -> Tuple[float, ScoreBreakdown]:
    """Calculate raw score before behavioral modification.

    Args:
        features: CandidateFeatures object.
        weights: Optional custom weights.

    Returns:
        Tuple of (raw_score, ScoreBreakdown).
    """
    if weights is None:
        weights = ScoringWeights()

    skills = calculate_skills_score(features)
    career = calculate_career_score(features)
    experience = calculate_experience_score(features)
    location = calculate_location_score(features)
    education = calculate_education_score(features)

    raw_score = (
        weights.skills_weight * skills +
        weights.career_weight * career +
        weights.experience_weight * experience +
        weights.location_weight * location +
        weights.education_weight * education
    )

    breakdown = ScoreBreakdown(
        skills_score=skills,
        career_score=career,
        experience_score=experience,
        location_score=location,
        education_score=education,
        raw_score=raw_score,
    )

    return raw_score, breakdown


def score_candidate(
    profile: CandidateProfile,
    weights: ScoringWeights = None,
) -> Tuple[float, ScoreBreakdown]:
    """Score a single candidate.

    Args:
        profile: CandidateProfile object.
        weights: Optional custom weights.

    Returns:
        Tuple of (final_score, ScoreBreakdown).
    """
    # Check for honeypot
    is_honeypot = check_honeypot(profile)

    # Extract features
    features = extract_features(profile)

    # Calculate raw score
    raw_score, breakdown = calculate_raw_score(features, weights)

    # Process behavioral signals
    behavioral = process_behavioral_signals(profile)

    # Apply behavioral modifier
    if is_honeypot:
        final_score = 0.0  # Honeypots get zero score
    else:
        final_score = raw_score * behavioral.composite_modifier

    breakdown.behavioral_modifier = behavioral.composite_modifier
    breakdown.final_score = final_score
    breakdown.is_honeypot = is_honeypot

    return final_score, breakdown


def score_candidates(
    profiles: List[CandidateProfile],
    weights: ScoringWeights = None,
) -> List[Tuple[str, float, ScoreBreakdown]]:
    """Score all candidates.

    Args:
        profiles: List of CandidateProfile objects.
        weights: Optional custom weights.

    Returns:
        List of (candidate_id, final_score, ScoreBreakdown) tuples,
        sorted by score descending.
    """
    results = []

    for profile in profiles:
        score, breakdown = score_candidate(profile, weights)
        results.append((profile.candidate_id, score, breakdown))

    # Sort by score descending, then by candidate_id ascending for ties
    results.sort(key=lambda x: (-x[1], x[0]))

    return results

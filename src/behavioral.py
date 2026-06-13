"""
Behavioral Signals Processor for Redrob AI Challenge.
Processes platform activity signals to calculate availability and engagement.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict

from .profile_parser import CandidateProfile, RedrobSignals


@dataclass
class BehavioralScores:
    """Processed behavioral signal scores."""
    availability_score: float = 0.0
    engagement_score: float = 0.0
    quality_score: float = 0.0
    composite_modifier: float = 0.0


def calculate_availability_score(signals: RedrobSignals) -> float:
    """Calculate candidate availability score (0-1).

    Components:
    - Open to work flag (0.3 weight)
    - Notice period (0.3 weight)
    - Last active date (0.4 weight)

    Args:
        signals: RedrobSignals object.

    Returns:
        Score between 0.0 and 1.0.
    """
    score = 0.0

    # Open to work flag
    if signals.open_to_work_flag:
        score += 0.3

    # Notice period
    if signals.notice_period_days <= 15:
        score += 0.3
    elif signals.notice_period_days <= 30:
        score += 0.25
    elif signals.notice_period_days <= 60:
        score += 0.15
    elif signals.notice_period_days <= 90:
        score += 0.05
    # 90+ days notice = 0

    # Last active date
    if signals.last_active_date:
        try:
            last_active = datetime.strptime(signals.last_active_date, "%Y-%m-%d").date()
            days_since_active = (date.today() - last_active).days

            if days_since_active <= 7:
                score += 0.4
            elif days_since_active <= 30:
                score += 0.35
            elif days_since_active <= 90:
                score += 0.25
            elif days_since_active <= 180:
                score += 0.1
            # 180+ days = 0
        except ValueError:
            # Invalid date format
            pass

    return min(score, 1.0)


def calculate_engagement_score(signals: RedrobSignals) -> float:
    """Calculate candidate engagement score (0-1).

    Components:
    - Recruiter response rate (0.4 weight)
    - Average response time (0.3 weight)
    - Interview completion rate (0.3 weight)

    Args:
        signals: RedrobSignals object.

    Returns:
        Score between 0.0 and 1.0.
    """
    score = 0.0

    # Recruiter response rate (direct weight)
    score += signals.recruiter_response_rate * 0.4

    # Average response time
    if signals.avg_response_time_hours <= 4:
        score += 0.3
    elif signals.avg_response_time_hours <= 24:
        score += 0.25
    elif signals.avg_response_time_hours <= 72:
        score += 0.15
    elif signals.avg_response_time_hours <= 168:  # 1 week
        score += 0.05
    # 1 week+ = 0

    # Interview completion rate (direct weight)
    score += signals.interview_completion_rate * 0.3

    return min(score, 1.0)


def calculate_quality_score(signals: RedrobSignals) -> float:
    """Calculate candidate quality score (0-1).

    Components:
    - Profile completeness (0.2 weight)
    - Skill assessment average (0.3 weight)
    - GitHub activity (0.2 weight)
    - Endorsements (0.15 weight)
    - Connections (0.15 weight)

    Args:
        signals: RedrobSignals object.

    Returns:
        Score between 0.0 and 1.0.
    """
    score = 0.0

    # Profile completeness (direct)
    score += (signals.profile_completeness_score / 100.0) * 0.2

    # Skill assessment average
    if signals.skill_assessment_scores:
        avg_assessment = sum(signals.skill_assessment_scores.values()) / len(
            signals.skill_assessment_scores
        )
        score += (avg_assessment / 100.0) * 0.3

    # GitHub activity (0-100, -1 if none)
    if signals.github_activity_score >= 0:
        score += (signals.github_activity_score / 100.0) * 0.2

    # Endorsements (normalize, cap at 100)
    endorsements_norm = min(signals.endorsements_received / 100.0, 1.0)
    score += endorsements_norm * 0.15

    # Connections (normalize, cap at 1000)
    connections_norm = min(signals.connection_count / 1000.0, 1.0)
    score += connections_norm * 0.15

    return min(score, 1.0)


def calculate_composite_modifier(
    availability: float,
    engagement: float,
    quality: float,
) -> float:
    """Calculate composite behavioral modifier (0-1).

    This modifier multiplies the skill/career score to down-weight
    unavailable or disengaged candidates.

    Args:
        availability: Availability score (0-1).
        engagement: Engagement score (0-1).
        quality: Quality score (0-1).

    Returns:
        Composite modifier between 0.3 and 1.0.
    """
    # Weighted average
    composite = (0.4 * availability) + (0.3 * engagement) + (0.3 * quality)

    # Apply floor to prevent complete elimination
    # Even inactive candidates get at least 0.3 modifier
    return max(composite, 0.3)


def process_behavioral_signals(profile: CandidateProfile) -> BehavioralScores:
    """Process all behavioral signals for a candidate.

    Args:
        profile: CandidateProfile object.

    Returns:
        BehavioralScores with all calculated scores.
    """
    signals = profile.redrob_signals

    availability = calculate_availability_score(signals)
    engagement = calculate_engagement_score(signals)
    quality = calculate_quality_score(signals)
    modifier = calculate_composite_modifier(availability, engagement, quality)

    return BehavioralScores(
        availability_score=availability,
        engagement_score=engagement,
        quality_score=quality,
        composite_modifier=modifier,
    )

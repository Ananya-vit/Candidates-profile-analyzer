"""
Candidate Profile Parser for Redrob AI Challenge.
Parses candidate JSON data into structured objects.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import json


@dataclass
class CareerEntry:
    """Single career history entry."""
    company: str
    title: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration_months: int
    is_current: bool
    industry: str
    company_size: str
    description: str

    @property
    def start_year(self) -> Optional[int]:
        if self.start_date:
            return datetime.strptime(self.start_date, "%Y-%m-%d").year
        return None

    @property
    def end_year(self) -> Optional[int]:
        if self.end_date:
            return datetime.strptime(self.end_date, "%Y-%m-%d").year
        return None


@dataclass
class Education:
    """Education entry."""
    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int
    grade: Optional[str] = None
    tier: str = "unknown"


@dataclass
class Skill:
    """Skill entry."""
    name: str
    proficiency: str
    endorsements: int
    duration_months: int = 0


@dataclass
class RedrobSignals:
    """Platform behavioral signals."""
    profile_completeness_score: float = 0.0
    signup_date: Optional[str] = None
    last_active_date: Optional[str] = None
    open_to_work_flag: bool = False
    profile_views_received_30d: int = 0
    applications_submitted_30d: int = 0
    recruiter_response_rate: float = 0.0
    avg_response_time_hours: float = 0.0
    skill_assessment_scores: Dict[str, float] = field(default_factory=dict)
    connection_count: int = 0
    endorsements_received: int = 0
    notice_period_days: int = 0
    expected_salary_range_inr_lpa: Dict[str, float] = field(default_factory=dict)
    preferred_work_mode: str = "flexible"
    willing_to_relocate: bool = False
    github_activity_score: float = -1.0
    search_appearance_30d: int = 0
    saved_by_recruiters_30d: int = 0
    interview_completion_rate: float = 0.0
    offer_acceptance_rate: float = -1.0
    verified_email: bool = False
    verified_phone: bool = False
    linkedin_connected: bool = False


@dataclass
class CandidateProfile:
    """Complete candidate profile."""
    candidate_id: str
    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float
    current_title: str
    current_company: str
    current_company_size: str
    current_industry: str
    career_history: List[CareerEntry] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    certifications: List[Dict[str, Any]] = field(default_factory=list)
    languages: List[Dict[str, str]] = field(default_factory=list)
    redrob_signals: RedrobSignals = field(default_factory=RedrobSignals)

    @property
    def skill_names(self) -> List[str]:
        """Get list of skill names."""
        return [s.name.lower() for s in self.skills]

    @property
    def all_text(self) -> str:
        """Get all text content for semantic analysis."""
        texts = [
            self.headline,
            self.summary,
            self.current_title,
            self.current_company,
        ]
        for entry in self.career_history:
            texts.append(entry.description)
            texts.append(entry.title)
        for skill in self.skills:
            texts.append(skill.name)
        for edu in self.education:
            texts.append(edu.field_of_study)
            texts.append(edu.degree)
        return " ".join(texts)


def parse_candidate(data: Dict[str, Any]) -> CandidateProfile:
    """Parse a candidate dictionary into a CandidateProfile object.

    Args:
        data: Dictionary containing candidate data.

    Returns:
        Parsed CandidateProfile object.
    """
    # Parse profile section
    profile = data.get("profile", {})

    # Parse career history
    career_history = []
    for entry in data.get("career_history", []):
        career_history.append(CareerEntry(
            company=entry.get("company", ""),
            title=entry.get("title", ""),
            start_date=entry.get("start_date"),
            end_date=entry.get("end_date"),
            duration_months=entry.get("duration_months", 0),
            is_current=entry.get("is_current", False),
            industry=entry.get("industry", ""),
            company_size=entry.get("company_size", ""),
            description=entry.get("description", ""),
        ))

    # Parse education
    education = []
    for entry in data.get("education", []):
        education.append(Education(
            institution=entry.get("institution", ""),
            degree=entry.get("degree", ""),
            field_of_study=entry.get("field_of_study", ""),
            start_year=entry.get("start_year", 0),
            end_year=entry.get("end_year", 0),
            grade=entry.get("grade"),
            tier=entry.get("tier", "unknown"),
        ))

    # Parse skills
    skills = []
    for entry in data.get("skills", []):
        skills.append(Skill(
            name=entry.get("name", ""),
            proficiency=entry.get("proficiency", "beginner"),
            endorsements=entry.get("endorsements", 0),
            duration_months=entry.get("duration_months", 0),
        ))

    # Parse redrob signals
    signals_data = data.get("redrob_signals", {})
    redrob_signals = RedrobSignals(
        profile_completeness_score=signals_data.get("profile_completeness_score", 0.0),
        signup_date=signals_data.get("signup_date"),
        last_active_date=signals_data.get("last_active_date"),
        open_to_work_flag=signals_data.get("open_to_work_flag", False),
        profile_views_received_30d=signals_data.get("profile_views_received_30d", 0),
        applications_submitted_30d=signals_data.get("applications_submitted_30d", 0),
        recruiter_response_rate=signals_data.get("recruiter_response_rate", 0.0),
        avg_response_time_hours=signals_data.get("avg_response_time_hours", 0.0),
        skill_assessment_scores=signals_data.get("skill_assessment_scores", {}),
        connection_count=signals_data.get("connection_count", 0),
        endorsements_received=signals_data.get("endorsements_received", 0),
        notice_period_days=signals_data.get("notice_period_days", 0),
        expected_salary_range_inr_lpa=signals_data.get("expected_salary_range_inr_lpa", {}),
        preferred_work_mode=signals_data.get("preferred_work_mode", "flexible"),
        willing_to_relocate=signals_data.get("willing_to_relocate", False),
        github_activity_score=signals_data.get("github_activity_score", -1.0),
        search_appearance_30d=signals_data.get("search_appearance_30d", 0),
        saved_by_recruiters_30d=signals_data.get("saved_by_recruiters_30d", 0),
        interview_completion_rate=signals_data.get("interview_completion_rate", 0.0),
        offer_acceptance_rate=signals_data.get("offer_acceptance_rate", -1.0),
        verified_email=signals_data.get("verified_email", False),
        verified_phone=signals_data.get("verified_phone", False),
        linkedin_connected=signals_data.get("linkedin_connected", False),
    )

    return CandidateProfile(
        candidate_id=data.get("candidate_id", ""),
        anonymized_name=profile.get("anonymized_name", ""),
        headline=profile.get("headline", ""),
        summary=profile.get("summary", ""),
        location=profile.get("location", ""),
        country=profile.get("country", ""),
        years_of_experience=profile.get("years_of_experience", 0.0),
        current_title=profile.get("current_title", ""),
        current_company=profile.get("current_company", ""),
        current_company_size=profile.get("current_company_size", ""),
        current_industry=profile.get("current_industry", ""),
        career_history=career_history,
        education=education,
        skills=skills,
        certifications=data.get("certifications", []),
        languages=data.get("languages", []),
        redrob_signals=redrob_signals,
    )


def parse_candidates_file(filepath: str) -> List[CandidateProfile]:
    """Parse a JSON or JSONL file containing candidates.

    Args:
        filepath: Path to the candidates JSON/JSONL file.

    Returns:
        List of parsed CandidateProfile objects.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Try JSON array first
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return [parse_candidate(candidate) for candidate in data]
        else:
            return [parse_candidate(data)]
    except json.JSONDecodeError:
        pass

    # Try JSONL format (one JSON object per line)
    candidates = []
    for line_num, line in enumerate(content.split("\n"), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            candidates.append(parse_candidate(obj))
        except json.JSONDecodeError as e:
            print(f"Warning: Skipping invalid JSON on line {line_num}: {e}")

    return candidates

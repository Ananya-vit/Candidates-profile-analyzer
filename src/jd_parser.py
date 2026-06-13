"""
Job Description Parser for Redrob AI Challenge.
Extracts structured requirements from the Senior AI Engineer JD.
"""

from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class JobRequirements:
    """Structured job requirements extracted from JD."""

    # Title and company
    title: str = "Senior AI Engineer"
    company: str = "Redrob AI"

    # Experience requirements
    min_years: float = 5.0
    max_years: float = 9.0

    # Hard requirements (must-have skills/qualifications)
    hard_requirements: Set[str] = field(default_factory=lambda: {
        "embeddings",
        "vector search",
        "retrieval",
        "vector databases",
        "hybrid search",
        "python",
        "evaluation frameworks",
        "ndcg",
        "mrr",
        "map",
        "production ml",
        "production ai",
        "machine learning",
        "deep learning",
    })

    # Soft requirements (nice-to-have)
    soft_requirements: Set[str] = field(default_factory=lambda: {
        "llm fine-tuning",
        "lora",
        "qlora",
        "peft",
        "learning-to-rank",
        "hr-tech",
        "recruiting",
        "distributed systems",
        "inference optimization",
        "open source",
        "rust",
        "go",
        "cuda",
    })

    # Disqualifying patterns
    disqualifiers: Set[str] = field(default_factory=lambda: {
        "pure research",
        "academic lab",
        "langchain only",
        "no production code",
        "job hopping",
        "title chasing",
        "framework enthusiast",
        "consulting only",
        "tcs",
        "infosys",
        "wipro",
        "accenture",
        "cognizant",
        "capgemini",
        "computer vision only",
        "speech only",
        "robotics only",
        "closed source only",
    })

    # Preferred locations
    preferred_locations: Set[str] = field(default_factory=lambda: {
        "pune",
        "noida",
        "delhi",
        "ncr",
        "hyderabad",
        "mumbai",
        "bangalore",
        "bengaluru",
    })

    # Negative signals (things to avoid)
    negative_signals: Set[str] = field(default_factory=lambda: {
        "marketing manager",
        "sales",
        "business development",
        "account manager",
        "project manager",
        "non-technical",
    })

    # Positive signals (things to look for)
    positive_signals: Set[str] = field(default_factory=lambda: {
        "ml engineer",
        "ai engineer",
        "data scientist",
        "research engineer",
        "software engineer",
        "backend engineer",
        "platform engineer",
        "infrastructure engineer",
    })

    # Industry preferences
    preferred_industries: Set[str] = field(default_factory=lambda: {
        "technology",
        "ai",
        "machine learning",
        "software",
        "saas",
        "platform",
        "product",
    })

    # Disfavored industries
    disfavored_industries: Set[str] = field(default_factory=lambda: {
        "consulting",
        "it services",
        "outsourcing",
    })


def get_job_requirements() -> JobRequirements:
    """Return the parsed job requirements for the Senior AI Engineer role."""
    return JobRequirements()


def calculate_title_relevance(title: str) -> float:
    """Calculate how relevant a candidate's title is to the target role.

    Args:
        title: The candidate's current or recent job title.

    Returns:
        Score between -1.0 and 1.0 indicating title relevance.
    """
    title_lower = title.lower()

    # Strong positive signals
    if any(term in title_lower for term in ["ml engineer", "ai engineer", "machine learning engineer"]):
        return 1.0
    if any(term in title_lower for term in ["data scientist", "research engineer", "research scientist"]):
        return 0.8
    if any(term in title_lower for term in ["software engineer", "backend engineer", "platform engineer"]):
        return 0.6
    if any(term in title_lower for term in ["data engineer", "infrastructure engineer"]):
        return 0.5
    if any(term in title_lower for term in ["developer", "engineer"]):
        return 0.4

    # Management/leadership (still technical)
    if any(term in title_lower for term in ["tech lead", "engineering manager", "staff engineer", "principal engineer"]):
        return 0.5

    # Negative signals
    if any(term in title_lower for term in ["marketing", "sales", "business development"]):
        return -0.8
    if any(term in title_lower for term in ["account manager", "project manager", "program manager"]):
        return -0.6
    if any(term in title_lower for term in ["consultant", "analyst"]):
        return -0.4

    # Neutral/unknown
    return 0.0


def calculate_company_type_score(company: str, industry: str, company_size: str) -> float:
    """Calculate score based on company type and industry.

    Args:
        company: Company name.
        industry: Company industry.
        company_size: Company size category.

    Returns:
        Score between -1.0 and 1.0.
    """
    company_lower = company.lower()
    industry_lower = industry.lower()

    # Disfavored consulting firms
    consulting_firms = ["tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
                        "deloitte", "pwc", "ey", "kpmg", "mckinsey", "bain", "bcg"]
    if any(firm in company_lower for firm in consulting_firms):
        return -0.5

    # Product companies (positive)
    product_indicators = ["ai", "ml", "software", "saas", "platform", "technology", "tech"]
    if any(ind in industry_lower for ind in product_indicators):
        return 0.8

    # Startups (positive for this role)
    if company_size in ["1-10", "11-50", "51-200", "201-500"]:
        return 0.6

    # Large tech companies
    if company_size in ["1001-5000", "5001-10000", "10001+"]:
        return 0.4

    # IT services (negative)
    if "it services" in industry_lower or "outsourcing" in industry_lower:
        return -0.3

    # Default neutral
    return 0.0

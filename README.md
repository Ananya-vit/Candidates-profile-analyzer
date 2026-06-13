# Redrob AI Challenge - Candidate Ranking System

## Overview

This system ranks candidates for the "Senior AI Engineer — Founding Team" role at Redrob AI. It goes beyond keyword matching to understand genuine fit through semantic analysis of career history, skills, behavioral signals, and platform activity.

## Architecture

### Core Components

1. **JD Parser** (`src/jd_parser.py`) - Extracts structured requirements from the job description
2. **Profile Parser** (`src/profile_parser.py`) - Parses candidate JSON data into structured objects
3. **Feature Extractor** (`src/feature_extractor.py`) - Extracts numerical features from profiles
4. **Behavioral Processor** (`src/behavioral.py`) - Processes platform activity signals
5. **Scoring Engine** (`src/scoring.py`) - Combines all features into final scores
6. **Reasoning Generator** (`src/reasoning.py`) - Generates human-readable reasoning

### Scoring Algorithm

The system uses a weighted scoring approach:

- **Skills Match (35%)** - AI/ML skills, proficiency, production experience
- **Career Trajectory (30%)** - Title relevance, company type, tenure patterns
- **Experience Level (20%)** - Years in range, recent coding activity
- **Location Fit (10%)** - Geographic match to Pune/Noida preferences
- **Education (5%)** - Institution tier, relevant field

All scores are multiplied by a **behavioral modifier** (0.3-1.0) based on:
- Availability (open to work, notice period, last active)
- Engagement (response rate, interview completion)
- Quality (profile completeness, GitHub activity)

### Key Features

- **Honeypot Detection** - Identifies and down-ranks fake/suspicious profiles
- **Semantic Skill Matching** - Matches skills to JD requirements beyond exact keywords
- **Behavioral Signal Integration** - Availability and engagement as score multipliers
- **Detailed Reasoning** - Human-readable explanations for each ranking

## Usage

### Prerequisites

```bash
pip install -r requirements.txt
```

### Running the Ranker

```bash
python rank.py --candidates ./candidates.json --out ./submission.csv --validate
```

### Arguments

- `--candidates` (required): Path to candidates JSON file
- `--out` (required): Path to output CSV file
- `--top` (optional): Number of top candidates to rank (default: 100)
- `--validate` (optional): Validate output format after writing

## Output Format

The output CSV has the following format:

```
candidate_id,rank,score,reasoning
CAND_0000031,1,0.5594,"Strong fit – ML Engineer with 6 yrs; 18 AI skills; production experience"
CAND_0000001,2,0.3702,"Good fit – Backend Engineer; 6.9 yrs; strong AI background"
...
```

## Design Decisions

### Why This Approach?

1. **Ship over Research** - Prioritizes production experience at product companies
2. **Systems over Frameworks** - Values distributed systems thinking over framework usage
3. **Product over Services** - Strong preference for product company backgrounds
4. **Engagement Matters** - Behavioral signals are critical multipliers
5. **Honeypots Exist** - Built to catch keyword-only matchers

### Scoring Rationale

- **Skills (35%)** - Core requirement for the role
- **Career (30%)** - Title and company type indicate fit
- **Experience (20%)** - Must be in the 5-9 year range
- **Location (10%)** - Pune/Noida preferred but flexible
- **Education (5%)** - Less important than experience

### Behavioral Modifier

The behavioral modifier (0.3-1.0) ensures:
- Active, available candidates rank higher
- Disengaged candidates are down-weighted (not eliminated)
- Perfect-on-paper but inactive candidates don't top the list

## Performance

- **Runtime**: < 1 second for 50 candidates on CPU
- **Memory**: < 100MB for 1000 candidates
- **No external API calls** - Fully local execution

## File Structure

```
redrob-challenge/
├── README.md
├── requirements.txt
├── rank.py                    # Main entry point
├── submission_metadata.yaml   # Submission metadata
├── src/
│   ├── __init__.py
│   ├── jd_parser.py          # Job description parsing
│   ├── profile_parser.py     # Candidate profile processing
│   ├── feature_extractor.py  # Feature extraction
│   ├── scoring.py            # Scoring algorithms
│   ├── behavioral.py         # Behavioral signal processing
│   └── reasoning.py          # Reasoning generation
├── data/
│   └── skill_taxonomy.json   # Skill mapping (optional)
├── tests/
│   └── test_scoring.py       # Unit tests
└── output/
    └── submission.csv        # Generated output
```

## Testing

```bash
python -m pytest tests/
```

## Validation

The submission can be validated using the provided validator:

```bash
python validate_submission.py output/submission.csv
```

## License

Internal use only - Redrob AI Challenge

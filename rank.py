#!/usr/bin/env python3
"""
Redrob AI Challenge - Candidate Ranking System

Ranks candidates for the Senior AI Engineer role based on:
- Skills matching (semantic analysis)
- Career trajectory (title, company, tenure)
- Experience level (years, recent activity)
- Location fit
- Education
- Behavioral signals (availability, engagement)

Usage:
    python rank.py --candidates ./candidates.json --out ./submission.csv
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import List, Tuple

from src.profile_parser import parse_candidates_file, CandidateProfile
from src.scoring import score_candidates, ScoreBreakdown
from src.reasoning import generate_reasoning_batch
from src.feature_extractor import extract_features
from src.behavioral import process_behavioral_signals


def load_candidates(filepath: str) -> List[CandidateProfile]:
    """Load candidates from JSON file.

    Args:
        filepath: Path to candidates JSON file.

    Returns:
        List of CandidateProfile objects.
    """
    print(f"Loading candidates from {filepath}...")
    profiles = parse_candidates_file(filepath)
    print(f"Loaded {len(profiles)} candidates.")
    return profiles


def rank_candidates(
    profiles: List[CandidateProfile],
    top_n: int = 100,
) -> List[Tuple[str, float, str]]:
    """Rank candidates and generate reasoning.

    Args:
        profiles: List of CandidateProfile objects.
        top_n: Number of top candidates to return.

    Returns:
        List of (candidate_id, score, reasoning) tuples.
    """
    print("Scoring candidates...")
    start_time = time.time()

    # Score all candidates
    scored = score_candidates(profiles)

    # Take top N
    top_scored = scored[:top_n]

    # Prepare for reasoning generation
    candidates_for_reasoning = [
        (cid, score, breakdown, rank + 1)
        for rank, (cid, score, breakdown) in enumerate(top_scored)
    ]

    print("Generating reasoning...")
    reasoning_list = generate_reasoning_batch(profiles, candidates_for_reasoning)

    # Combine results
    results = []
    for (candidate_id, score, breakdown, rank), reasoning in zip(
        candidates_for_reasoning, reasoning_list
    ):
        results.append((candidate_id, score, reasoning))

    elapsed = time.time() - start_time
    print(f"Ranking completed in {elapsed:.2f} seconds.")

    return results


def write_submission(
    results: List[Tuple[str, float, str]],
    output_path: str,
) -> None:
    """Write results to submission CSV.

    Args:
        results: List of (candidate_id, score, reasoning) tuples.
        output_path: Path to output CSV file.
    """
    print(f"Writing submission to {output_path}...")

    # Re-sort by rounded score descending, then candidate_id ascending for ties
    results_sorted = sorted(results, key=lambda x: (-round(x[1], 4), x[0]))

    # Ensure output directory exists
    out_path = Path(output_path)
    out_dir = out_path.parent
    if str(out_dir) and not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        # Data rows
        for rank, (candidate_id, score, reasoning) in enumerate(results_sorted, 1):
            # Ensure score is formatted properly
            score_str = f"{score:.4f}"
            writer.writerow([candidate_id, rank, score_str, reasoning])

    print(f"Submission written with {len(results_sorted)} candidates.")


def validate_submission(filepath: str, expected_count: int = 100) -> List[str]:
    """Validate submission format.

    Args:
        filepath: Path to submission CSV.
        expected_count: Expected number of data rows in the submission.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    path = Path(filepath)

    if path.suffix.lower() != ".csv":
        errors.append("Filename must use .csv extension.")

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)

            try:
                header = next(reader)
            except StopIteration:
                errors.append("File is empty.")
                return errors

            required_header = ["candidate_id", "rank", "score", "reasoning"]
            if header != required_header:
                errors.append(f"Invalid header. Expected: {required_header}")

            rows = list(reader)
            non_empty_rows = [r for r in rows if any(cell.strip() for cell in r)]

            if len(non_empty_rows) != expected_count:
                errors.append(
                    f"Expected {expected_count} data rows, got {len(non_empty_rows)}."
                )

            seen_ids = set()
            seen_ranks = set()
            prev_score = None

            for i, row in enumerate(non_empty_rows):
                row_num = i + 2

                if len(row) != 4:
                    errors.append(f"Row {row_num}: Expected 4 columns, got {len(row)}.")
                    continue

                candidate_id, rank_str, score_str, reasoning = row

                # Validate candidate_id
                if candidate_id in seen_ids:
                    errors.append(f"Row {row_num}: Duplicate candidate_id {candidate_id}.")
                seen_ids.add(candidate_id)

                # Validate rank
                try:
                    rank = int(rank_str)
                    if rank < 1 or rank > expected_count:
                        errors.append(
                            f"Row {row_num}: Rank {rank} out of range 1-{expected_count}."
                        )
                    if rank in seen_ranks:
                        errors.append(f"Row {row_num}: Duplicate rank {rank}.")
                    seen_ranks.add(rank)
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid rank '{rank_str}'.")

                # Validate score
                try:
                    score = float(score_str)
                    if prev_score is not None and score > prev_score:
                        errors.append(
                            f"Row {row_num}: Score {score} > previous score {prev_score}."
                        )
                    prev_score = score
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid score '{score_str}'.")

    except Exception as e:
        errors.append(f"Error reading file: {e}")

    return errors


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Redrob AI Challenge - Candidate Ranking System"
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to candidates JSON file",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Path to output CSV file",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=100,
        help="Number of top candidates to rank (default: 100)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output after writing",
    )

    args = parser.parse_args()

    # Load candidates
    profiles = load_candidates(args.candidates)

    # Rank candidates
    results = rank_candidates(profiles, args.top)

    # Write submission
    write_submission(results, args.out)

    # Validate if requested
    if args.validate:
        print("\nValidating submission...")
        errors = validate_submission(args.out, expected_count=len(results))
        if errors:
            print(f"Validation failed with {len(errors)} errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("Validation passed!")

    print("\nDone!")


if __name__ == "__main__":
    main()

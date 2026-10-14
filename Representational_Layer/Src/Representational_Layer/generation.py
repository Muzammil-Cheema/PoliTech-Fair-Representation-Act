from __future__ import annotations

from math import exp
from random import Random

from .models import Ballot, Candidate, RankGroup, RankingMethod
from .scoring import CandidateScores


def generate_deterministic_ballot_ranking(
    candidates: list[Candidate],
    candidate_scores: dict[str, float],
) -> list[RankGroup]:
    """Generate a full deterministic ranking sorted by score (descending).

    Ties are currently broken by preserving the original list order, although
    real tie-breaking policies might be expanded in the future.
    """
    scored = [
        (candidate_scores.get(candidate.candidate_id, 0.0), i, candidate)
        for i, candidate in enumerate(candidates)
    ]
    # Sort by score descending, then by original index ascending to preserve order for ties
    scored.sort(key=lambda x: (-x[0], x[1]))

    return [
        RankGroup(rank=rank, candidate_ids=[candidate.candidate_id])
        for rank, (_, _, candidate) in enumerate(scored, start=1)
    ]


def generate_weighted_ballot_ranking(
    candidates: list[Candidate],
    candidate_probabilities: dict[str, float],
    rng: Random,
) -> list[RankGroup]:
    """Generate a full ranking by sampling candidates without replacement.

    Higher candidate probabilities make that candidate more likely to appear
    earlier in the ranking. Each selected candidate receives its own rank.
    """
    remaining_candidates = list(candidates)
    rankings: list[RankGroup] = []
    next_rank = 1

    while remaining_candidates:
        weights = [max(candidate_probabilities.get(candidate.candidate_id, 0.0), 0.0) for candidate in remaining_candidates]

        if sum(weights) == 0:
            selected_candidate = remaining_candidates[rng.randrange(len(remaining_candidates))]
        else:
            selected_candidate = rng.choices(remaining_candidates, weights=weights, k=1)[0]

        rankings.append(
            RankGroup(rank=next_rank, candidate_ids=[selected_candidate.candidate_id])
        )
        remaining_candidates = [
            candidate
            for candidate in remaining_candidates
            if candidate.candidate_id != selected_candidate.candidate_id
        ]
        next_rank += 1

    return rankings


def _scores_to_probabilities(
    scores: dict[str, float],
    ranking_method: RankingMethod,
    temperature: float,
) -> dict[str, float]:
    if ranking_method == "softmax_without_replacement":
        scale = temperature if temperature > 0 else 1.0
        return {
            candidate_id: exp(score / scale)
            for candidate_id, score in scores.items()
        }

    minimum_score = min(scores.values()) if scores else 0.0
    offset = abs(minimum_score) + 1.0
    return {
        candidate_id: score + offset
        for candidate_id, score in scores.items()
    }


def generate_ballot(
    ballot_id: str,
    generation_run_id: str,
    source_elector_unit_id: str,
    candidates: list[Candidate],
    candidate_probabilities: dict[str, float],
    rng: Random,
) -> Ballot:
    """Generate a ballot with a complete ranking for the provided candidates."""
    return Ballot(
        ballot_id=ballot_id,
        generation_run_id=generation_run_id,
        source_elector_unit_id=source_elector_unit_id,
        rankings=generate_weighted_ballot_ranking(
            candidates=candidates,
            candidate_probabilities=candidate_probabilities,
            rng=rng,
        ),
    )


def generate_ballots_from_scores(
    generation_run_id: str,
    source_elector_unit_id: str,
    candidates: list[Candidate],
    candidate_scores: CandidateScores,
    ranking_method: RankingMethod,
    temperature: float,
    count: int,
    rng: Random,
) -> list[Ballot]:
    """Generate a batch of ballots for an elector unit using the configured ranking method."""
    if count <= 0:
        return []

    # Extract just the final scores from CandidateScores dict
    scores = {
        candidate_id: float(entry["final_score"])
        for candidate_id, entry in candidate_scores.items()
    }

    if ranking_method == "deterministic_sort":
        ranking = generate_deterministic_ballot_ranking(candidates, scores)
        # For deterministic, all ballots are identical
        return [
            Ballot(
                ballot_id=f"{generation_run_id}-{source_elector_unit_id}-{i:04d}",
                generation_run_id=generation_run_id,
                source_elector_unit_id=source_elector_unit_id,
                rankings=ranking,
            )
            for i in range(1, count + 1)
        ]

    probabilities = _scores_to_probabilities(scores, ranking_method, temperature)
    ballots = []
    for i in range(1, count + 1):
        ballot = Ballot(
            ballot_id=f"{generation_run_id}-{source_elector_unit_id}-{i:04d}",
            generation_run_id=generation_run_id,
            source_elector_unit_id=source_elector_unit_id,
            rankings=generate_weighted_ballot_ranking(candidates, probabilities, rng),
        )
        ballots.append(ballot)
        
    return ballots

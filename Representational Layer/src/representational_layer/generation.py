from __future__ import annotations

from random import Random

from .models import Ballot, Candidate, RankGroup


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

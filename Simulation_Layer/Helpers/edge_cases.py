from __future__ import annotations

from typing import Optional

from Simulation_Layer.Core.models import Ballot, Ranking


def is_undervote(ballot: Ballot) -> bool:
    """Return whether a ballot is an undervote (contains no rankings).

    Args:
        ballot: Ballot to evaluate.

    Returns:
        True when the ballot has no rankings, else False.
    """
    return len(ballot.rankings) == 0


def sorted_rankings(ballot: Ballot) -> list[Ranking]:
    """Return ballot rankings ordered by ascending rank number.

    Args:
        ballot: Ballot containing rank groups.

    Returns:
        A new list of ranking groups sorted by `rank`.
    """
    return sorted(ballot.rankings, key=lambda r: r.rank)


def highest_ranked_active(
    ballot: Ballot,
    active_candidate_ids: set[str],
) -> Optional[str]:
    """Resolve a ballot to its highest-ranked unambiguous active candidate.

    Edge-case behavior:
    - Undervotes: no rankings, so no allocation.
    - Skipped ranks: ignored until an active candidate appears.
    - Repeated candidates: first usable active placement wins.
    - Same-rank multi-active ambiguity: no allocation for that round.

    Args:
        ballot: Ballot to resolve.
        active_candidate_ids: Candidate IDs currently active in the round.

    Returns:
        Candidate ID when an unambiguous active choice is found, otherwise None.
    """
    if is_undervote(ballot):
        return None

    for ranking in sorted_rankings(ballot):
        active_in_rank = [cid for cid in ranking.candidate_ids if cid in active_candidate_ids]

        if not active_in_rank:
            continue

        if len(active_in_rank) == 1:
            return active_in_rank[0]

        return None

    return None

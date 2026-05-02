from __future__ import annotations

from typing import Optional

from Core.models import Ballot, Ranking


def is_undervote(ballot: Ballot) -> bool:
    return len(ballot.rankings) == 0


def sorted_rankings(ballot: Ballot) -> list[Ranking]:
    return sorted(ballot.rankings, key=lambda r: r.rank)


def highest_ranked_active(
    ballot: Ballot,
    active_candidate_ids: set[str],
) -> Optional[str]:
    """
    Handles ranking edge cases:

    - Undervotes: no rankings -> ballot never counts.
    - Skipped rankings: allowed; continue to next rank with any active candidate.
    - Repeated rankings: earliest usable active ranking wins.
    - Same-rank groups: if first reachable active rank has multiple active
      candidates, ballot becomes inactive.
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

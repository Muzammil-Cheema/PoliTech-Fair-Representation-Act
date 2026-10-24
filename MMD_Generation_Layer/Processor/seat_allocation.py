"""Interim vote-share proxy for splitting district seats between Democrats and Republicans.

The source data has only single-choice Democratic and Republican precinct totals, not ranked
ballots, so it cannot support FRA ranked-choice tabulation. This proxy splits each district's
seats in proportion to its major-party vote share instead:

- ``dem_seats = round(available_seats * votes_dem / (votes_dem + votes_rep))``
- ``rep_seats = available_seats - dem_seats``

Rounding policy: the share is computed with exact fractions, and an exact half seat rounds to
the even Democratic seat count (Python's ``round``), so ``1.5 -> 2`` and ``2.5 -> 2``. Exact
halves are rare and this rule does not consistently favor either party.

Zero-vote policy: a district with no major-party votes is treated as an even ``1/2`` split and
then follows the same half-seat rule, so it is not handed wholesale to either party.

The proxy does not model ballot rankings, transfers, candidates, or FRA counting.
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping
from fractions import Fraction
from typing import NamedTuple

SEAT_ALLOCATION_METHOD = "vote_share_proxy"
SEAT_ALLOCATION_LABEL = "Vote-share proxy (not FRA ranked-choice tabulation)"


class ProxySeatAllocation(NamedTuple):
    """Seats a district's major-party vote share assigns to each party under the proxy."""

    dem_seats: int
    rep_seats: int
    dem_vote_share: float


def democratic_vote_share(votes_dem: int, votes_rep: int) -> Fraction:
    """Return the exact Democratic share of major-party votes; ``1/2`` when both are zero."""
    if votes_dem < 0 or votes_rep < 0:
        raise ValueError(f"Vote totals must be non-negative, got dem={votes_dem}, rep={votes_rep}")

    total_votes = votes_dem + votes_rep
    if total_votes == 0:
        return Fraction(1, 2)
    return Fraction(int(votes_dem), int(total_votes))


def allocate_proxy_seats(available_seats: int, votes_dem: int, votes_rep: int) -> ProxySeatAllocation:
    """Split ``available_seats`` between the parties by Democratic vote share.

    Exact half seats round to the even Democratic count, and zero-vote districts are treated as
    an even split (see the module docstring). ``dem_seats + rep_seats`` always equals
    ``available_seats``.

    Raises:
        ValueError: If ``available_seats`` is below 1 or either vote total is negative.
    """
    if available_seats < 1:
        raise ValueError(f"available_seats must be at least 1, got {available_seats}")

    dem_vote_share = democratic_vote_share(votes_dem, votes_rep)
    dem_seats = round(available_seats * dem_vote_share)
    return ProxySeatAllocation(dem_seats, available_seats - dem_seats, float(dem_vote_share))


def aggregate_district_votes(
    assignment: Mapping[Hashable, Hashable],
    votes_dem: Mapping[Hashable, int],
    votes_rep: Mapping[Hashable, int],
) -> dict[Hashable, tuple[int, int]]:
    """Sum precinct Democratic and Republican votes into ``{district_id: (votes_dem, votes_rep)}``."""
    totals: dict[Hashable, list[int]] = {}
    for precinct_id, district_id in assignment.items():
        district_totals = totals.setdefault(district_id, [0, 0])
        district_totals[0] += int(votes_dem[precinct_id])
        district_totals[1] += int(votes_rep[precinct_id])
    return {district_id: (dem, rep) for district_id, (dem, rep) in totals.items()}

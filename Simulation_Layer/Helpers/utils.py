from __future__ import annotations

import math
from typing import Dict, Optional

from Core.models import Election
from Global_Utilities.logger import error
from Helpers.edge_cases import highest_ranked_active, is_undervote


def initial_candidate_status(election: Election) -> Dict[str, str]:
    status: Dict[str, str] = {}
    for candidate in election.candidates:
        status[candidate.candidate_id] = "withdrawn" if candidate.withdrawn else "active"
    return status


def active_candidates(status: Dict[str, str]) -> list[str]:
    return [cid for cid, candidate_status in status.items() if candidate_status == "active"]


def elected_candidates(status: Dict[str, str]) -> list[str]:
    return [cid for cid, candidate_status in status.items() if candidate_status == "elected"]


def tie_break(tied_ids: list[str], tie_break_order: list[str]) -> str:
    if not tied_ids:
        error("Cannot tie-break an empty candidate list")

    order_index = {cid: i for i, cid in enumerate(tie_break_order)}
    missing_ids = [candidate_id for candidate_id in tied_ids if candidate_id not in order_index]
    if missing_ids:
        error(f"Cannot tie-break candidates missing from tie_break_order: {missing_ids}")

    return min(tied_ids, key=lambda cid: order_index[cid])


def add_winner(status: Dict[str, str], candidate_id: str) -> None:
    if candidate_id not in status:
        error(f"Cannot elect unknown candidate '{candidate_id}'")
    status[candidate_id] = "elected"


def eliminate_candidate(status: Dict[str, str], candidate_id: str) -> None:
    if candidate_id not in status:
        error(f"Cannot eliminate unknown candidate '{candidate_id}'")
    status[candidate_id] = "eliminated"


def compute_threshold(first_round_total: float, seat_count: int) -> float:
    if seat_count < 1:
        error("Cannot compute threshold with seat_count less than 1")
    return math.floor(first_round_total / (seat_count + 1)) + 1


def truncate_4(value: float) -> float:
    return math.floor(value * 10_000) / 10_000.0


def append_round(
    rounds: list[Dict],
    election: Election,
    status: Dict[str, str],
    totals: Dict[str, float],
    action: Optional[Dict],
    include_threshold: bool,
    ballot_allocations: Optional[Dict[str, Optional[str]]] = None,
) -> None:
    round_entry = {
        "round": election.round_number,
        "vote_totals": totals.copy(),
        "status": status.copy(),
        "action": action,
    }
    if ballot_allocations is not None:
        round_entry["ballot_allocations"] = ballot_allocations.copy()
    if include_threshold:
        round_entry["threshold"] = election.threshold
    rounds.append(round_entry)


def count_votes_single_round(
    election: Election,
    status: Dict[str, str],
    use_transfer_values: bool,
) -> tuple[Dict[str, float], Dict[str, Optional[str]]]:
    active_set = set(active_candidates(status))
    totals: Dict[str, float] = {cid: 0.0 for cid in status.keys()}
    ballot_allocations: Dict[str, Optional[str]] = {}

    for ballot in election.ballots:
        if is_undervote(ballot):
            ballot_allocations[ballot.ballot_id] = None
            continue
        candidate_id = highest_ranked_active(ballot, active_set)
        ballot_allocations[ballot.ballot_id] = candidate_id
        if candidate_id is None:
            continue
        value = ballot.current_transfer_value if use_transfer_values else 1.0
        totals[candidate_id] += value

    return totals, ballot_allocations


def apply_threshold_to_elected(
    totals: Dict[str, float],
    status: Dict[str, str],
    threshold: Optional[float],
) -> None:
    if threshold is None:
        return
    for candidate_id, candidate_status in status.items():
        if candidate_status == "elected":
            totals[candidate_id] = threshold


def build_surplus_fractions(
    elected_candidate_ids: list[str],
    totals: Dict[str, float],
    threshold: Optional[float],
) -> tuple[Dict[str, float], list[Dict[str, float | str]]]:
    if threshold is None:
        error("Cannot compute surplus fractions without threshold")

    surplus_fractions: Dict[str, float] = {}
    action_detail: list[Dict[str, float | str]] = []
    for candidate_id in elected_candidate_ids:
        vote_total = totals.get(candidate_id, 0.0)
        if vote_total <= 0:
            surplus_fraction = 0.0
        else:
            surplus_fraction = truncate_4((vote_total - threshold) / vote_total)
            if surplus_fraction < 0:
                surplus_fraction = 0.0

        surplus_fractions[candidate_id] = surplus_fraction
        action_detail.append(
            {"candidate": candidate_id, "surplus_fraction": surplus_fraction}
        )

    return surplus_fractions, action_detail


def apply_simultaneous_surplus_transfer_values(
    election: Election,
    round_ballot_allocations: Dict[str, Optional[str]],
    surplus_fractions: Dict[str, float],
) -> None:
    # Compute all updated transfer values from a stable round snapshot and then
    # apply them together, so simultaneous surpluses cannot observe one another's
    # in-pass mutations.
    updates_by_ballot_id: Dict[str, float] = {}

    for ballot in election.ballots:
        allocated_candidate_id = round_ballot_allocations.get(ballot.ballot_id)
        if allocated_candidate_id is None:
            continue

        if allocated_candidate_id not in surplus_fractions:
            continue

        surplus_fraction = surplus_fractions[allocated_candidate_id]
        updates_by_ballot_id[ballot.ballot_id] = truncate_4(
            ballot.current_transfer_value * surplus_fraction
        )

    if not updates_by_ballot_id:
        return

    for ballot in election.ballots:
        updated_transfer_value = updates_by_ballot_id.get(ballot.ballot_id)
        if updated_transfer_value is None:
            continue
        ballot.current_transfer_value = updated_transfer_value

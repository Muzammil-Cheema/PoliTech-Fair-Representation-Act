from __future__ import annotations

import math
from typing import Dict, Optional

from core.models import Election
from global_utilities.logger import error
from helpers.edge_cases import highest_ranked_active, is_undervote


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
) -> None:
    round_entry = {
        "round": election.round_number,
        "vote_totals": totals.copy(),
        "status": status.copy(),
        "action": action,
    }
    if include_threshold:
        round_entry["threshold"] = election.threshold
    rounds.append(round_entry)


def count_votes_single_round(
    election: Election,
    status: Dict[str, str],
    use_transfer_values: bool,
) -> Dict[str, float]:
    active_set = set(active_candidates(status))
    totals: Dict[str, float] = {cid: 0.0 for cid in status.keys()}

    for ballot in election.ballots:
        if is_undervote(ballot):
            continue
        candidate_id = highest_ranked_active(ballot, active_set)
        if candidate_id is None:
            continue
        value = ballot.current_transfer_value if use_transfer_values else 1.0
        totals[candidate_id] += value

    return totals


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


def distribute_surplus_transfer_values(
    election: Election,
    elected_candidate_id: str,
    surplus_fraction: float,
) -> None:
    active_set_for_this = {elected_candidate_id}
    for ballot in election.ballots:
        current_candidate_id = highest_ranked_active(ballot, active_set_for_this)
        if current_candidate_id != elected_candidate_id:
            continue
        ballot.current_transfer_value = truncate_4(
            ballot.current_transfer_value * surplus_fraction
        )

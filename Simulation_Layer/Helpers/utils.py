from __future__ import annotations

import math
from typing import Dict, Optional

from Simulation_Layer.Core.models import Ballot, Candidate
from Global_Utilities.logger import error
from Simulation_Layer.Helpers.edge_cases import highest_ranked_active, is_undervote


def initial_candidate_status(candidates: list[Candidate]) -> Dict[str, str]:
    """Build initial status map for all candidates.

    Args:
        candidates: Candidates participating in the election.

    Returns:
        Mapping of candidate ID -> `"active"` or `"withdrawn"`.
    """
    status: Dict[str, str] = {}
    for candidate in candidates:
        status[candidate.candidate_id] = "withdrawn" if candidate.withdrawn else "active"
    return status


def active_candidates(status: Dict[str, str]) -> list[str]:
    """Return candidate IDs currently marked active.

    Args:
        status: Candidate status mapping.

    Returns:
        Active candidate IDs in insertion order.
    """
    return [cid for cid, candidate_status in status.items() if candidate_status == "active"]


def elected_candidates(status: Dict[str, str]) -> list[str]:
    """Return candidate IDs currently marked elected.

    Args:
        status: Candidate status mapping.

    Returns:
        Elected candidate IDs in insertion order.
    """
    return [cid for cid, candidate_status in status.items() if candidate_status == "elected"]


def tie_break(tied_ids: list[str], tie_break_order: list[str]) -> str:
    """Resolve a tie deterministically using the configured tie-break order.

    Args:
        tied_ids: Candidate IDs tied on the relevant metric.
        tie_break_order: Full deterministic tie-break sequence.

    Returns:
        The selected winner/loser candidate ID among `tied_ids`.

    Notes:
        Calls `error(...)` and exits when inputs are invalid.
    """
    if not tied_ids:
        error("Cannot tie-break an empty candidate list")

    order_index = {cid: i for i, cid in enumerate(tie_break_order)}
    missing_ids = [candidate_id for candidate_id in tied_ids if candidate_id not in order_index]
    if missing_ids:
        error(f"Cannot tie-break candidates missing from tie_break_order: {missing_ids}")

    return min(tied_ids, key=lambda cid: order_index[cid])


def add_winner(status: Dict[str, str], candidate_id: str) -> None:
    """Mark a candidate as elected in the mutable status map.

    Args:
        status: Candidate status mapping to mutate.
        candidate_id: Candidate to mark elected.

    Notes:
        Calls `error(...)` and exits if `candidate_id` is unknown.
    """
    if candidate_id not in status:
        error(f"Cannot elect unknown candidate '{candidate_id}'")
    status[candidate_id] = "elected"


def eliminate_candidate(status: Dict[str, str], candidate_id: str) -> None:
    """Mark a candidate as eliminated in the mutable status map.

    Args:
        status: Candidate status mapping to mutate.
        candidate_id: Candidate to mark eliminated.

    Notes:
        Calls `error(...)` and exits if `candidate_id` is unknown.
    """
    if candidate_id not in status:
        error(f"Cannot eliminate unknown candidate '{candidate_id}'")
    status[candidate_id] = "eliminated"


def compute_threshold(first_round_total: float, seat_count: int) -> float:
    """Compute the Droop-style STV threshold from first-round valid total.

    Args:
        first_round_total: Sum of first-round votes allocated to active candidates.
        seat_count: Seats to fill in the contest.

    Returns:
        Threshold as `floor(total / (seats + 1)) + 1`.

    Notes:
        Calls `error(...)` and exits if `seat_count < 1`.
    """
    if seat_count < 1:
        error("Cannot compute threshold with seat_count less than 1")
    return math.floor(first_round_total / (seat_count + 1)) + 1


def truncate_4(value: float) -> float:
    """Truncate a numeric value to four decimal places (no rounding).

    Args:
        value: Input numeric value.

    Returns:
        Value truncated to 4 decimal places.
    """
    return math.floor(value * 10_000) / 10_000.0


def append_round(
    rounds: list[Dict],
    round_number: int,
    threshold: Optional[float],
    status: Dict[str, str],
    totals: Dict[str, float],
    action: Optional[Dict],
    include_threshold: bool,
    ballot_allocations: Optional[Dict[str, Optional[str]]] = None,
) -> None:
    """Append one round snapshot to the mutable round log list.

    Args:
        rounds: Round log list to append into.
        round_number: Human-visible round index for this snapshot.
        threshold: Election threshold for STV rounds, else None.
        status: Candidate status mapping to snapshot.
        totals: Vote totals mapping to snapshot.
        action: Action metadata for the round, if any.
        include_threshold: Whether to include threshold in the output entry.
        ballot_allocations: Optional ballot ID -> allocated candidate ID mapping.
    """
    round_entry = {
        "round": round_number,
        "vote_totals": totals.copy(),
        "status": status.copy(),
        "action": action,
    }
    if ballot_allocations is not None:
        round_entry["ballot_allocations"] = ballot_allocations.copy()
    if include_threshold:
        round_entry["threshold"] = threshold
    rounds.append(round_entry)


def count_votes_single_round(
    ballots: list[Ballot],
    status: Dict[str, str],
    use_transfer_values: bool,
    transfer_values_by_ballot_id: Optional[Dict[str, float]] = None,
) -> tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """Count one round of votes and capture per-ballot allocation decisions.

    Args:
        ballots: Ballots to evaluate for this round.
        status: Candidate status mapping used to derive active candidates.
        use_transfer_values: Whether to apply transfer values or unit weights.
        transfer_values_by_ballot_id: Optional per-ballot transfer-value override.

    Returns:
        A tuple:
        - vote totals by candidate ID,
        - ballot allocation mapping (`ballot_id -> candidate_id | None`).
    """
    active_set = set(active_candidates(status))
    totals: Dict[str, float] = {cid: 0.0 for cid in status.keys()}
    ballot_allocations: Dict[str, Optional[str]] = {}

    for ballot in ballots:
        if ballot.state == "inactive":
            ballot_allocations[ballot.ballot_id] = None
            continue

        if is_undervote(ballot):
            ballot.state = "inactive"
            ballot_allocations[ballot.ballot_id] = None
            continue
        candidate_id = highest_ranked_active(ballot, active_set)
        ballot_allocations[ballot.ballot_id] = candidate_id
        if candidate_id is None:
            ballot.state = "inactive"
            continue
        if use_transfer_values:
            if transfer_values_by_ballot_id is None:
                value = ballot.current_transfer_value
            else:
                value = transfer_values_by_ballot_id.get(
                    ballot.ballot_id,
                    ballot.current_transfer_value,
                )
        else:
            value = 1.0
        totals[candidate_id] += value

    return totals, ballot_allocations


def apply_threshold_to_elected(
    totals: Dict[str, float],
    status: Dict[str, str],
    threshold: Optional[float],
) -> None:
    """Normalize already-elected candidate totals to the threshold value.

    Args:
        totals: Candidate vote totals to mutate in place.
        status: Candidate status mapping.
        threshold: Election threshold, or None for no-op.
    """
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
    """Build STV surplus fractions for all newly elected candidates.

    Args:
        elected_candidate_ids: Newly elected candidate IDs this cycle.
        totals: Current round vote totals.
        threshold: Election threshold used to calculate surplus.

    Returns:
        A tuple:
        - mapping of candidate ID -> surplus fraction,
        - action-detail list used for round logging.

    Notes:
        Calls `error(...)` and exits when threshold is missing.
    """
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
    ballots: list[Ballot],
    round_ballot_allocations: Dict[str, Optional[str]],
    surplus_fractions: Dict[str, float],
    transfer_values_by_ballot_id: Dict[str, float],
) -> Dict[str, float]:
    """Apply simultaneous surplus transfer updates using round allocations.

    This function is intentionally non-mutating for caller-owned maps:
    it uses a copy-update-writeback flow and returns a new transfer-value map.

    Args:
        ballots: Ballots participating in the election.
        round_ballot_allocations: Snapshot allocation for the source round.
        surplus_fractions: Per-elected-candidate surplus fractions.
        transfer_values_by_ballot_id: Current transfer values per ballot ID.

    Returns:
        A new transfer-values mapping after applying simultaneous surplus updates.
    """
    # Compute all updated transfer values from a stable round snapshot and then
    # apply them together, so simultaneous surpluses cannot observe one another's
    # in-pass mutations.
    updates_by_ballot_id: Dict[str, float] = {}

    for ballot in ballots:
        allocated_candidate_id = round_ballot_allocations.get(ballot.ballot_id)
        if allocated_candidate_id is None:
            continue

        if allocated_candidate_id not in surplus_fractions:
            continue

        surplus_fraction = surplus_fractions[allocated_candidate_id]
        current_value = transfer_values_by_ballot_id.get(
            ballot.ballot_id,
            ballot.current_transfer_value,
        )
        updates_by_ballot_id[ballot.ballot_id] = truncate_4(
            current_value * surplus_fraction
        )

    if not updates_by_ballot_id:
        return transfer_values_by_ballot_id.copy()

    # Copy -> update -> writeback pattern to avoid mutating source ballots.
    updated_transfer_values = transfer_values_by_ballot_id.copy()
    for ballot_id, updated_transfer_value in updates_by_ballot_id.items():
        updated_transfer_values[ballot_id] = updated_transfer_value

    return updated_transfer_values

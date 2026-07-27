from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Simulation_Layer.Core.config import MODE_SINGLE_SEAT_RCV
from Simulation_Layer.Core.models import Election
from Simulation_Layer.Core.utils import (
    active_candidates,
    add_winner,
    apply_simultaneous_surplus_transfer_values,
    append_round,
    apply_threshold_to_elected,
    build_surplus_fractions,
    compute_threshold,
    count_votes_single_round,
    elected_candidates,
    eliminate_candidate,
    initial_candidate_status,
    tie_break,
)
from Global_Utilities import error, info, read_simulation_ready_json, success, warn


def run_single_seat_rcv(election: Election) -> Dict:
    """Execute one full single-seat RCV election and return round artifacts.

    Args:
        election: Working election object for this execution.

    Returns:
        Result dictionary with winners, round snapshots, and final candidate status.
    """
    status = initial_candidate_status(election.candidates)
    rounds: List[Dict] = []

    while True:
        election.round_number += 1
        totals, ballot_allocations = count_votes_single_round(
            election.ballots, status, use_transfer_values=False
        )
        append_round(
            rounds=rounds,
            round_number=election.round_number,
            threshold=election.threshold,
            status=status,
            totals={cid: totals.get(cid, 0.0) for cid in status.keys()},
            action=None,
            include_threshold=False,
            ballot_allocations=ballot_allocations,
        )

        active = active_candidates(status)
        if not active:
            error(f"No active candidates remain in election '{election.election_id}'")

        if len(active) <= 2:
            max_votes = max(totals.get(candidate_id, 0.0) for candidate_id in active) if active else 0.0
            top = [candidate_id for candidate_id in active if totals.get(candidate_id, 0.0) == max_votes]
            if len(top) > 1:
                # tie_break_order is an elimination priority, not a survival priority
                # (see Documents/AGENTS.md, Documents/README.md): it names who is
                # weaker, never who wins. So resolve a final-round tie the same way
                # every other tie is resolved -- find who it would eliminate -- and
                # elect whichever tied candidate is left.
                eliminated_in_tie = tie_break(top, election.tie_break_order)
                winner = next(candidate_id for candidate_id in top if candidate_id != eliminated_in_tie)
            else:
                winner = top[0]
            add_winner(status, winner)
            rounds[-1]["action"] = {"type": "elect", "candidate": winner}
            break

        min_votes = min(totals.get(candidate_id, 0.0) for candidate_id in active)
        lowest = [candidate_id for candidate_id in active if totals.get(candidate_id, 0.0) == min_votes]
        eliminated = tie_break(lowest, election.tie_break_order) if len(lowest) > 1 else lowest[0]
        eliminate_candidate(status, eliminated)
        rounds[-1]["action"] = {"type": "eliminate", "candidate": eliminated}

    final_status = status.copy()
    winners = [candidate_id for candidate_id, candidate_status in final_status.items() if candidate_status == "elected"]

    return {
        "winners": winners,
        "rounds": rounds,
        "final_candidate_status": final_status,
    }


def run_multi_seat_stv(election: Election) -> Dict:
    """Execute one full multi-seat STV election and return round artifacts.

    The algorithm:
    1. Computes first-round totals and threshold.
    2. Elects threshold-meeting candidates.
    3. Applies simultaneous surplus transfers from the round snapshot.
    4. Eliminates lowest candidates when no threshold election occurs.
    5. Fills remaining seats when active candidates fit remaining seat count.

    Args:
        election: Working election object for this execution.

    Returns:
        Result dictionary with winners, round snapshots, and final candidate status.
    """
    status = initial_candidate_status(election.candidates)
    rounds: List[Dict] = []
    transfer_values_by_ballot_id = {
        ballot.ballot_id: ballot.current_transfer_value for ballot in election.ballots
    }

    election.round_number += 1
    totals, ballot_allocations = count_votes_single_round(
        election.ballots,
        status,
        use_transfer_values=True,
        transfer_values_by_ballot_id=transfer_values_by_ballot_id,
    )
    first_round_total = sum(value for candidate_id, value in totals.items() if status[candidate_id] == "active")
    election.threshold = compute_threshold(first_round_total, election.seat_count)
    append_round(
        rounds=rounds,
        round_number=election.round_number,
        threshold=election.threshold,
        status=status,
        totals=totals,
        action=None,
        include_threshold=True,
        ballot_allocations=ballot_allocations,
    )

    while True:
        active = active_candidates(status)
        elected = elected_candidates(status)
        seats_filled = len(elected)
        seats_remaining = election.seat_count - seats_filled

        if seats_remaining <= 0:
            break

        if len(active) + seats_filled <= election.seat_count:
            for candidate_id in active:
                add_winner(status, candidate_id)
            election.round_number += 1
            append_round(
                rounds=rounds,
                round_number=election.round_number,
                threshold=election.threshold,
                status=status,
                totals=totals,
                action={"type": "fill_remaining_seats", "candidates": active},
                include_threshold=True,
                ballot_allocations=ballot_allocations,
            )
            break

        elected_this_round: List[str] = []
        for candidate_id in active:
            if totals.get(candidate_id, 0.0) >= (election.threshold or 0):
                add_winner(status, candidate_id)
                elected_this_round.append(candidate_id)

        if elected_this_round:
            surplus_fractions, action_detail = build_surplus_fractions(
                elected_candidate_ids=elected_this_round,
                totals=totals,
                threshold=election.threshold,
            )
            transfer_values_by_ballot_id = apply_simultaneous_surplus_transfer_values(
                ballots=election.ballots,
                round_ballot_allocations=ballot_allocations,
                surplus_fractions=surplus_fractions,
                transfer_values_by_ballot_id=transfer_values_by_ballot_id,
            )

            election.round_number += 1
            totals, ballot_allocations = count_votes_single_round(
                election.ballots,
                status,
                use_transfer_values=True,
                transfer_values_by_ballot_id=transfer_values_by_ballot_id,
            )
            apply_threshold_to_elected(totals, status, election.threshold)
            append_round(
                rounds=rounds,
                round_number=election.round_number,
                threshold=election.threshold,
                status=status,
                totals=totals,
                action={"type": "elect_and_transfer", "details": action_detail},
                include_threshold=True,
                ballot_allocations=ballot_allocations,
            )
            continue

        if active:
            min_votes = min(totals.get(candidate_id, 0.0) for candidate_id in active)
            lowest = [candidate_id for candidate_id in active if totals.get(candidate_id, 0.0) == min_votes]
            eliminated = tie_break(lowest, election.tie_break_order) if len(lowest) > 1 else lowest[0]
            eliminate_candidate(status, eliminated)
            action = {"type": "eliminate", "candidate": eliminated}
        else:
            action = None

        election.round_number += 1
        totals, ballot_allocations = count_votes_single_round(
            election.ballots,
            status,
            use_transfer_values=True,
            transfer_values_by_ballot_id=transfer_values_by_ballot_id,
        )
        apply_threshold_to_elected(totals, status, election.threshold)
        append_round(
            rounds=rounds,
            round_number=election.round_number,
            threshold=election.threshold,
            status=status,
            totals=totals,
            action=action,
            include_threshold=True,
            ballot_allocations=ballot_allocations,
        )

    final_status = status.copy()
    winners = [candidate_id for candidate_id, candidate_status in final_status.items() if candidate_status == "elected"]
    return {
        "winners": winners,
        "rounds": rounds,
        "final_candidate_status": final_status,
    }


def run_election(election: Election) -> Dict:
    """Run an election by mode on a deep-copied working election object.

    Args:
        election: Source election definition.

    Returns:
        Result dictionary produced by the selected counting mode.

    Notes:
        A deep copy is used so repeated calls on the same caller-owned object are
        deterministic and do not leak mutable state across executions.
    """
    # Run on a working copy so repeated calls on the same Election object are deterministic.
    working_election = deepcopy(election)
    if working_election.mode == MODE_SINGLE_SEAT_RCV:
        return run_single_seat_rcv(working_election)
    return run_multi_seat_stv(working_election)


def load_election_from_json(path: str) -> Election:
    """Load and validate an election from the shared simulation JSON contract.

    Args:
        path: Relative or absolute path accepted by shared JSON I/O helpers.

    Returns:
        Fully constructed and validated `Election` object.
    """
    (
        election_id,
        seat_count,
        mode,
        candidates,
        ballots,
        tie_break_order,
        max_ranks_allowed,
    ) = read_simulation_ready_json(path)
    return Election(
        election_id=election_id,
        seat_count=seat_count,
        mode=mode,
        candidates=candidates,
        ballots=ballots,
        tie_break_order=tie_break_order,
        max_ranks_allowed=max_ranks_allowed,
    )


def run_cli() -> None:
    """Run the interactive CLI workflow for manual election execution.

    The CLI:
    - prompts for an input JSON path,
    - loads and validates election data,
    - runs the election engine,
    - prints winners, final status, and per-round summaries.
    """
    info("Fair Representation Act Counting Engine")
    info("Interactive mode.")
    info("Enter path to election JSON (matching the Simulation_Layer Design Specification).")
    info("Path:")
    path = input().strip()

    if not path:
        error("No election JSON path provided")

    try:
        election = load_election_from_json(path)
    except SystemExit:
        warn(f"Election loading failed for path '{path}'. Exiting.")
        raise
    except Exception as exc:
        error(f"Invalid election JSON. Details: {exc}")

    try:
        result = run_election(election)
    except SystemExit:
        warn(f"Election execution failed for election '{election.election_id}'. Exiting.")
        raise
    except Exception as exc:
        error(f"Election run failed unexpectedly. Details: {exc}")
    success(f"Winners: {result['winners']}")
    info("Final candidate status:")
    for candidate_id, candidate_status in result["final_candidate_status"].items():
        info(f"{candidate_id}: {candidate_status}")
    info("Rounds:")
    for round_info in result["rounds"]:
        info(f"Round {round_info['round']}:")
        info(f"Vote totals: {round_info['vote_totals']}")
        if "threshold" in round_info and round_info["threshold"] is not None:
            info(f"Threshold: {round_info['threshold']}")
        if round_info.get("action"):
            info(f"Action: {round_info['action']}")


if __name__ == "__main__":
    run_cli()

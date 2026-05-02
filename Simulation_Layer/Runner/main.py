from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

# Allow direct execution via: python "Simulation_Layer/Runner/main.py"
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from Core.config import MODE_SINGLE_SEAT_RCV
from Core.models import Election
from Global_Utilities import error, info, read_simulation_ready_json, success
from Helpers.utils import (
    active_candidates,
    add_winner,
    append_round,
    apply_threshold_to_elected,
    compute_threshold,
    count_votes_single_round,
    distribute_surplus_transfer_values,
    elected_candidates,
    eliminate_candidate,
    initial_candidate_status,
    tie_break,
    truncate_4,
)


def run_single_seat_rcv(election: Election) -> Dict:
    status = initial_candidate_status(election)
    rounds: List[Dict] = []

    while True:
        election.round_number += 1
        totals = count_votes_single_round(election, status, use_transfer_values=False)
        append_round(
            rounds=rounds,
            election=election,
            status=status,
            totals={cid: totals.get(cid, 0.0) for cid in status.keys()},
            action=None,
            include_threshold=False,
        )

        active = active_candidates(status)
        if not active:
            error(f"No active candidates remain in election '{election.election_id}'")

        if len(active) <= 2:
            max_votes = max(totals.get(candidate_id, 0.0) for candidate_id in active) if active else 0.0
            top = [candidate_id for candidate_id in active if totals.get(candidate_id, 0.0) == max_votes]
            winner = tie_break(top, election.tie_break_order) if len(top) > 1 else top[0]
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
    status = initial_candidate_status(election)
    rounds: List[Dict] = []

    election.round_number += 1
    totals = count_votes_single_round(election, status, use_transfer_values=True)
    first_round_total = sum(value for candidate_id, value in totals.items() if status[candidate_id] == "active")
    election.threshold = compute_threshold(first_round_total, election.seat_count)
    append_round(
        rounds=rounds,
        election=election,
        status=status,
        totals=totals,
        action=None,
        include_threshold=True,
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
            append_round(
                rounds=rounds,
                election=election,
                status=status,
                totals=totals,
                action={"type": "fill_remaining_seats", "candidates": active},
                include_threshold=True,
            )
            break

        elected_this_round: List[str] = []
        for candidate_id in active:
            if totals.get(candidate_id, 0.0) >= (election.threshold or 0):
                add_winner(status, candidate_id)
                elected_this_round.append(candidate_id)

        if elected_this_round:
            action_detail: list[Dict] = []
            for candidate_id in elected_this_round:
                vote_total = totals.get(candidate_id, 0.0)
                if vote_total <= 0:
                    action_detail.append({"candidate": candidate_id, "surplus_fraction": 0.0})
                    continue

                surplus_fraction = truncate_4((vote_total - (election.threshold or 0)) / vote_total)
                if surplus_fraction < 0:
                    surplus_fraction = 0.0
                action_detail.append({"candidate": candidate_id, "surplus_fraction": surplus_fraction})

                distribute_surplus_transfer_values(
                    election=election,
                    elected_candidate_id=candidate_id,
                    surplus_fraction=surplus_fraction,
                )

            election.round_number += 1
            totals = count_votes_single_round(election, status, use_transfer_values=True)
            apply_threshold_to_elected(totals, status, election.threshold)
            append_round(
                rounds=rounds,
                election=election,
                status=status,
                totals=totals,
                action={"type": "elect_and_transfer", "details": action_detail},
                include_threshold=True,
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
        totals = count_votes_single_round(election, status, use_transfer_values=True)
        apply_threshold_to_elected(totals, status, election.threshold)
        append_round(
            rounds=rounds,
            election=election,
            status=status,
            totals=totals,
            action=action,
            include_threshold=True,
        )

    final_status = status.copy()
    winners = [candidate_id for candidate_id, candidate_status in final_status.items() if candidate_status == "elected"]
    return {
        "winners": winners,
        "rounds": rounds,
        "final_candidate_status": final_status,
    }


def run_election(election: Election) -> Dict:
    if election.mode == MODE_SINGLE_SEAT_RCV:
        return run_single_seat_rcv(election)
    return run_multi_seat_stv(election)


def load_election_from_json(path: str) -> Election:
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
    info("Fair Representation Act Counting Engine")
    info("Interactive mode.")
    info("Enter path to election JSON (matching the Simulation_Layer Design Specification).")
    info("Path:")
    path = input().strip()

    if not path:
        error("No election JSON path provided")

    try:
        election = load_election_from_json(path)
    except Exception as exc:
        error(f"Invalid election JSON. Details: {exc}")

    result = run_election(election)
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

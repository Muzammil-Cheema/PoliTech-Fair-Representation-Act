from __future__ import annotations

import ast
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIMULATION_ROOT = PROJECT_ROOT / "Simulation_Layer"
CASE_DIR = PROJECT_ROOT / "Pipe" / "Acceptance_Test_Cases"
ACCEPTANCE_REPLAY_RUNS = 5000
REQUIRED_ELECTION_FIELDS = {
    "ballots",
    "candidates",
    "election_id",
    "mode",
    "seat_count",
    "tie_break_order",
}
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")
DEFAULT_TEST_TRANSFER_VALUE = 1.0


if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
if str(SIMULATION_ROOT) not in sys.path:
    sys.path.append(str(SIMULATION_ROOT))


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


def parse_cli_output(stdout: str) -> dict:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]

    winners: list[str] | None = None
    final_candidate_status: dict[str, str] = {}
    rounds: list[dict] = []
    current_round: dict | None = None
    in_final_status = False

    for line in lines:
        if "Winners:" in line:
            winners = ast.literal_eval(line.split("Winners:", 1)[1].strip())
            continue

        if "Final candidate status:" in line:
            in_final_status = True
            continue

        if "Rounds:" in line:
            in_final_status = False
            continue

        if in_final_status and ": " in line and "Round " not in line and "Vote totals:" not in line:
            candidate_id, status = line.rsplit(": ", 1)
            final_candidate_status[candidate_id.split()[-1]] = status
            continue

        round_match = re.search(r"Round (\d+):$", line)
        if round_match:
            current_round = {"round": int(round_match.group(1))}
            rounds.append(current_round)
            continue

        if current_round is None:
            continue

        if "Vote totals:" in line:
            current_round["vote_totals"] = ast.literal_eval(
                line.split("Vote totals:", 1)[1].strip()
            )
            continue

        if "Threshold:" in line:
            current_round["threshold"] = ast.literal_eval(
                line.split("Threshold:", 1)[1].strip()
            )
            continue

        if "Action:" in line:
            current_round["action"] = ast.literal_eval(
                line.split("Action:", 1)[1].strip()
            )

    return {
        "winners": winners or [],
        "rounds": rounds,
        "final_candidate_status": final_candidate_status,
        "raw_output": stdout,
    }


def runnable_pipe_json_files() -> list[Path]:
    runnable_files: list[Path] = []
    for path in sorted((PROJECT_ROOT / "Pipe").rglob("*.json")):
        with path.open("r", encoding="utf-8") as json_file:
            payload = json.load(json_file)

        metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
        available_fields = set(payload.keys()) | set(metadata.keys()) if isinstance(payload, dict) else set()
        if REQUIRED_ELECTION_FIELDS.issubset(available_fields):
            runnable_files.append(path)

    return runnable_files


def acceptance_case_json_files() -> list[Path]:
    return [
        path
        for path in sorted(CASE_DIR.glob("*.json"))
        if path.name != "index.json"
    ]


def fixture_value(payload: Mapping[str, Any], field_name: str) -> Any:
    metadata = payload.get("metadata", {})
    if isinstance(metadata, Mapping) and field_name in metadata:
        return metadata[field_name]
    return payload.get(field_name)


def fixture_candidate_status(payload: Mapping[str, Any]) -> dict[str, str]:
    return {
        candidate["candidate_id"]: "withdrawn" if candidate.get("withdrawn", False) else "active"
        for candidate in payload["candidates"]
    }


def fixture_active_candidates(status: Mapping[str, str]) -> list[str]:
    return [
        candidate_id
        for candidate_id, candidate_status in status.items()
        if candidate_status == "active"
    ]


def fixture_elected_candidates(status: Mapping[str, str]) -> list[str]:
    return [
        candidate_id
        for candidate_id, candidate_status in status.items()
        if candidate_status == "elected"
    ]


def fixture_tie_break(tied_ids: list[str], tie_break_order: list[str]) -> str:
    order_index = {candidate_id: index for index, candidate_id in enumerate(tie_break_order)}
    return min(tied_ids, key=lambda candidate_id: order_index[candidate_id])


def fixture_highest_ranked_active(
    ballot: Mapping[str, Any],
    active_candidate_ids: set[str],
) -> str | None:
    for ranking in sorted(ballot.get("rankings", []), key=lambda item: item["rank"]):
        active_in_rank = [
            candidate_id
            for candidate_id in ranking["candidate_ids"]
            if candidate_id in active_candidate_ids
        ]

        if not active_in_rank:
            continue

        if len(active_in_rank) == 1:
            return active_in_rank[0]

        return None

    return None


def fixture_count_votes(
    payload: Mapping[str, Any],
    status: Mapping[str, str],
    transfer_values_by_ballot_id: Mapping[str, float] | None = None,
    inactive_ballot_ids: set[str] | None = None,
) -> tuple[dict[str, float], dict[str, str | None], set[str]]:
    if inactive_ballot_ids is None:
        inactive_ballot_ids = set()

    active_set = set(fixture_active_candidates(status))
    totals = {candidate_id: 0.0 for candidate_id in status.keys()}
    ballot_allocations: dict[str, str | None] = {}

    for ballot in payload["ballots"]:
        ballot_id = ballot["ballot_id"]
        if ballot_id in inactive_ballot_ids:
            ballot_allocations[ballot_id] = None
            continue

        candidate_id = fixture_highest_ranked_active(ballot, active_set)
        ballot_allocations[ballot_id] = candidate_id

        if candidate_id is None:
            inactive_ballot_ids.add(ballot_id)
            continue

        value = DEFAULT_TEST_TRANSFER_VALUE
        if transfer_values_by_ballot_id is not None:
            value = transfer_values_by_ballot_id.get(ballot_id, DEFAULT_TEST_TRANSFER_VALUE)
        totals[candidate_id] += value

    return totals, ballot_allocations, inactive_ballot_ids


def fixture_threshold(first_round_total: float, seat_count: int) -> float:
    return math.floor(first_round_total / (seat_count + 1)) + 1


def fixture_truncate_4(value: float) -> float:
    return math.floor(value * 10_000) / 10_000.0


def expected_single_seat_winners(payload: Mapping[str, Any]) -> list[str]:
    status = fixture_candidate_status(payload)
    tie_break_order = fixture_value(payload, "tie_break_order")
    inactive_ballot_ids: set[str] = set()

    while True:
        totals, _, inactive_ballot_ids = fixture_count_votes(
            payload,
            status,
            inactive_ballot_ids=inactive_ballot_ids,
        )
        active = fixture_active_candidates(status)

        if len(active) <= 2:
            max_votes = max(totals.get(candidate_id, 0.0) for candidate_id in active)
            top = [
                candidate_id
                for candidate_id in active
                if totals.get(candidate_id, 0.0) == max_votes
            ]
            if len(top) > 1:
                eliminated_in_tie = fixture_tie_break(top, tie_break_order)
                winner = next(
                    candidate_id for candidate_id in top if candidate_id != eliminated_in_tie
                )
            else:
                winner = top[0]
            status[winner] = "elected"
            break

        min_votes = min(totals.get(candidate_id, 0.0) for candidate_id in active)
        lowest = [
            candidate_id
            for candidate_id in active
            if totals.get(candidate_id, 0.0) == min_votes
        ]
        eliminated = fixture_tie_break(lowest, tie_break_order) if len(lowest) > 1 else lowest[0]
        status[eliminated] = "eliminated"

    return fixture_elected_candidates(status)


def expected_multi_seat_winners(payload: Mapping[str, Any]) -> list[str]:
    status = fixture_candidate_status(payload)
    seat_count = fixture_value(payload, "seat_count")
    tie_break_order = fixture_value(payload, "tie_break_order")
    transfer_values_by_ballot_id = {
        ballot["ballot_id"]: DEFAULT_TEST_TRANSFER_VALUE for ballot in payload["ballots"]
    }
    inactive_ballot_ids: set[str] = set()

    totals, ballot_allocations, inactive_ballot_ids = fixture_count_votes(
        payload,
        status,
        transfer_values_by_ballot_id,
        inactive_ballot_ids,
    )
    first_round_total = sum(
        value
        for candidate_id, value in totals.items()
        if status[candidate_id] == "active"
    )
    threshold = fixture_threshold(first_round_total, seat_count)

    while True:
        active = fixture_active_candidates(status)
        elected = fixture_elected_candidates(status)
        seats_remaining = seat_count - len(elected)

        if seats_remaining <= 0:
            break

        if len(active) + len(elected) <= seat_count:
            for candidate_id in active:
                status[candidate_id] = "elected"
            break

        elected_this_round: list[str] = []
        for candidate_id in active:
            if totals.get(candidate_id, 0.0) >= threshold:
                status[candidate_id] = "elected"
                elected_this_round.append(candidate_id)

        if elected_this_round:
            surplus_fractions: dict[str, float] = {}
            for candidate_id in elected_this_round:
                vote_total = totals.get(candidate_id, 0.0)
                surplus_fraction = 0.0
                if vote_total > 0:
                    surplus_fraction = max(
                        fixture_truncate_4((vote_total - threshold) / vote_total),
                        0.0,
                    )
                surplus_fractions[candidate_id] = surplus_fraction

            updated_transfer_values = transfer_values_by_ballot_id.copy()
            for ballot_id, candidate_id in ballot_allocations.items():
                if candidate_id not in surplus_fractions:
                    continue
                current_value = transfer_values_by_ballot_id.get(
                    ballot_id,
                    DEFAULT_TEST_TRANSFER_VALUE,
                )
                updated_transfer_values[ballot_id] = fixture_truncate_4(
                    current_value * surplus_fractions[candidate_id]
                )
            transfer_values_by_ballot_id = updated_transfer_values

            totals, ballot_allocations, inactive_ballot_ids = fixture_count_votes(
                payload,
                status,
                transfer_values_by_ballot_id,
                inactive_ballot_ids,
            )
            continue

        min_votes = min(totals.get(candidate_id, 0.0) for candidate_id in active)
        lowest = [
            candidate_id
            for candidate_id in active
            if totals.get(candidate_id, 0.0) == min_votes
        ]
        eliminated = fixture_tie_break(lowest, tie_break_order) if len(lowest) > 1 else lowest[0]
        status[eliminated] = "eliminated"
        totals, ballot_allocations, inactive_ballot_ids = fixture_count_votes(
            payload,
            status,
            transfer_values_by_ballot_id,
            inactive_ballot_ids,
        )

    return fixture_elected_candidates(status)


def expected_winners_from_json(json_path: Path) -> list[str]:
    with json_path.open("r", encoding="utf-8") as json_file:
        payload = json.load(json_file)

    mode = fixture_value(payload, "mode")
    if mode == "single_seat_rcv":
        return expected_single_seat_winners(payload)
    if mode == "multi_seat_stv":
        return expected_multi_seat_winners(payload)

    raise AssertionError(f"Unsupported election mode in fixture: {mode}")

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIMULATION_ROOT = PROJECT_ROOT / "Simulation_Layer"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
if str(SIMULATION_ROOT) not in sys.path:
    sys.path.append(str(SIMULATION_ROOT))

from Simulation_Layer.Runner.main import run_cli

CASE_DIR = PROJECT_ROOT / "Pipe" / "Acceptance_Test_Cases"
REQUIRED_ELECTION_FIELDS = {
    "ballots",
    "candidates",
    "election_id",
    "mode",
    "seat_count",
    "tie_break_order",
}
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


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


def run_case(cli_path: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> dict:
    monkeypatch.setattr("builtins.input", lambda: cli_path)
    run_cli()
    captured = capsys.readouterr()
    clean_stdout = strip_ansi(captured.out)
    return parse_cli_output(clean_stdout)


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


@pytest.mark.parametrize(
    "json_path",
    runnable_pipe_json_files(),
    ids=lambda path: path.relative_to(PROJECT_ROOT / "Pipe").as_posix(),
)
def test_all_runnable_pipe_json_files_complete(
    json_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli_path = json_path.relative_to(PROJECT_ROOT / "Pipe").as_posix()
    result = run_case(cli_path, monkeypatch, capsys)

    assert result["winners"]
    assert result["rounds"]


# Verifies ordinary single-seat RCV elimination: the lowest candidate drops
# first, their ballot transfers, and candidate C wins in the final two-candidate
# round.
def test_single_seat_ordinary_elimination(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/01_single_seat_ordinary_elimination.json", monkeypatch, capsys)

    assert result["winners"] == ["C"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "B"}
    assert result["rounds"][1]["vote_totals"]["C"] == pytest.approx(3.0)
    assert result["final_candidate_status"] == {
        "A": "active",
        "B": "eliminated",
        "C": "elected",
    }


# Verifies withdrawn candidates are inactive from the start, so first-choice
# ballots for B immediately resolve to the next active ranking and elect A.
def test_single_seat_with_withdrawn_candidate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/02_single_seat_with_withdrawn_candidate.json", monkeypatch, capsys)

    assert result["winners"] == ["A"]
    assert result["rounds"][0]["vote_totals"] == {"A": 3.0, "B": 0.0, "C": 1.0}
    assert result["final_candidate_status"]["B"] == "withdrawn"
    assert result["final_candidate_status"]["A"] == "elected"


# Verifies the single-seat counter stops correctly when only two active
# candidates are present and elects the higher vote-getter in one round.
def test_single_seat_two_active_candidates(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/03_single_seat_two_active_candidates.json", monkeypatch, capsys)

    assert result["winners"] == ["A"]
    assert len(result["rounds"]) == 1
    assert result["rounds"][0]["action"] == {"type": "elect", "candidate": "A"}


# Verifies multi-seat STV elects a candidate above threshold, transfers only
# that candidate's surplus, and then fills the remaining seat with B.
def test_multi_seat_one_candidate_exceeds_threshold(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/04_multi_seat_one_candidate_exceeds_threshold.json", monkeypatch, capsys)

    assert result["winners"] == ["A", "B"]
    assert result["rounds"][0]["threshold"] == 2
    assert result["rounds"][1]["action"] == {
        "type": "elect_and_transfer",
        "details": [{"candidate": "A", "surplus_fraction": 0.3333}],
    }
    assert result["rounds"][-1]["action"] == {
        "type": "fill_remaining_seats",
        "candidates": ["B"],
    }


# Verifies simultaneous surplus handling when two candidates clear the threshold
# in the same round, producing both winners together.
def test_multi_seat_multiple_candidates_exceed_threshold(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/05_multi_seat_multiple_candidates_exceed_threshold.json", monkeypatch, capsys)

    assert result["winners"] == ["A", "B"]
    assert result["rounds"][0]["threshold"] == 3
    assert result["rounds"][1]["action"] == {
        "type": "elect_and_transfer",
        "details": [
            {"candidate": "A", "surplus_fraction": 0.25},
            {"candidate": "B", "surplus_fraction": 0.25},
        ],
    }
    assert result["final_candidate_status"]["C"] == "active"


# Verifies the no-threshold-elimination path in STV: D is eliminated first, C
# is then elected at threshold, and B claims the last remaining seat.
def test_multi_seat_lowest_candidate_eliminated(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/06_multi_seat_lowest_candidate_eliminated.json", monkeypatch, capsys)

    assert result["winners"] == ["B", "C"]
    assert result["rounds"][1]["action"] == {"type": "eliminate", "candidate": "D"}
    assert result["rounds"][2]["action"] == {
        "type": "elect_and_transfer",
        "details": [{"candidate": "C", "surplus_fraction": 0.0}],
    }
    assert result["final_candidate_status"] == {
        "A": "eliminated",
        "B": "elected",
        "C": "elected",
        "D": "eliminated",
    }


# Verifies an undervote ballot contributes nothing to the tally and the counted
# ballots alone still elect A.
def test_undervote_ballot_ignored(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/07_undervote_ballot_ignored.json", monkeypatch, capsys)

    assert result["winners"] == ["A"]
    assert result["rounds"][0]["vote_totals"] == {"A": 2.0, "B": 1.0}
    assert len(result["rounds"]) == 1


# Verifies a ballot with only eliminated candidates becomes inactive instead of
# transferring further, leaving the final round tied 2-2 between A and B.
def test_ballot_becomes_inactive_all_ranked_candidates_inactive(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/08_ballot_becomes_inactive_all_ranked_candidates_inactive.json", monkeypatch, capsys)

    assert result["winners"] == ["A"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "C"}
    assert result["rounds"][1]["vote_totals"] == {"A": 2.0, "B": 2.0, "C": 0.0}
    assert result["rounds"][1]["action"] == {"type": "elect", "candidate": "A"}


# Verifies skipped ranks are preserved: after A is eliminated, the ballot with a
# missing rank 2 still transfers from rank 1 to rank 3 and keeps C competitive.
def test_skipped_ranking_remains_valid(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/09_skipped_ranking_remains_valid.json", monkeypatch, capsys)

    assert result["winners"] == ["B"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["vote_totals"] == {"A": 0.0, "B": 2.0, "C": 2.0}


# Verifies repeated candidate rankings remain valid: the ballot transfers using
# the earliest later usable ranking and does not become invalid.
def test_repeated_candidate_remains_valid(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/10_repeated_candidate_remains_valid.json", monkeypatch, capsys)

    assert result["winners"] == ["B"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["vote_totals"] == {"A": 0.0, "B": 2.0, "C": 2.0}


# Verifies a same-rank group causes temporary inactivity when first reached, but
# becomes usable later once only one candidate in that rank group is still active.
def test_same_rank_assignment_causes_inactivity(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/11_same_rank_assignment_causes_inactivity.json", monkeypatch, capsys)

    assert result["winners"] == ["C"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["vote_totals"] == {
        "A": 0.0,
        "B": 1.0,
        "C": 1.0,
        "D": 2.0,
    }
    assert result["rounds"][2]["vote_totals"]["C"] == pytest.approx(2.0)


# Verifies the deterministic tie-break rule drives both elimination and the
# final winner selection in an otherwise perfectly tied single-seat contest.
def test_tie_break_rule_deterministic(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/12_tie_break_rule_deterministic.json", monkeypatch, capsys)

    assert result["winners"] == ["B"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["action"] == {"type": "elect", "candidate": "B"}


# Verifies STV completion can end the count once the remaining active candidates
# fit exactly into the remaining seats, filling all three seats without more rounds.
def test_completion_when_remaining_candidates_match_seats(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/13_completion_when_remaining_candidates_match_seats.json", monkeypatch, capsys)

    assert result["winners"] == ["A", "B", "C"]
    assert result["rounds"][0]["threshold"] == 2
    assert result["rounds"][1]["action"] == {
        "type": "fill_remaining_seats",
        "candidates": ["A", "B", "C"],
    }
    assert result["final_candidate_status"] == {
        "A": "elected",
        "B": "elected",
        "C": "elected",
    }


# Verifies a candidate elected exactly at threshold has zero surplus, so those
# ballots transfer forward at value 0 and the final winners are A and C, not all three.
def test_candidate_reaches_threshold_exactly(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_case("Acceptance_Test_Cases/14_candidate_reaches_threshold_exactly.json", monkeypatch, capsys)

    assert result["winners"] == ["A", "C"]
    assert result["rounds"][1]["action"] == {
        "type": "elect_and_transfer",
        "details": [{"candidate": "A", "surplus_fraction": 0.0}],
    }
    assert result["rounds"][1]["vote_totals"] == {"A": 2, "B": 1.0, "C": 1.0}
    assert result["rounds"][-1]["action"] == {
        "type": "fill_remaining_seats",
        "candidates": ["C"],
    }

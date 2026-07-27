from __future__ import annotations

from pathlib import Path

import pytest

from acceptance_helpers import (
    ACCEPTANCE_REPLAY_RUNS,
    PROJECT_ROOT,
    acceptance_case_json_files,
    expected_winners_from_json,
    parse_cli_output,
    runnable_pipe_json_files,
    strip_ansi,
)
from Global_Utilities import success, warn
from Simulation_Layer.Runner.main import run_cli


def run_case(cli_path: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> dict:
    monkeypatch.setattr("builtins.input", lambda: cli_path)
    run_cli()
    captured = capsys.readouterr()
    clean_stdout = strip_ansi(captured.out)
    return parse_cli_output(clean_stdout)


def log_winner_check(
    *,
    json_path: Path,
    expected_winners: list[str],
    actual_winners: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture_name = json_path.relative_to(PROJECT_ROOT / "Pipe").as_posix()
    if actual_winners == expected_winners:
        with capsys.disabled():
            success(f"{fixture_name} winners match expected output: {actual_winners}")
        return

    with capsys.disabled():
        warn(
            f"{fixture_name} winners differ. "
            f"Expected: {expected_winners}; actual: {actual_winners}"
        )


def log_test_success(capsys: pytest.CaptureFixture[str], message: str) -> None:
    with capsys.disabled():
        success(message)


def test_cli_invalid_path_logs_context_before_exit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify invalid CLI paths log read details and CLI context before exit."""
    monkeypatch.setattr("builtins.input", lambda: "Pipe/does_not_exist.json")

    with pytest.raises(SystemExit) as exc_info:
        run_cli()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    clean_stdout = strip_ansi(captured.out)
    assert "Could not read simulation JSON" in clean_stdout
    assert "Election loading failed for path 'Pipe/does_not_exist.json'. Exiting." in clean_stdout
    log_test_success(capsys, "test_cli_invalid_path_logs_context_before_exit passed.")


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
    """Verify each runnable Pipe JSON completes and prints expected winners."""
    cli_path = json_path.relative_to(PROJECT_ROOT / "Pipe").as_posix()
    result = run_case(cli_path, monkeypatch, capsys)
    expected_winners = expected_winners_from_json(json_path)
    log_winner_check(
        json_path=json_path,
        expected_winners=expected_winners,
        actual_winners=result["winners"],
        capsys=capsys,
    )

    assert result["winners"] == expected_winners
    assert result["rounds"]


# Verifies ordinary single-seat RCV elimination: the lowest candidate drops
# first, their ballot transfers, and candidate C wins in the final two-candidate
# round.
def test_single_seat_ordinary_elimination(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify ordinary single-seat RCV elimination transfers B ballots to C."""
    result = run_case("Acceptance_Test_Cases/01_single_seat_ordinary_elimination.json", monkeypatch, capsys)

    assert result["winners"] == ["C"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "B"}
    assert result["rounds"][1]["vote_totals"]["C"] == pytest.approx(3.0)
    assert result["final_candidate_status"] == {
        "A": "active",
        "B": "eliminated",
        "C": "elected",
    }
    log_test_success(capsys, "test_single_seat_ordinary_elimination passed.")


# Verifies withdrawn candidates are inactive from the start, so first-choice
# ballots for B immediately resolve to the next active ranking and elect A.
def test_single_seat_with_withdrawn_candidate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify withdrawn candidates are inactive and ballots advance to A."""
    result = run_case("Acceptance_Test_Cases/02_single_seat_with_withdrawn_candidate.json", monkeypatch, capsys)

    assert result["winners"] == ["A"]
    assert result["rounds"][0]["vote_totals"] == {"A": 3.0, "B": 0.0, "C": 1.0}
    assert result["final_candidate_status"]["B"] == "withdrawn"
    assert result["final_candidate_status"]["A"] == "elected"
    log_test_success(capsys, "test_single_seat_with_withdrawn_candidate passed.")


# Verifies the single-seat counter stops correctly when only two active
# candidates are present and elects the higher vote-getter in one round.
def test_single_seat_two_active_candidates(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify a two-active-candidate RCV contest elects the top vote-getter."""
    result = run_case("Acceptance_Test_Cases/03_single_seat_two_active_candidates.json", monkeypatch, capsys)

    assert result["winners"] == ["A"]
    assert len(result["rounds"]) == 1
    assert result["rounds"][0]["action"] == {"type": "elect", "candidate": "A"}
    log_test_success(capsys, "test_single_seat_two_active_candidates passed.")


# Verifies multi-seat STV elects a candidate above threshold, transfers only
# that candidate's surplus, and then fills the remaining seat with B.
def test_multi_seat_one_candidate_exceeds_threshold(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify STV surplus transfer after one candidate exceeds threshold."""
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
    log_test_success(capsys, "test_multi_seat_one_candidate_exceeds_threshold passed.")


# Verifies simultaneous surplus handling when two candidates clear the threshold
# in the same round, producing both winners together.
def test_multi_seat_multiple_candidates_exceed_threshold(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify simultaneous STV surplus transfers elect A and B together."""
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
    log_test_success(capsys, "test_multi_seat_multiple_candidates_exceed_threshold passed.")


# Verifies the no-threshold-elimination path in STV: D is eliminated first, C
# is then elected at threshold, and B claims the last remaining seat.
def test_multi_seat_lowest_candidate_eliminated(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify STV eliminates the lowest candidate before threshold election."""
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
    log_test_success(capsys, "test_multi_seat_lowest_candidate_eliminated passed.")


# Verifies an undervote ballot contributes nothing to the tally and the counted
# ballots alone still elect A.
def test_undervote_ballot_ignored(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify undervote ballots contribute no votes and A still wins."""
    result = run_case("Acceptance_Test_Cases/07_undervote_ballot_ignored.json", monkeypatch, capsys)

    assert result["winners"] == ["A"]
    assert result["rounds"][0]["vote_totals"] == {"A": 2.0, "B": 1.0}
    assert len(result["rounds"]) == 1
    log_test_success(capsys, "test_undervote_ballot_ignored passed.")


# Verifies a ballot with only eliminated candidates becomes inactive instead of
# transferring further, leaving the final round tied 2-2 between A and B.
def test_ballot_becomes_inactive_all_ranked_candidates_inactive(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify ballots with no active ranked candidates become inactive."""
    result = run_case("Acceptance_Test_Cases/08_ballot_becomes_inactive_all_ranked_candidates_inactive.json", monkeypatch, capsys)

    assert result["winners"] == ["B"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "C"}
    assert result["rounds"][1]["vote_totals"] == {"A": 2.0, "B": 2.0, "C": 0.0}
    assert result["rounds"][1]["action"] == {"type": "elect", "candidate": "B"}
    log_test_success(capsys, "test_ballot_becomes_inactive_all_ranked_candidates_inactive passed.")


# Verifies skipped ranks are preserved: after A is eliminated, the ballot with a
# missing rank 2 still transfers from rank 1 to rank 3, tying B and C, and the
# tie-break order (which names B as the weaker of the two) lets C win.
def test_skipped_ranking_remains_valid(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify skipped ranks preserve later usable rankings for transfer."""
    result = run_case("Acceptance_Test_Cases/09_skipped_ranking_remains_valid.json", monkeypatch, capsys)

    assert result["winners"] == ["C"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["vote_totals"] == {"A": 0.0, "B": 2.0, "C": 2.0}
    log_test_success(capsys, "test_skipped_ranking_remains_valid passed.")


# Verifies repeated candidate rankings remain valid: the ballot transfers using
# the earliest later usable ranking and does not become invalid.
def test_repeated_candidate_remains_valid(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify repeated candidate rankings do not invalidate the ballot."""
    result = run_case("Acceptance_Test_Cases/10_repeated_candidate_remains_valid.json", monkeypatch, capsys)

    assert result["winners"] == ["C"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["vote_totals"] == {"A": 0.0, "B": 2.0, "C": 2.0}
    log_test_success(capsys, "test_repeated_candidate_remains_valid passed.")


# Verifies same-rank ambiguity creates a persistently inactive ballot under FRA,
# so it cannot be revived in later rounds after additional eliminations.
def test_same_rank_assignment_causes_inactivity(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify same-rank ambiguity causes permanent ballot inactivity."""
    result = run_case("Acceptance_Test_Cases/11_same_rank_assignment_causes_inactivity.json", monkeypatch, capsys)

    assert result["winners"] == ["D"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["vote_totals"] == {
        "A": 0.0,
        "B": 1.0,
        "C": 1.0,
        "D": 2.0,
    }
    assert result["rounds"][2]["vote_totals"]["C"] == pytest.approx(1.0)
    assert result["rounds"][2]["vote_totals"]["D"] == pytest.approx(2.0)
    assert result["rounds"][2]["action"] == {"type": "elect", "candidate": "D"}
    log_test_success(capsys, "test_same_rank_assignment_causes_inactivity passed.")


# Verifies the deterministic tie-break rule drives both elimination and the
# final winner selection in an otherwise perfectly tied single-seat contest.
def test_tie_break_rule_deterministic(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify tie-break order controls tied elimination and final election."""
    result = run_case("Acceptance_Test_Cases/12_tie_break_rule_deterministic.json", monkeypatch, capsys)

    assert result["winners"] == ["C"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["action"] == {"type": "elect", "candidate": "C"}
    log_test_success(capsys, "test_tie_break_rule_deterministic passed.")


# Verifies STV completion can end the count once the remaining active candidates
# fit exactly into the remaining seats, filling all three seats without more rounds.
def test_completion_when_remaining_candidates_match_seats(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify STV fills seats when active candidates equal remaining seats."""
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
    log_test_success(capsys, "test_completion_when_remaining_candidates_match_seats passed.")


# Verifies a candidate elected exactly at threshold has zero surplus, so those
# ballots transfer forward at value 0 and the final winners are A and C, not all three.
def test_candidate_reaches_threshold_exactly(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify exact-threshold election has zero surplus transfer."""
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
    log_test_success(capsys, "test_candidate_reaches_threshold_exactly passed.")


# Verifies replay safety across every canonical acceptance fixture: repeated
# runs against the same in-memory election object should keep producing the
# fixture-derived expected winners.
def test_acceptance_cases_are_deterministic_over_repeated_runs(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify all acceptance fixtures keep expected winners over repeated runs."""
    failures: list[str] = []

    for json_path in acceptance_case_json_files():
        cli_path = json_path.relative_to(PROJECT_ROOT / "Pipe").as_posix()
        expected_winners = expected_winners_from_json(json_path)

        for run_number in range(1, ACCEPTANCE_REPLAY_RUNS + 1):
            result = run_case(cli_path, monkeypatch, capsys)
            actual_winners = result["winners"]
            if actual_winners == expected_winners:
                continue

            failure = (
                f"{cli_path} run {run_number}: "
                f"expected {expected_winners}; actual {actual_winners}"
            )
            failures.append(failure)
            with capsys.disabled():
                warn(f"Determinism check failed. {failure}")

    if not failures:
        log_test_success(
            capsys,
            f"test_acceptance_cases_are_deterministic_over_repeated_runs passed: "
            f"all {len(acceptance_case_json_files())} acceptance cases matched "
            f"expected winners across {ACCEPTANCE_REPLAY_RUNS} repeated run_cli() runs each.",
        )

    assert not failures

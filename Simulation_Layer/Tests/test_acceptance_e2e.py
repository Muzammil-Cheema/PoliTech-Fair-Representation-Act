from __future__ import annotations

from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIMULATION_ROOT = PROJECT_ROOT / "Simulation_Layer"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
if str(SIMULATION_ROOT) not in sys.path:
    sys.path.append(str(SIMULATION_ROOT))

from Runner.main import load_election_from_json, run_election


CASE_DIR = PROJECT_ROOT / "Pipe" / "Acceptance_Test_Cases"


def run_case(filename: str) -> dict:
    election = load_election_from_json(CASE_DIR / filename)
    return run_election(election)


# Verifies ordinary single-seat RCV elimination: the lowest candidate drops
# first, their ballot transfers, and candidate C wins in the final two-candidate
# round.
def test_single_seat_ordinary_elimination() -> None:
    result = run_case("01_single_seat_ordinary_elimination.json")

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
def test_single_seat_with_withdrawn_candidate() -> None:
    result = run_case("02_single_seat_with_withdrawn_candidate.json")

    assert result["winners"] == ["A"]
    assert result["rounds"][0]["vote_totals"] == {"A": 3.0, "B": 0.0, "C": 1.0}
    assert result["rounds"][0]["status"]["B"] == "withdrawn"
    assert result["final_candidate_status"]["A"] == "elected"


# Verifies the single-seat counter stops correctly when only two active
# candidates are present and elects the higher vote-getter in one round.
def test_single_seat_two_active_candidates() -> None:
    result = run_case("03_single_seat_two_active_candidates.json")

    assert result["winners"] == ["A"]
    assert len(result["rounds"]) == 1
    assert result["rounds"][0]["action"] == {"type": "elect", "candidate": "A"}


# Verifies multi-seat STV elects a candidate above threshold, transfers only
# that candidate's surplus, and then fills the remaining seat with B.
def test_multi_seat_one_candidate_exceeds_threshold() -> None:
    result = run_case("04_multi_seat_one_candidate_exceeds_threshold.json")

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
def test_multi_seat_multiple_candidates_exceed_threshold() -> None:
    result = run_case("05_multi_seat_multiple_candidates_exceed_threshold.json")

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
def test_multi_seat_lowest_candidate_eliminated() -> None:
    result = run_case("06_multi_seat_lowest_candidate_eliminated.json")

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
def test_undervote_ballot_ignored() -> None:
    result = run_case("07_undervote_ballot_ignored.json")

    assert result["winners"] == ["A"]
    assert result["rounds"][0]["vote_totals"] == {"A": 2.0, "B": 1.0}
    assert len(result["rounds"]) == 1


# Verifies a ballot with only eliminated candidates becomes inactive instead of
# transferring further, leaving the final round tied 2-2 between A and B.
def test_ballot_becomes_inactive_all_ranked_candidates_inactive() -> None:
    result = run_case("08_ballot_becomes_inactive_all_ranked_candidates_inactive.json")

    assert result["winners"] == ["A"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "C"}
    assert result["rounds"][1]["vote_totals"] == {"A": 2.0, "B": 2.0, "C": 0.0}
    assert result["rounds"][1]["action"] == {"type": "elect", "candidate": "A"}


# Verifies skipped ranks are preserved: after A is eliminated, the ballot with a
# missing rank 2 still transfers from rank 1 to rank 3 and keeps C competitive.
def test_skipped_ranking_remains_valid() -> None:
    result = run_case("09_skipped_ranking_remains_valid.json")

    assert result["winners"] == ["B"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["vote_totals"] == {"A": 0.0, "B": 2.0, "C": 2.0}


# Verifies repeated candidate rankings remain valid: the ballot transfers using
# the earliest later usable ranking and does not become invalid.
def test_repeated_candidate_remains_valid() -> None:
    result = run_case("10_repeated_candidate_remains_valid.json")

    assert result["winners"] == ["B"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["vote_totals"] == {"A": 0.0, "B": 2.0, "C": 2.0}


# Verifies a same-rank group causes temporary inactivity when first reached, but
# becomes usable later once only one candidate in that rank group is still active.
def test_same_rank_assignment_causes_inactivity() -> None:
    result = run_case("11_same_rank_assignment_causes_inactivity.json")

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
def test_tie_break_rule_deterministic() -> None:
    result = run_case("12_tie_break_rule_deterministic.json")

    assert result["winners"] == ["B"]
    assert result["rounds"][0]["action"] == {"type": "eliminate", "candidate": "A"}
    assert result["rounds"][1]["action"] == {"type": "elect", "candidate": "B"}


# Verifies STV completion can end the count once the remaining active candidates
# fit exactly into the remaining seats, filling all three seats without more rounds.
def test_completion_when_remaining_candidates_match_seats() -> None:
    result = run_case("13_completion_when_remaining_candidates_match_seats.json")

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
def test_candidate_reaches_threshold_exactly() -> None:
    result = run_case("14_candidate_reaches_threshold_exactly.json")

    assert result["winners"] == ["A", "C"]
    assert result["rounds"][1]["action"] == {
        "type": "elect_and_transfer",
        "details": [{"candidate": "A", "surplus_fraction": 0.0}],
    }
    assert result["rounds"][1]["vote_totals"] == {"A": 2, "B": 0.0, "C": 0.0}
    assert result["rounds"][-1]["action"] == {
        "type": "fill_remaining_seats",
        "candidates": ["C"],
    }

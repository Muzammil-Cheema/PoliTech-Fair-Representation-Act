from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from Global_Utilities import read_simulation_ready_json
from output_writer import write_simulation_ready_output
from Representational_Layer import Ballot, Candidate, RankGroup


def test_global_json_io_returns_typed_simulation_objects(tmp_path: Path) -> None:
    output_path = write_simulation_ready_output(
        test_name="json_io_contract",
        candidates=[
            Candidate(
                candidate_id="cand-a",
                election_id="election-001",
                profile={"party_id": "D"},
            ),
            Candidate(
                candidate_id="cand-b",
                election_id="election-001",
                withdrawn=True,
                profile={"party_id": "R"},
            ),
        ],
        ballots=[
            Ballot(
                ballot_id="ballot-001",
                generation_run_id="run-001",
                source_elector_unit_id="block-001",
                rankings=[
                    RankGroup(rank=1, candidate_ids=["cand-a"]),
                    RankGroup(rank=2, candidate_ids=["cand-b"]),
                ],
            )
        ],
        metadata={
            "election_id": "election-001",
            "seat_count": 1,
            "mode": "single_seat_rcv",
            "tie_break_order": ["cand-a", "cand-b"],
            "max_ranks_allowed": 2,
        },
        project_root=tmp_path,
    )

    (
        election_id,
        seat_count,
        mode,
        candidates,
        ballots,
        tie_break_order,
        max_ranks_allowed,
    ) = read_simulation_ready_json(output_path)

    assert election_id == "election-001"
    assert seat_count == 1
    assert mode == "single_seat_rcv"
    assert [candidate.candidate_id for candidate in candidates] == ["cand-a", "cand-b"]
    assert candidates[1].withdrawn is True
    assert ballots[0].rankings[0].candidate_ids == ["cand-a"]
    assert tie_break_order == ["cand-a", "cand-b"]
    assert max_ranks_allowed == 2

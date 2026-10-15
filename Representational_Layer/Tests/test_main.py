import json
import pytest
from pathlib import Path

from Representational_Layer.Utils import load_experiment_contract
from Representational_Layer.main import run_representational_workflow
from Global_Utilities import read_simulation_ready_json


def test_run_representational_workflow_valid_contract(tmp_path: Path):
    # Path to the valid fixture
    fixture_dir = Path(__file__).parent / "Input_Contracts"
    contract_path = fixture_dir / "valid_starter_and_custom_contract.json"
    output_path = tmp_path / "valid_output.json"

    state = load_experiment_contract(contract_path)
    assert len(state.ballot_generation_runs) == 1
    selected_run = state.ballot_generation_runs[0]
    expected_ballot_count = sum(
        unit.size
        for unit in state.elector_units
        if unit.election_id == selected_run.election_id
    )

    # Run workflow
    result = run_representational_workflow(
        contract_path=contract_path,
        output_path=output_path,
    )

    assert result.output_path.exists()
    assert len(result.candidates) > 0
    assert len(result.ballots) > 0
    
    # Verify the contents via read_simulation_ready_json
    election_id, seat_count, mode, candidates, ballots, tie_break_order, max_ranks_allowed = read_simulation_ready_json(result.output_path)
    
    assert election_id == "election-north"
    assert seat_count == 3
    assert mode == "multi_seat_stv"
    
    # Default run selection uses the sole generation run in this fixture.
    # The ballot population must equal the summed elector-unit size for that run's election.
    assert len(ballots) == expected_ballot_count
    

def test_run_representational_workflow_ambiguous_runs(tmp_path: Path):
    # Create a temporary contract with multiple generation runs
    fixture_dir = Path(__file__).parent / "Input_Contracts"
    contract_path = fixture_dir / "valid_starter_and_custom_contract.json"
    
    # Load and duplicate the generation run
    data = json.loads(contract_path.read_text(encoding="utf-8"))
    run2 = dict(data["ballot_generation_runs"][0])
    run2["generation_run_id"] = "run-2"
    data["ballot_generation_runs"].append(run2)
    
    multi_run_path = tmp_path / "multi_run.json"
    multi_run_path.write_text(json.dumps(data), encoding="utf-8")
    
    # Should raise error when no generation_run_id is specified
    with pytest.raises(ValueError, match="contains multiple generation runs"):
        run_representational_workflow(contract_path=multi_run_path)
        
    # Should succeed when explicit ID is provided
    output_path = tmp_path / "multi_run_output.json"
    result = run_representational_workflow(
        contract_path=multi_run_path,
        generation_run_id="run-2",
        output_path=output_path,
    )
    assert output_path.exists()
    assert result.output_path == output_path


def test_run_representational_workflow_is_deterministic_for_same_contract_and_seed(
    tmp_path: Path,
):
    fixture_dir = Path(__file__).parent / "Input_Contracts"
    contract_path = fixture_dir / "valid_starter_and_custom_contract.json"

    first_output_path = tmp_path / "deterministic_first.json"
    second_output_path = tmp_path / "deterministic_second.json"

    first_result = run_representational_workflow(
        contract_path=contract_path,
        output_path=first_output_path,
    )
    second_result = run_representational_workflow(
        contract_path=contract_path,
        output_path=second_output_path,
    )

    assert [candidate.candidate_id for candidate in first_result.candidates] == [
        candidate.candidate_id for candidate in second_result.candidates
    ]
    assert [ballot.ballot_id for ballot in first_result.ballots] == [
        ballot.ballot_id for ballot in second_result.ballots
    ]
    assert [ballot.rankings for ballot in first_result.ballots] == [
        ballot.rankings for ballot in second_result.ballots
    ]

    first_payload = json.loads(first_result.output_path.read_text(encoding="utf-8"))
    second_payload = json.loads(second_result.output_path.read_text(encoding="utf-8"))
    assert first_payload == second_payload


@pytest.mark.parametrize("missing", ["candidates", "elector_units"])
def test_selected_election_requires_candidates_and_elector_units(
    tmp_path: Path, missing: str,
) -> None:
    contract_path = Path(__file__).parent / "Input_Contracts" / "valid_starter_and_custom_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    district = {**contract["districts"][0], "district_id": "district-south"}
    election = {
        **contract["elections"][0],
        "election_id": "election-south",
        "district_id": district["district_id"],
    }
    run = {
        **contract["ballot_generation_runs"][0],
        "generation_run_id": "run-south",
        "election_id": election["election_id"],
    }
    contract["districts"].append(district)
    contract["elections"].append(election)
    contract["ballot_generation_runs"].append(run)

    if missing == "candidates":
        contract["elector_units"].append({
            **contract["elector_units"][0],
            "elector_unit_id": "block-south",
            "election_id": election["election_id"],
        })
        expected_error = "no active candidates"
    else:
        contract["candidates"].append({
            **contract["candidates"][0],
            "candidate_id": "cand-south",
            "election_id": election["election_id"],
        })
        expected_error = "no elector units"

    config_path = tmp_path / "missing_selected_data.json"
    config_path.write_text(json.dumps(contract), encoding="utf-8")
    load_experiment_contract(config_path)

    output_path = tmp_path / "should_not_exist.json"
    with pytest.raises(ValueError, match=expected_error):
        run_representational_workflow(
            contract_path=config_path,
            generation_run_id="run-south",
            output_path=output_path,
        )
    assert not output_path.exists()


@pytest.mark.parametrize(
    "ranking_method",
    ["deterministic_sort", "weighted_without_replacement", "softmax_without_replacement"],
)
def test_rank_cap_applies_during_ballot_creation(
    tmp_path: Path, ranking_method: str,
) -> None:
    contract_path = Path(__file__).parent / "Input_Contracts" / "valid_starter_and_custom_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["districts"][0]["seat_target"] = 1
    contract["elections"][0]["mode"] = "single_seat_rcv"
    contract["elections"][0]["max_rankings_allowed"] = 1
    contract["elector_units"][0]["size"] = 2
    contract["preference_models"][0]["ranking_method"] = ranking_method
    config_path = tmp_path / "rank_capped.json"
    config_path.write_text(json.dumps(contract), encoding="utf-8")

    result = run_representational_workflow(config_path, output_path=tmp_path / "output.json")

    assert len(result.ballots) == 2
    assert all(len(ballot.rankings) == 1 for ballot in result.ballots)
    if ranking_method == "deterministic_sort":
        assert result.ballots[0].rankings == result.ballots[1].rankings
    assert all(isinstance(ballot.rankings, tuple) for ballot in result.ballots)


def test_selected_election_rejects_only_withdrawn_candidates(tmp_path: Path) -> None:
    contract_path = Path(__file__).parent / "Input_Contracts" / "valid_starter_and_custom_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    first_candidate = contract["candidates"][0]
    contract["candidates"][0] = {
        "candidate_id": first_candidate["candidate_id"],
        "election_id": first_candidate["election_id"],
        "withdrawn": True,
        "profile": first_candidate["profile"],
    }
    contract["candidates"][1]["withdrawn"] = True
    config_path = tmp_path / "withdrawn_candidates.json"
    config_path.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(ValueError, match="no active candidates"):
        run_representational_workflow(config_path, output_path=tmp_path / "output.json")

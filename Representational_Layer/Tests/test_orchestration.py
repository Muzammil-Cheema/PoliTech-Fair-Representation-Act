from __future__ import annotations

import json
from pathlib import Path

from Attributes import STARTER_ACTIVE_ATTRIBUTES, STARTER_ATTRIBUTE_WEIGHTS, get_starter_attribute_specs
from Global_Utilities import read_simulation_ready_json
from Representational_Layer import (
    BallotGenerationRun,
    Candidate,
    District,
    Election,
    ElectorUnit,
    Experiment,
    PreferenceModel,
    RepresentationalExperimentState,
    RepresentationalWorkflowConfig,
    run_representational_workflow,
)


def _build_experiment_state(*, ranking_method: str) -> RepresentationalExperimentState:
    experiment = Experiment(experiment_id="exp-orchestration")
    district = District(
        district_id="district-orchestration",
        experiment_id=experiment.experiment_id,
        population=100_000,
        seat_target=3,
    )
    election = Election(
        election_id="election-orchestration",
        experiment_id=experiment.experiment_id,
        district_id=district.district_id,
        mode="multi_seat_stv",
        max_rankings_allowed=3,
    )
    candidates = [
        Candidate(
            candidate_id="cand-a",
            election_id=election.election_id,
            profile={
                "ideology_score": 0.10,
                "party_id": "D",
                "home_region": "north",
                "community_tags": {"labor"},
                "issue_tags": {"housing", "climate"},
                "candidate_quality": 80.0,
            },
        ),
        Candidate(
            candidate_id="cand-b",
            election_id=election.election_id,
            profile={
                "ideology_score": -0.90,
                "party_id": "R",
                "home_region": "south",
                "community_tags": {"rural"},
                "issue_tags": {"public_safety"},
                "candidate_quality": 90.0,
            },
        ),
        Candidate(
            candidate_id="cand-c",
            election_id=election.election_id,
            profile={
                "ideology_score": 0.40,
                "party_id": "D",
                "home_region": "south",
                "community_tags": {"urban", "college_town"},
                "issue_tags": {"housing", "education"},
                "candidate_quality": 60.0,
            },
        ),
    ]
    elector_units = [
        ElectorUnit(
            elector_unit_id="block-central",
            election_id=election.election_id,
            size=1200,
            profile={
                "ideology_score": 0.20,
                "party_id": "D",
                "home_region": "north",
                "community_tags": {"labor", "urban"},
                "issue_tags": {"housing", "education"},
            },
        )
    ]
    preference_model = PreferenceModel(
        preference_model_id="pref-orchestration",
        experiment_id=experiment.experiment_id,
        name="workflow",
        temperature=1.0,
        active_attributes=STARTER_ACTIVE_ATTRIBUTES,
        attribute_weights=STARTER_ATTRIBUTE_WEIGHTS,
        missing_value_policy="ignore",
        ranking_method=ranking_method,  # type: ignore[arg-type]
    )
    generation_run = BallotGenerationRun(
        generation_run_id="run-orchestration",
        election_id=election.election_id,
        preference_model_id=preference_model.preference_model_id,
        random_seed=101,
    )

    return RepresentationalExperimentState(
        experiment=experiment,
        districts=[district],
        elections=[election],
        attribute_specs=get_starter_attribute_specs(STARTER_ACTIVE_ATTRIBUTES),
        candidates=candidates,
        elector_units=elector_units,
        preference_models=[preference_model],
        ballot_generation_runs=[generation_run],
    )


def test_run_representational_workflow_exports_deterministic_rankings(tmp_path: Path) -> None:
    state = _build_experiment_state(ranking_method="deterministic_sort")
    output_path = tmp_path / "deterministic_workflow.json"

    result = run_representational_workflow(
        state,
        RepresentationalWorkflowConfig(
            test_name="deterministic_workflow",
            output_path=output_path,
            tie_break_order=["cand-c", "cand-a", "cand-b"],
        ),
    )

    election_id, seat_count, mode, candidates, ballots, tie_break_order, max_ranks_allowed = (
        read_simulation_ready_json(result.output_path)
    )
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))

    assert election_id == "election-orchestration"
    assert seat_count == 3
    assert mode == "multi_seat_stv"
    assert tie_break_order == ["cand-c", "cand-a", "cand-b"]
    assert max_ranks_allowed == 3
    assert [candidate.candidate_id for candidate in candidates] == ["cand-a", "cand-b", "cand-c"]
    assert [group.candidate_ids[0] for group in ballots[0].rankings] == ["cand-a", "cand-c", "cand-b"]
    assert [group.rank for group in ballots[0].rankings] == [1, 2, 3]
    assert payload["metadata"]["max_rankings_allowed"] == 3
    assert result.ballots[0].rankings[0].candidate_ids == ["cand-a"]
    assert result.output_path == output_path


def test_run_representational_workflow_weighted_generation_is_reproducible(tmp_path: Path) -> None:
    state = _build_experiment_state(ranking_method="weighted_without_replacement")
    output_path = tmp_path / "weighted_workflow.json"

    config = RepresentationalWorkflowConfig(
        test_name="weighted_workflow",
        output_path=output_path,
        ballots_per_elector_unit=2,
    )

    result_one = run_representational_workflow(state, config)
    result_two = run_representational_workflow(state, config)

    assert result_one.ballots == result_two.ballots
    assert len(result_one.ballots) == 2
    assert len(result_one.ballots[0].rankings) == 3
    assert len({tuple(group.candidate_ids[0] for group in ballot.rankings) for ballot in result_one.ballots}) >= 1
    assert result_one.output_path.exists()
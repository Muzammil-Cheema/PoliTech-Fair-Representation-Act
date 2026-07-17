from __future__ import annotations

from dataclasses import dataclass
from math import exp
from pathlib import Path
from random import Random
from typing import Sequence

from Global_Utilities import resolve_pipe_path, write_simulation_ready_json

from .generation import generate_ballot
from .input_contract import RepresentationalExperimentState
from .models import Ballot, BallotGenerationRun, Candidate, ElectorUnit, Election, PreferenceModel, RankGroup, RankingMethod
from .scoring import score_candidates_for_elector_unit


@dataclass(frozen=True)
class RepresentationalWorkflowConfig:
    """Configuration for the public representational orchestration entrypoint."""

    test_name: str
    election_id: str | None = None
    preference_model_id: str | None = None
    ballot_generation_run_id: str | None = None
    ranking_method: RankingMethod | None = None
    ballots_per_elector_unit: int = 1
    tie_break_order: Sequence[str] | None = None
    output_path: str | Path | None = None
    project_root: Path | None = None


@dataclass(frozen=True)
class RepresentationalWorkflowResult:
    """Return value for the orchestration entrypoint."""

    output_path: Path
    candidates: list[Candidate]
    ballots: list[Ballot]
    metadata: dict[str, object]


def run_representational_workflow(
    state: RepresentationalExperimentState,
    config: RepresentationalWorkflowConfig,
) -> RepresentationalWorkflowResult:
    """Score, rank, generate ballots, and export simulation-ready JSON."""

    if config.ballots_per_elector_unit < 1:
        raise ValueError("ballots_per_elector_unit must be at least 1.")

    election, preference_model, generation_run = _resolve_workflow_subjects(state, config)
    ranking_method = config.ranking_method or preference_model.ranking_method
    candidates, elector_units = _resolve_workflow_population(state, election)

    ballots = _build_ballots_for_workflow(
        candidates=candidates,
        elector_units=elector_units,
        attribute_specs=state.attribute_specs,
        election=election,
        preference_model=preference_model,
        generation_run=generation_run,
        ranking_method=ranking_method,
        ballots_per_elector_unit=config.ballots_per_elector_unit,
    )
    metadata = _build_workflow_metadata(
        state=state,
        election=election,
        candidates=candidates,
        tie_break_order=config.tie_break_order,
    )
    output_path = _resolve_output_path(
        test_name=config.test_name,
        output_path=config.output_path,
        project_root=config.project_root,
    )
    write_simulation_ready_json(
        output_path=output_path,
        test_name=config.test_name,
        ballots=ballots,
        candidates=candidates,
        metadata=metadata,
    )
    return RepresentationalWorkflowResult(
        output_path=output_path,
        candidates=candidates,
        ballots=ballots,
        metadata=metadata,
    )


def _resolve_workflow_subjects(
    state: RepresentationalExperimentState,
    config: RepresentationalWorkflowConfig,
) -> tuple[Election, PreferenceModel, BallotGenerationRun]:
    return (
        _resolve_single_election(state, config.election_id),
        _resolve_preference_model(state, config.preference_model_id),
        _resolve_generation_run(state, config.ballot_generation_run_id),
    )


def _resolve_workflow_population(
    state: RepresentationalExperimentState,
    election: Election,
) -> tuple[list[Candidate], list[ElectorUnit]]:
    candidates = [
        candidate
        for candidate in state.candidates
        if candidate.election_id == election.election_id
    ]
    elector_units = [
        elector_unit
        for elector_unit in state.elector_units
        if elector_unit.election_id == election.election_id
    ]
    if not candidates:
        raise ValueError(f"No candidates found for election_id '{election.election_id}'.")
    if not elector_units:
        raise ValueError(f"No elector units found for election_id '{election.election_id}'.")
    return candidates, elector_units


def _resolve_single_election(
    state: RepresentationalExperimentState,
    election_id: str | None,
) -> Election:
    elections = state.elections
    if election_id is None:
        if len(elections) != 1:
            raise ValueError("election_id is required when the contract contains multiple elections.")
        return elections[0]

    for election in elections:
        if election.election_id == election_id:
            return election
    raise ValueError(f"Unknown election_id '{election_id}'.")


def _resolve_preference_model(
    state: RepresentationalExperimentState,
    preference_model_id: str | None,
) -> PreferenceModel:
    preference_models = state.preference_models
    if preference_model_id is None:
        if len(preference_models) != 1:
            raise ValueError(
                "preference_model_id is required when the contract contains multiple preference models."
            )
        return preference_models[0]

    for preference_model in preference_models:
        if preference_model.preference_model_id == preference_model_id:
            return preference_model
    raise ValueError(f"Unknown preference_model_id '{preference_model_id}'.")


def _resolve_generation_run(
    state: RepresentationalExperimentState,
    ballot_generation_run_id: str | None,
) -> BallotGenerationRun:
    generation_runs = state.ballot_generation_runs
    if ballot_generation_run_id is None:
        if len(generation_runs) != 1:
            raise ValueError(
                "ballot_generation_run_id is required when the contract contains multiple generation runs."
            )
        return generation_runs[0]

    for generation_run in generation_runs:
        if generation_run.generation_run_id == ballot_generation_run_id:
            return generation_run
    raise ValueError(f"Unknown ballot_generation_run_id '{ballot_generation_run_id}'.")


def _build_ballots_for_workflow(
    *,
    candidates: list[Candidate],
    elector_units: list[ElectorUnit],
    attribute_specs: list[object],
    election: Election,
    preference_model: PreferenceModel,
    generation_run: BallotGenerationRun,
    ranking_method: RankingMethod,
    ballots_per_elector_unit: int,
) -> list[Ballot]:
    ballots: list[Ballot] = []
    for elector_unit_index, elector_unit in enumerate(elector_units):
        candidate_scores = score_candidates_for_elector_unit(
            candidates=candidates,
            elector_unit=elector_unit,
            attribute_specs=attribute_specs,
            preference_model=preference_model,
        )
        ballots.extend(
            _build_ballots_for_elector_unit(
                candidate_scores=candidate_scores,
                candidates=candidates,
                elector_unit=elector_unit,
                election=election,
                generation_run=generation_run,
                preference_model=preference_model,
                ranking_method=ranking_method,
                ballots_per_elector_unit=ballots_per_elector_unit,
                elector_unit_index=elector_unit_index,
            )
        )
    return ballots


def _build_ballots_for_elector_unit(
    *,
    candidate_scores: dict[str, dict[str, object]],
    candidates: list[Candidate],
    elector_unit: ElectorUnit,
    election: Election,
    generation_run: BallotGenerationRun,
    preference_model: PreferenceModel,
    ranking_method: RankingMethod,
    ballots_per_elector_unit: int,
    elector_unit_index: int,
) -> list[Ballot]:
    ballots: list[Ballot] = []
    for ballot_index in range(ballots_per_elector_unit):
        ballot_id = _build_ballot_id(
            generation_run_id=generation_run.generation_run_id,
            elector_unit=elector_unit,
            elector_unit_index=elector_unit_index,
            ballot_index=ballot_index,
        )
        ballots.append(
            _build_ballot_for_method(
                ballot_id=ballot_id,
                candidate_scores=candidate_scores,
                candidates=candidates,
                elector_unit=elector_unit,
                election=election,
                generation_run=generation_run,
                preference_model=preference_model,
                ranking_method=ranking_method,
                ballot_index=ballot_index,
            )
        )
    return ballots


def _build_ballot_for_method(
    *,
    ballot_id: str,
    candidate_scores: dict[str, dict[str, object]],
    candidates: list[Candidate],
    elector_unit: ElectorUnit,
    election: Election,
    generation_run: BallotGenerationRun,
    preference_model: PreferenceModel,
    ranking_method: RankingMethod,
    ballot_index: int,
) -> Ballot:
    if ranking_method == "deterministic_sort":
        return Ballot(
            ballot_id=ballot_id,
            generation_run_id=generation_run.generation_run_id,
            source_elector_unit_id=elector_unit.elector_unit_id,
            rankings=_build_deterministic_rankings(
                candidate_scores=candidate_scores,
                max_ranks_allowed=election.max_rankings_allowed,
            ),
        )

    candidate_weights = _build_candidate_weights(
        candidate_scores=candidate_scores,
        ranking_method=ranking_method,
        temperature=preference_model.temperature,
    )
    rng = Random(
        f"{generation_run.random_seed or 0}:{election.election_id}:{elector_unit.elector_unit_id}:{ballot_index}"
    )
    ballot = generate_ballot(
        ballot_id=ballot_id,
        generation_run_id=generation_run.generation_run_id,
        source_elector_unit_id=elector_unit.elector_unit_id,
        candidates=candidates,
        candidate_probabilities=candidate_weights,
        rng=rng,
    )
    ballot.rankings = _truncate_rankings(
        ballot.rankings,
        election.max_rankings_allowed,
    )
    return ballot


def _build_workflow_metadata(
    *,
    state: RepresentationalExperimentState,
    election: Election,
    candidates: list[Candidate],
    tie_break_order: Sequence[str] | None,
) -> dict[str, object]:
    max_rankings_allowed = election.max_rankings_allowed
    # `max_ranks_allowed` is the canonical handoff key used by the simulation layer.
    # `max_rankings_allowed` is retained as a compatibility alias for older readers.
    return {
        "election_id": election.election_id,
        "seat_count": _seat_count_for_election(state, election.election_id),
        "mode": election.mode,
        "tie_break_order": list(tie_break_order or _default_tie_break_order(candidates)),
        "max_ranks_allowed": max_rankings_allowed,
        "max_rankings_allowed": max_rankings_allowed,
    }


def _seat_count_for_election(state: RepresentationalExperimentState, election_id: str) -> int:
    election = next(election for election in state.elections if election.election_id == election_id)
    district = next(district for district in state.districts if district.district_id == election.district_id)
    return district.seat_target


def _default_tie_break_order(candidates: Sequence[Candidate]) -> list[str]:
    return [candidate.candidate_id for candidate in sorted(candidates, key=lambda candidate: candidate.candidate_id)]


def _build_deterministic_rankings(
    *,
    candidate_scores: dict[str, dict[str, object]],
    max_ranks_allowed: int,
) -> list[RankGroup]:
    ordered_candidate_ids = [
        candidate_id
        for candidate_id, _ in sorted(
            candidate_scores.items(),
            key=lambda item: (-float(item[1]["final_score"]), item[0]),
        )
    ]
    if max_ranks_allowed > 0:
        ordered_candidate_ids = ordered_candidate_ids[:max_ranks_allowed]
    return [
        RankGroup(rank=index + 1, candidate_ids=[candidate_id])
        for index, candidate_id in enumerate(ordered_candidate_ids)
    ]


def _build_candidate_weights(
    *,
    candidate_scores: dict[str, dict[str, object]],
    ranking_method: RankingMethod,
    temperature: float,
) -> dict[str, float]:
    scores = {
        candidate_id: float(entry["final_score"])
        for candidate_id, entry in candidate_scores.items()
    }

    if ranking_method == "softmax_without_replacement":
        scale = temperature if temperature > 0 else 1.0
        return {
            candidate_id: exp(score / scale)
            for candidate_id, score in scores.items()
        }

    minimum_score = min(scores.values()) if scores else 0.0
    offset = abs(minimum_score) + 1.0
    return {
        candidate_id: score + offset
        for candidate_id, score in scores.items()
    }


def _truncate_rankings(rankings: list[RankGroup], max_ranks_allowed: int) -> list[RankGroup]:
    if max_ranks_allowed <= 0:
        return rankings
    return rankings[:max_ranks_allowed]


def _build_ballot_id(
    *,
    generation_run_id: str,
    elector_unit: ElectorUnit,
    elector_unit_index: int,
    ballot_index: int,
) -> str:
    return (
        f"{generation_run_id}-{elector_unit.elector_unit_id}-{elector_unit_index:04d}-{ballot_index:02d}"
    )


def _resolve_output_path(
    *,
    test_name: str,
    output_path: str | Path | None,
    project_root: Path | None,
) -> Path:
    if output_path is not None:
        return Path(output_path)
    return resolve_pipe_path(f"{test_name}_output.json", project_root=project_root)
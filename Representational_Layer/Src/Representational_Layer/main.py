from __future__ import annotations

from dataclasses import dataclass
import random
from pathlib import Path

from .generation import generate_ballots_from_scores
from .input_contract import load_experiment_contract
from .models import Ballot, Candidate
from .scoring import score_candidates_for_elector_unit
from ..output_writer import write_simulation_ready_output


@dataclass(frozen=True)
class RepresentationalWorkflowResult:
    candidates: list[Candidate]
    ballots: list[Ballot]
    output_path: Path


def run_representational_workflow(
    contract_path: str | Path,
    generation_run_id: str | None = None,
    output_path: str | Path | None = None,
    project_root: Path | None = None,
) -> RepresentationalWorkflowResult:
    """Run the complete representational workflow from a JSON contract.

    This function strictly honors the provided input contract. It determines which
    generation run to execute, resolves the correct election, models, and candidates,
    scores those candidates, generates ballots according to elector unit sizes,
    and writes simulation-ready output.
    """
    state = load_experiment_contract(contract_path)

    # Enforce run execution policy
    if generation_run_id is None:
        if len(state.ballot_generation_runs) == 1:
            run = state.ballot_generation_runs[0]
        elif len(state.ballot_generation_runs) == 0:
            raise ValueError("Input contract has no ballot generation runs.")
        else:
            raise ValueError(
                "Input contract contains multiple generation runs. "
                "You must specify generation_run_id explicitly."
            )
    else:
        runs = [r for r in state.ballot_generation_runs if r.generation_run_id == generation_run_id]
        if not runs:
            raise ValueError(f"Generation run '{generation_run_id}' not found in contract.")
        run = runs[0]

    # Resolve linked objects
    elections = [e for e in state.elections if e.election_id == run.election_id]
    if not elections:
        raise ValueError(f"Election '{run.election_id}' not found.")
    election = elections[0]

    districts = [d for d in state.districts if d.district_id == election.district_id]
    if not districts:
        raise ValueError(f"District '{election.district_id}' not found.")
    district = districts[0]

    pref_models = [p for p in state.preference_models if p.preference_model_id == run.preference_model_id]
    if not pref_models:
        raise ValueError(f"Preference model '{run.preference_model_id}' not found.")
    preference_model = pref_models[0]

    candidates = [c for c in state.candidates if c.election_id == election.election_id and not c.withdrawn]
    elector_units = [u for u in state.elector_units if u.election_id == election.election_id]

    rng = random.Random(run.random_seed)
    
    # Generate ballots
    ballots: list[Ballot] = []
    for unit in elector_units:
        scores = score_candidates_for_elector_unit(
            candidates=candidates,
            elector_unit=unit,
            attribute_specs=state.attribute_specs,
            preference_model=preference_model,
        )
        
        unit_ballots = generate_ballots_from_scores(
            generation_run_id=run.generation_run_id,
            source_elector_unit_id=unit.elector_unit_id,
            candidates=candidates,
            candidate_scores=scores,
            ranking_method=preference_model.ranking_method,
            temperature=preference_model.temperature,
            count=unit.size,
            rng=rng,
        )
        ballots.extend(unit_ballots)
        
    # Truncate ranks based on election rules
    if election.max_rankings_allowed > 0:
        for ballot in ballots:
            ballot.rankings = ballot.rankings[:election.max_rankings_allowed]

    # Prepare simulation metadata
    # Use deterministic alphabetical tie-break order if none provided by the model
    tie_break_order = sorted([c.candidate_id for c in candidates])

    metadata = {
        "election_id": election.election_id,
        "seat_count": district.seat_target,
        "mode": election.mode,
        "max_ranks_allowed": election.max_rankings_allowed,
        "tie_break_order": tie_break_order,
    }

    test_name = run.generation_run_id
    from Global_Utilities import write_simulation_ready_json
    
    if output_path is not None:
        final_output_path = Path(output_path)
        write_simulation_ready_json(
            output_path=final_output_path,
            test_name=test_name,
            ballots=ballots,
            candidates=candidates,
            metadata=metadata,
        )
        return RepresentationalWorkflowResult(
            candidates=candidates,
            ballots=ballots,
            output_path=final_output_path,
        )
    else:
        final_output_path = write_simulation_ready_output(
            test_name=test_name,
            ballots=ballots,
            candidates=candidates,
            metadata=metadata,
            project_root=project_root,
        )
        return RepresentationalWorkflowResult(
            candidates=candidates,
            ballots=ballots,
            output_path=final_output_path,
        )

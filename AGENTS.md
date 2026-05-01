# AGENTS.md

## IMPORTANT
This file must be updated after **every LLM-authored code change** so the documentation and source remain aligned.

## Core Rules For Agents

1. Keep representational logic and simulation logic separate.
2. Use shared JSON I/O helpers, not ad-hoc serializers:
   - `global_utilities.write_simulation_ready_json(...)`
   - `global_utilities.read_simulation_ready_json(...)`
   - `global_utilities.resolve_pipe_path(...)`
3. Use logging wrappers for runtime messages:
   - `global_utilities.info(...)`
   - `global_utilities.warn(...)`
   - `global_utilities.success(...)`
   - `global_utilities.error(...)`
4. Avoid direct `print(...)` in reusable modules.
5. Keep ballots in rank-group form (`rank`, `candidate_ids`) for FRA edge-case compatibility.
6. Preserve deterministic metadata when exporting to simulation (`election_id`, `seat_count`, `mode`, `tie_break_order`, optional rank cap fields).
7. Reuse existing models and helpers. Do not duplicate models in new files.

## Commit Message Convention

- Use `feat: <message>` for feature work.
- Use `fix: <message>` for bug fixes.
- Use `refactor: <message>` for refactoring-only changes.

## Environment Variables

### Required by source code

- None currently required by runtime source files.

### Common workflow variables

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`
  - Recommended for stable local test execution.
- `PYTHONPATH=.:src`
  - Useful when running scripts directly from `Representational Layer/`.

## Layer Boundary Contract

- Representational layer outputs:
  - Candidate objects
  - Rank-preserving ballot objects
  - Metadata needed by simulation
- Simulation layer inputs:
  - Election metadata + candidates + ballots + tie-break order
- Simulation layer must remain agnostic to representational profile semantics.

## Directory Breakdown

### Repository root
- `Getting_Started.md`: human-oriented onboarding and workflow.
- `AGENTS.md`: agent operating manual (this file).
- `attributes/`: shared representational attribute vocabulary and defaults.
- `global_utilities/`: shared logger and JSON contract helpers used across layers.
- `pipe/`: simulation handoff JSON inputs and acceptance fixtures.
- `Representational Layer/`: representational package, tests, and outputs.
- `Simulation Layer/`: FRA counting engine package.

### `attributes/`
- `attributes/__init__.py`
  - Exports starter attribute specs and defaults.
- `attributes/starter_attributes.py`
  - Constants:
    - `STARTER_SIX_ATTRIBUTE_SPECS`
    - `STARTER_ACTIVE_ATTRIBUTES`
    - `STARTER_ATTRIBUTE_WEIGHTS`
  - Function:
    - `get_starter_attribute_specs(names: list[str] | None) -> list[AttributeSpec]`

### `global_utilities/`
- `global_utilities/__init__.py`
  - Re-exports logging and lazily exposes JSON I/O helpers.
- `global_utilities/logger.py`
  - `_log(color, tag, symbol, message)`
  - `info(message)`
  - `warn(message)`
  - `success(message)`
  - `error(message)` (terminates process)
  - Global constants:
    - `RESET`
    - `BLUE`
    - `GREEN`
    - `RED`
    - `YELLOW`
- `global_utilities/json_io.py`
  - Types:
    - `SimulationJsonMetadata`
    - `SimulationJsonObjects`
    - `RepresentationCandidate` protocol
    - `RepresentationRankGroup` protocol
    - `RepresentationBallot` protocol
  - Constants:
    - `PROJECT_ROOT`
    - `SIMULATION_ROOT`
    - `PIPE_DIR_NAME`
  - Functions:
    - `resolve_pipe_path(path, project_root=None) -> Path`
    - `_to_json_compatible(value) -> Any`
    - `_get_metadata_value(data, metadata, field_name) -> Any`
    - `_get_max_ranks_allowed(data, metadata) -> int | None`
    - `write_simulation_ready_json(output_path, test_name, ballots, candidates, metadata) -> Path`
    - `read_simulation_ready_json(path) -> SimulationJsonObjects`

### `Representational Layer/`
- `Representational Layer/README.md`: package summary and quick start.
- `Representational Layer/pyproject.toml`: build/test config.
- `Representational Layer/src/output_writer.py`
  - `write_simulation_ready_output(test_name, ballots, candidates, metadata, project_root=None) -> Path`
  - Wraps global JSON helper and writes to `pipe/`.
- `Representational Layer/src/representational_layer/__init__.py`
  - Public exports for models, generation, and scoring.
- `Representational Layer/src/representational_layer/models.py`
  - Dataclasses:
    - `Experiment`
    - `District`
    - `Election`
    - `AttributeSpec`
    - `Candidate`
    - `ElectorUnit`
    - `PreferenceModel`
    - `BallotGenerationRun`
    - `RankGroup`
    - `Ballot`
  - Type aliases/literals:
    - `Profile`, `Parameters`, `ElectionMode`, `AttributeType`, `ComparisonMode`, `ScoreStyle`, `MissingValuePolicy`, `RankingMethod`
- `Representational Layer/src/representational_layer/scoring.py`
  - Public function:
    - `score_candidates_for_elector_unit(candidates, elector_unit, attribute_specs, preference_model) -> CandidateScores`
  - Internal helpers:
    - `_compute_attribute_score(...)`
    - `_numeric_similarity_score(...)`
    - `_set_overlap_score(...)`
    - `_candidate_effect_score(...)`
    - `_custom_score(...)`
    - `_resolve_missing_score(...)`
    - `_apply_score_style(...)`
    - `_to_float(...)`
    - `_to_set(...)`
    - `_clamp(...)`
- `Representational Layer/src/representational_layer/generation.py`
  - `generate_weighted_ballot_ranking(candidates, candidate_probabilities, rng) -> list[RankGroup]`
  - `generate_ballot(ballot_id, generation_run_id, source_elector_unit_id, candidates, candidate_probabilities, rng) -> Ballot`

### `Representational Layer/tests/`
- `test_models.py`
  - Smoke tests for baseline representational graph and weighted ranking generator.
- `test_scoring.py`
  - Attribute-score normalization and missing-value weighting behavior.
- `test_profile_based_ballot_generation.py`
  - Deterministic profile-based ranking tests and larger multi-elector-unit batch test.
  - Uses `write_simulation_ready_output(...)` to export test outputs.
- `test_json_io.py`
  - Contract test from representational objects -> simulation typed objects via global JSON helpers.

### `Simulation Layer/`
- `Simulation Layer/fra_engine.py`
  - Compatibility shim and re-exports:
    - `Ballot`, `Candidate`, `Election`, `Mode`, `Ranking`
    - `load_election_from_json`, `run_election`, `run_multi_seat_stv`, `run_single_seat_rcv`, `run_cli`
- `Simulation Layer/core/config.py`
  - Global constants:
    - `MODE_SINGLE_SEAT_RCV`
    - `MODE_MULTI_SEAT_STV`
    - `VALID_MODES`
    - `DEFAULT_TRANSFER_VALUE`
    - `DEFAULT_ENCODING`
- `Simulation Layer/core/models.py`
  - Dataclasses:
    - `Candidate`, `Ranking`, `Ballot`, `Election`
  - `Election.__post_init__` enforces core validation constraints.
- `Simulation Layer/helpers/edge_cases.py`
  - `is_undervote(ballot)`
  - `sorted_rankings(ballot)`
  - `highest_ranked_active(ballot, active_candidate_ids)`
- `Simulation Layer/helpers/utils.py`
  - Candidate/state helpers:
    - `initial_candidate_status(election)`
    - `active_candidates(status)`
    - `elected_candidates(status)`
    - `tie_break(tied_ids, tie_break_order)`
    - `add_winner(status, candidate_id)`
    - `eliminate_candidate(status, candidate_id)`
  - Math/round helpers:
    - `compute_threshold(first_round_total, seat_count)`
    - `truncate_4(value)`
    - `append_round(rounds, election, status, totals, action, include_threshold)`
    - `count_votes_single_round(election, status, use_transfer_values)`
    - `apply_threshold_to_elected(totals, status, threshold)`
    - `distribute_surplus_transfer_values(election, elected_candidate_id, surplus_fraction)`
- `Simulation Layer/runner/main.py`
  - Global constants:
    - `PROJECT_ROOT`
  - `run_single_seat_rcv(election) -> Dict`
  - `run_multi_seat_stv(election) -> Dict`
  - `run_election(election) -> Dict`
  - `load_election_from_json(path) -> Election`
  - `run_cli() -> None`

### `pipe/`
- `pipe/input.json`: manual/CLI handoff entry path.
- `pipe/acceptance_test_cases/*.json`: canonical simulation acceptance inputs.
- `pipe/test_*_output.json`: representational test exports in simulation-ready form.

## Global Constants Inventory

- `global_utilities/json_io.py`
  - `PROJECT_ROOT`, `SIMULATION_ROOT`, `PIPE_DIR_NAME`
- `global_utilities/logger.py`
  - `RESET`, `BLUE`, `GREEN`, `RED`, `YELLOW`
- `Simulation Layer/core/config.py`
  - `MODE_SINGLE_SEAT_RCV`, `MODE_MULTI_SEAT_STV`, `VALID_MODES`, `DEFAULT_TRANSFER_VALUE`, `DEFAULT_ENCODING`
- `Simulation Layer/fra_engine.py`
  - `SIMULATION_ROOT`, `PROJECT_ROOT`
- `Simulation Layer/runner/main.py`
  - `PROJECT_ROOT`
- `Representational Layer/src/output_writer.py`
  - `PROJECT_ROOT`
- Test-only globals:
  - `Representational Layer/tests/test_json_io.py`: `PROJECT_ROOT`
  - `Simulation Layer/tests/test_acceptance_e2e.py`: `PROJECT_ROOT`, `SIMULATION_ROOT`, `CASE_DIR`

## Complete Model/Class Inventory

### Representational layer classes

- `Experiment`
- `District`
- `Election`
- `AttributeSpec`
- `Candidate`
- `ElectorUnit`
- `PreferenceModel`
- `BallotGenerationRun`
- `RankGroup`
- `Ballot`

### Simulation layer classes

- `Candidate`
- `Ranking`
- `Ballot`
- `Election`

### Shared JSON-contract classes/types

- `SimulationJsonMetadata` (`TypedDict`)
- `RepresentationCandidate` (`Protocol`)
- `RepresentationRankGroup` (`Protocol`)
- `RepresentationBallot` (`Protocol`)

## Required Agent Workflow For JSON Handoffs

1. Build representational candidates/ballots using existing models and scoring helpers.
2. Call `write_simulation_ready_output(...)` (or `write_simulation_ready_json(...)` directly when needed).
3. Ensure metadata includes:
   - `election_id`
   - `seat_count`
   - `mode`
   - `tie_break_order`
   - optional `max_ranks_allowed` or `max_rankings_allowed`
4. Read/validate using `read_simulation_ready_json(...)` when testing round-trip compatibility.

## Change Management Rules For Agents

- If you add/rename/move a function, update this file immediately.
- If you add a new directory/file, add it to the directory breakdown.
- If you modify JSON contract fields, update the "Required Agent Workflow For JSON Handoffs" section.
- If you change logging conventions, update the "Core Rules For Agents" section.

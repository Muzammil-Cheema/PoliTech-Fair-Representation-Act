# AGENTS.md

## IMPORTANT
This file must be updated after **every LLM-authored code change** so the documentation and source remain aligned.

## Core Rules For Agents

1. Keep representational logic and simulation logic separate.
2. Use shared JSON I/O helpers, not ad-hoc serializers:
   - `Global_Utilities.write_simulation_ready_json(...)`
   - `Global_Utilities.read_simulation_ready_json(...)`
   - `Global_Utilities.resolve_pipe_path(...)`
3. Use logging wrappers for runtime messages:
   - `Global_Utilities.info(...)`
   - `Global_Utilities.warn(...)`
   - `Global_Utilities.success(...)`
   - `Global_Utilities.error(...)`
4. Avoid direct `print(...)` in reusable modules.
5. Keep ballots in rank-group form (`rank`, `candidate_ids`) for FRA edge-case compatibility.
6. Preserve deterministic metadata when exporting to simulation (`election_id`, `seat_count`, `mode`, `tie_break_order`, optional rank cap fields).
7. Reuse existing models and helpers. Do not duplicate models in new files.

## Naming Convention

- Do not use spaces in project-owned file or directory names; use underscores instead.
- Directory names use capitalized words separated by underscores, for example `Representational_Layer/` and `Global_Utilities/`.
- File names use lowercase words separated by underscores, for example `test_acceptance_e2e.py`.
- Keep conventional repository files such as `AGENTS.md` and `README.md` as exceptions when the toolchain expects those exact names.

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
- `PYTHONPATH=.:Src`
  - Useful when running scripts directly from `Representational_Layer/`.

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
- `README.md`: human-oriented onboarding and workflow.
- `AGENTS.md`: agent operating manual (this file).
- `Global_Utilities/`: shared logger and JSON contract helpers used across layers.
- `Pipe/`: simulation handoff JSON inputs and acceptance fixtures.
- `Representational_Layer/`: representational package, tests, and outputs.
- `Simulation_Layer/`: FRA counting engine package.

### `Representational_Layer/Attributes/`
- `Representational_Layer/Attributes/__init__.py`
  - Exports starter attribute specs and defaults.
- `Representational_Layer/Attributes/starter_attributes.py`
  - Constants:
    - `STARTER_SIX_ATTRIBUTE_SPECS`
    - `STARTER_ACTIVE_ATTRIBUTES`
    - `STARTER_ATTRIBUTE_WEIGHTS`
  - Function:
    - `get_starter_attribute_specs(names: list[str] | None) -> list[AttributeSpec]`

### `Global_Utilities/`
- `Global_Utilities/__init__.py`
  - Re-exports logging and lazily exposes JSON I/O helpers.
- `Global_Utilities/logger.py`
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
- `Global_Utilities/json_io.py`
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

### `Representational_Layer/`
- `Representational_Layer/README.md`: package summary and quick start.
- Root `pyproject.toml`: build/test config for representation and simulation layers.
- `Representational_Layer/Src/output_writer.py`
  - `write_simulation_ready_output(test_name, ballots, candidates, metadata, project_root=None) -> Path`
  - Wraps global JSON helper and writes to `Pipe/`.
- `Representational_Layer/Src/Representational_Layer/__init__.py`
  - Public exports for models, generation, and scoring.
- `Representational_Layer/Src/Representational_Layer/models.py`
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
- `Representational_Layer/Src/Representational_Layer/scoring.py`
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
- `Representational_Layer/Src/Representational_Layer/generation.py`
  - `generate_weighted_ballot_ranking(candidates, candidate_probabilities, rng) -> list[RankGroup]`
  - `generate_ballot(ballot_id, generation_run_id, source_elector_unit_id, candidates, candidate_probabilities, rng) -> Ballot`

### `Representational_Layer/Tests/`
- `test_models.py`
  - Smoke tests for baseline representational graph and weighted ranking generator.
- `test_scoring.py`
  - Attribute-score normalization and missing-value weighting behavior.
- `test_profile_based_ballot_generation.py`
  - Deterministic profile-based ranking tests and larger multi-elector-unit batch test.
  - Uses `write_simulation_ready_output(...)` to export test outputs.
- `test_json_io.py`
  - Contract test from representational objects -> simulation typed objects via global JSON helpers.

### `Simulation_Layer/`
- `Simulation_Layer/fra_engine.py`
  - Compatibility shim and re-exports:
    - `Ballot`, `Candidate`, `Election`, `Mode`, `Ranking`
    - `load_election_from_json`, `run_election`, `run_multi_seat_stv`, `run_single_seat_rcv`, `run_cli`
- `Simulation_Layer/Core/config.py`
  - Global constants:
    - `MODE_SINGLE_SEAT_RCV`
    - `MODE_MULTI_SEAT_STV`
    - `VALID_MODES`
    - `DEFAULT_TRANSFER_VALUE`
    - `DEFAULT_ENCODING`
- `Simulation_Layer/Core/models.py`
  - Dataclasses:
    - `Candidate`, `Ranking`, `Ballot`, `Election`
  - `Election.__post_init__` enforces core validation constraints.
- `Simulation_Layer/Helpers/edge_cases.py`
  - `is_undervote(ballot)`
  - `sorted_rankings(ballot)`
  - `highest_ranked_active(ballot, active_candidate_ids)`
- `Simulation_Layer/Helpers/utils.py`
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
- `Simulation_Layer/Runner/main.py`
  - Global constants:
    - `PROJECT_ROOT`
  - `run_single_seat_rcv(election) -> Dict`
  - `run_multi_seat_stv(election) -> Dict`
  - `run_election(election) -> Dict`
  - `load_election_from_json(path) -> Election`
  - `run_cli() -> None`
- `Simulation_Layer/Tests/test_acceptance_e2e.py`
  - Asserts canonical acceptance-case outcomes.
  - Recursively discovers runnable JSON files under `Pipe/` and verifies each completes through the simulation engine.

### `Pipe/`
- `Pipe/input.json`: manual/CLI handoff entry path.
- `Pipe/Acceptance_Test_Cases/*.json`: canonical simulation acceptance inputs.
- `Pipe/test_*_output.json`: representational test exports in simulation-ready form.

## Global Constants Inventory

- `Global_Utilities/json_io.py`
  - `PROJECT_ROOT`, `SIMULATION_ROOT`, `PIPE_DIR_NAME`
- `Global_Utilities/logger.py`
  - `RESET`, `BLUE`, `GREEN`, `RED`, `YELLOW`
- `Simulation_Layer/Core/config.py`
  - `MODE_SINGLE_SEAT_RCV`, `MODE_MULTI_SEAT_STV`, `VALID_MODES`, `DEFAULT_TRANSFER_VALUE`, `DEFAULT_ENCODING`
- `Simulation_Layer/fra_engine.py`
  - `SIMULATION_ROOT`, `PROJECT_ROOT`
- `Simulation_Layer/Runner/main.py`
  - `PROJECT_ROOT`
- `Representational_Layer/Src/output_writer.py`
  - `PROJECT_ROOT`
- Test-only globals:
  - `Representational_Layer/Tests/test_json_io.py`: `PROJECT_ROOT`
  - `Simulation_Layer/Tests/test_acceptance_e2e.py`: `PROJECT_ROOT`, `SIMULATION_ROOT`, `CASE_DIR`

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

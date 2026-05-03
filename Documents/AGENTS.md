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
6. Preserve deterministic metadata when exporting to simulation (`election_id`, `seat_count`, `mode`, `tie_break_order`, optional rank cap fields). `tie_break_order` is an elimination priority: if tied candidates appear as `[A, B]`, `A` is eliminated before `B`.
7. Reuse existing models and helpers. Do not duplicate models in new files.
8. Keep MMD generation, representational ballot generation, and simulation counting separate unless a task explicitly asks for integration.
9. Treat current MMD outputs as district-generation artifacts, not simulation-ready election JSON.

## Naming Convention

- Do not use spaces in project-owned file or directory names; use underscores instead.
- Directory names use capitalized words separated by underscores, for example `Representational_Layer/` and `Global_Utilities/`.
- File names use lowercase words separated by underscores, for example `test_acceptance_e2e.py`.
- Keep conventional repository files such as `AGENTS.md` and `README.md` as exceptions when the toolchain expects those exact names. In this repo those top-level files are compatibility symlinks into `Documents/`.

## Commit Message Convention

- Use `feat: <message>` for feature work.
- Use `fix: <message>` for bug fixes.
- Use `refactor: <message>` for refactoring-only changes.
- Use `test: <message>` for testing changes, adding or removing tests, running tests, and sharing test results.

## Git Workflow Rule

- Continue working on `main` by default.
- Do not create or switch to a new Git branch unless the user explicitly asks for one.

## Environment Variables

### Required by source code

- None currently required by runtime source files.

### Common workflow variables

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`
  - Recommended for stable local test execution.
- `PYTHONPATH=.:Src`
  - Useful when running scripts directly from `Representational_Layer/`.
- `PYTHONPATH=.:MMD_Generation_Layer`
  - Useful when running MMD scripts directly from the repository root.

## Common Commands

- `source .venv/bin/activate`
  - Activate the root virtual environment.
- `python -m pip install -e '.[dev]'`
  - Install the repo in editable mode with pytest.
- `python -m pip install -e '.[mmd]'`
  - Install MMD geospatial, notebook, and Streamlit dependencies.
- `jupyter notebook MMD_Generation_Layer/Processor/main.ipynb`
  - Open the MMD notebook workflow.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`
  - Run all configured tests from the repository root.
- `python Simulation_Layer/fra_engine.py`
  - Run the simulation CLI compatibility shim. This is an interactive/manual flow that prompts for an input JSON path and prints winners, final candidate status, and round details to the terminal.
- `python Simulation_Layer/Runner/main.py`
  - Run the simulation layer's direct CLI entrypoint with the same manual terminal-output behavior as `fra_engine.py`.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q Simulation_Layer/Tests/test_acceptance_e2e.py`
  - Run the simulation acceptance tests. This validates expected outcomes and normally stays quiet unless a case fails; do not expect the same report-style terminal output as the manual CLI.
- `python Simulation_Layer/Tests/run_acceptance_cli.py`
  - Run every canonical acceptance case through the CLI transcript path and validate printed winners against the fixture-derived oracle.
- `streamlit run MMD_Generation_Layer/Client/baseline_dashboard.py`
  - Open the MMD baseline dashboard.

## Layer Boundary Contract

- Representational layer outputs:
  - Candidate objects
  - Rank-preserving ballot objects
  - Metadata needed by simulation
- MMD generation layer outputs:
  - District-plan assignment JSON files
  - Ensemble summary CSV files
  - Map and histogram visualizations
- Simulation layer inputs:
  - Election metadata + candidates + ballots + tie-break order
- MMD outputs are not yet consumed directly by the simulation layer.
- Simulation layer must remain agnostic to representational profile semantics.

## Directory Breakdown

### Repository root
- `README.md`: compatibility symlink to `Documents/README.md` for tooling and package metadata.
- `AGENTS.md`: compatibility symlink to `Documents/AGENTS.md` for agent/tooling discovery.
- `Documents/`: dedicated home for project markdown and handoff documentation.
- `pyproject.toml`: shared package, editable-install, optional dependency, Python path, and pytest configuration for all layers.
  - Extras:
    - `dev`: pytest.
    - `mmd`: geospatial, notebook, GerryChain, and Streamlit dependencies.
  - Explicit package mappings include `Representational_Layer`, `Attributes`, `Simulation_Layer`, `Core`, `Helpers`, `Runner`, `Global_Utilities`, and `MMD_Generation_Layer`.
- `MMD_Generation_Layer/`: copied district-generation layer for geographic district-plan ensembles and dashboarding.
- `Global_Utilities/`: shared logger and JSON contract helpers used across layers.
- `Pipe/`: simulation handoff JSON inputs and acceptance fixtures.
- `Representational_Layer/`: representational package, tests, and outputs.
- `Simulation_Layer/`: FRA counting engine package.

### `Documents/`
- `Documents/README.md`: human-oriented onboarding and workflow.
- `Documents/AGENTS.md`: agent operating manual (this file), exposed at the repo root through `AGENTS.md`.
- `Documents/Thread_Handoff/Documents_Thread.md`: handoff for the documentation/questioning thread.
- `Documents/Thread_Handoff/Git_Thread.md`: handoff for the Git-focused support thread.
- `Documents/Thread_Handoff/Global_Thread.md`: handoff for the shared-infrastructure/global thread.
- `Documents/Thread_Handoff/MMD_Thread.md`: handoff for the MMD-generation thread.
- `Documents/Thread_Handoff/Simulation_Thread.md`: handoff for the simulation-layer implementation/debugging thread.
- `Documents/Thread_Handoff/Testing_Thread.md`: handoff for the testing-focused support thread.

### `MMD_Generation_Layer/`
- Purpose:
  - Generates and visualizes baseline district-plan ensembles from geographic data.
  - Currently uses equal-population district targets across districts.
  - Does not yet generate FRA-ready proportional-population multimember districts by seat count.
- `MMD_Generation_Layer/config.py`
  - Directories and paths:
    - `base_dir`
    - `processor_dir`
    - `shape_path`
    - `output_dir`
    - `plans_dir`
    - `ensemble_csv_path`
    - `seat_share_png_path`
  - Global constants:
    - `NUM_PLANS`
    - `NUM_DISTRICTS`
    - `ID_COLUMN`
    - `GEOM_COLUMN`
    - `SEED`
- `MMD_Generation_Layer/Data/Shapefiles/NC/`
  - North Carolina shapefile sidecar files:
    - `nc_2024_with_population.shp`
    - `nc_2024_with_population.shx`
    - `nc_2024_with_population.dbf`
    - `nc_2024_with_population.prj`
    - `nc_2024_with_population.cpg`
- `MMD_Generation_Layer/__init__.py`
  - Package marker for the MMD generation layer.
- `MMD_Generation_Layer/Processor/main.ipynb`
  - Notebook-driven GerryChain/ReCom pipeline.
  - Defines notebook-local functions:
    - `load_and_build_graph(shape_path=shape_path, id_col=ID_COLUMN, geom_col=GEOM_COLUMN)`
    - `create_initial_partition(graph, num_districts=NUM_DISTRICTS, seed=SEED)`
    - `generate_baseline_ensemble(graph, num_plans=NUM_PLANS, num_districts=NUM_DISTRICTS, seed=42)`
    - `save_results(ensemble, output_dir)`
    - `generate_district_csvs()`
    - `plot_baseline_histogram(csv_path, output_dir)`
- `MMD_Generation_Layer/Client/baseline_dashboard.py`
  - Streamlit dashboard for existing baseline outputs.
  - Functions:
    - `load_ensemble_results(csv_path: str) -> pd.DataFrame`
    - `load_shapefile(shape_path: str, id_col: str = ID_COLUMN) -> gpd.GeoDataFrame`
    - `load_plan_assignment(plan_id: int, plans_dir: Path) -> dict[str, int] | None`
    - `create_district_map(...)`
    - `plot_baseline_histogram(results_df: pd.DataFrame, output_dir: Path)`
    - `main()`
- `MMD_Generation_Layer/Outputs/`
  - `baseline_ensemble.csv`: summary rows with `plan_id`, `dem_seats`, `rep_seats`, and `dem_seat_share`.
  - `seat_share.png`: notebook-generated Democratic seat-share histogram.
  - `democratic_seats.png`: dashboard-generated Democratic seat-count histogram.
  - `Plan_Assignments/plan_*.json`: precinct ID to district ID assignment maps.

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
    - `BLUE` (used for bright cyan `info(...)` output)
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
    - `PIPE_DIR_NAME`
  - Functions:
    - `resolve_pipe_path(path, project_root=None) -> Path`
      - Accepts bare relative names like `input.json` and already-prefixed relative paths like `Pipe/input.json`.
    - `_to_json_compatible(value) -> Any`
    - `_get_metadata_value(data, metadata, field_name) -> Any`
    - `_get_max_ranks_allowed(data, metadata) -> int | None`
    - `write_simulation_ready_json(output_path, test_name, ballots, candidates, metadata) -> Path`
    - `read_simulation_ready_json(path) -> SimulationJsonObjects`

### `Representational_Layer/`
- `Representational_Layer/__init__.py`: public facade re-exporting `Representational_Layer/Src/Representational_Layer`.
- `Representational_Layer/models.py`: compatibility wrapper for `Representational_Layer/Src/Representational_Layer/models.py`.
- `Representational_Layer/generation.py`: compatibility wrapper for `Representational_Layer/Src/Representational_Layer/generation.py`.
- `Representational_Layer/scoring.py`: compatibility wrapper for `Representational_Layer/Src/Representational_Layer/scoring.py`.
- Root `pyproject.toml`: build/test config for all layers.
- `Representational_Layer/Attributes/`: shared representational attribute vocabulary and defaults.
- `Representational_Layer/Outputs/`: local/debug JSON exports generated by representational tests for inspection.
- `Representational_Layer/Tests/`: representational-layer pytest suite.
- `Representational_Layer/Src/__init__.py`: source package container marker.
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
  - Covers `resolve_pipe_path(...)` behavior for both bare relative paths and `Pipe/...` relative paths.

### `Simulation_Layer/`
- Source functions in `Core`, `Helpers`, and `Runner` now include descriptive docstrings that document behavior, parameters, and return values.
- `Simulation_Layer/fra_engine.py`
  - Global constants:
    - `PROJECT_ROOT`
  - Compatibility shim and re-exports:
    - `Ballot`, `Candidate`, `Election`, `Mode`, `Ranking`
    - `load_election_from_json`, `run_election`, `run_multi_seat_stv`, `run_single_seat_rcv`, `run_cli`
  - Bootstraps the repo root onto `sys.path` for direct file execution from the repository root.
- `Simulation_Layer/__init__.py`
  - Simulation-layer package marker.
- `Simulation_Layer/Core/config.py`
  - Global constants:
    - `MODE_SINGLE_SEAT_RCV`
    - `MODE_MULTI_SEAT_STV`
    - `VALID_MODES`
    - `DEFAULT_TRANSFER_VALUE`
    - `DEFAULT_ENCODING`
- `Simulation_Layer/Core/models.py`
  - Type aliases/literals:
    - `Mode`, `BallotState`
  - Dataclasses:
    - `Candidate`, `Ranking`, `Ballot`, `Election`
  - `Ballot.state` tracks persistent ballot activity (`active` or `inactive`) during a tabulation run.
  - `Election.__post_init__` enforces core validation constraints.
- `Simulation_Layer/Core/__init__.py`
  - Re-exports simulation config constants and core model classes.
- `Simulation_Layer/Helpers/edge_cases.py`
  - `is_undervote(ballot)`
  - `sorted_rankings(ballot)`
  - `highest_ranked_active(ballot, active_candidate_ids)`
  - `highest_ranked_active(...)` only resolves the current-round assignment; persistent inactivity is applied in counting utilities.
- `Simulation_Layer/Helpers/__init__.py`
  - Re-exports edge-case helpers and count utility helpers.
- `Simulation_Layer/Helpers/utils.py`
  - Candidate/state helpers:
    - `initial_candidate_status(candidates)`
    - `active_candidates(status)`
    - `elected_candidates(status)`
    - `tie_break(tied_ids, tie_break_order)`
    - `add_winner(status, candidate_id)`
    - `eliminate_candidate(status, candidate_id)`
  - Math/round helpers:
    - `compute_threshold(first_round_total, seat_count)`
    - `truncate_4(value)`
    - `append_round(rounds, round_number, threshold, status, totals, action, include_threshold, ballot_allocations=None)`
    - `count_votes_single_round(ballots, status, use_transfer_values, transfer_values_by_ballot_id=None) -> tuple[totals, ballot_allocations]`
      - Ballots that are already `inactive` are skipped in all future rounds.
      - Ballots that cannot resolve to a candidate in a round are marked `inactive` and remain inactive for the rest of the run.
    - `apply_threshold_to_elected(totals, status, threshold)`
    - `build_surplus_fractions(elected_candidate_ids, totals, threshold)`
    - `apply_simultaneous_surplus_transfer_values(ballots, round_ballot_allocations, surplus_fractions, transfer_values_by_ballot_id) -> dict[ballot_id, transfer_value]`
- `Simulation_Layer/Runner/main.py`
  - Global constants:
    - `PROJECT_ROOT`
  - `run_single_seat_rcv(election) -> Dict`
  - `run_multi_seat_stv(election) -> Dict`
  - `run_election(election) -> Dict` (runs on a deep-copied working election so callers can safely replay counts on the same in-memory object)
  - `load_election_from_json(path) -> Election`
  - `run_cli() -> None` (logs warning-context messages before re-raising logger-triggered `SystemExit` during election load or execution failures)
  - Bootstraps the repo root onto `sys.path` for direct file execution from the repository root.
- `Simulation_Layer/Runner/__init__.py`
  - Re-exports runner entrypoints except `run_cli`.
- `Simulation_Layer/Tests/test_acceptance_e2e.py`
  - Pytest-only acceptance suite for canonical simulation outcomes.
  - Each `test_*` function has a concise docstring stating the behavior under test.
  - Keeps raw `run_cli()` output captured internally and emits concise per-test success/warning lines through shared logging wrappers.
  - Recursively discovers runnable JSON files under `Pipe/`, runs each through the CLI path, and compares printed winners against fixture-derived expected winners.
  - Logs success when actual winners match expected winners and logs a warning with actual vs. expected winners before failing when they differ.
  - Replays all 14 canonical acceptance fixtures 5000 times each through `run_cli()` and logs every expected-vs-actual winner mismatch.
  - Includes a regression test that invalid CLI input paths emit the shared JSON read error plus a CLI-context warning before exiting.
  - Pytest-local helpers:
    - `run_case(cli_path, monkeypatch, capsys) -> dict`
    - `log_winner_check(json_path, expected_winners, actual_winners, capsys) -> None`
    - `log_test_success(capsys, message) -> None`
- `Simulation_Layer/Tests/acceptance_helpers.py`
  - Shared acceptance-test parsing, fixture discovery, and fixture-derived expected-winner oracle used by pytest and the CLI runner.
  - Functions:
    - `strip_ansi(text) -> str`
    - `parse_cli_output(stdout) -> dict`
    - `runnable_pipe_json_files() -> list[Path]`
    - `acceptance_case_json_files() -> list[Path]`
    - `fixture_value(payload, field_name) -> Any`
    - `fixture_candidate_status(payload) -> dict[str, str]`
    - `fixture_active_candidates(status) -> list[str]`
    - `fixture_elected_candidates(status) -> list[str]`
    - `fixture_tie_break(tied_ids, tie_break_order) -> str`
    - `fixture_highest_ranked_active(ballot, active_candidate_ids) -> str | None`
    - `fixture_count_votes(payload, status, transfer_values_by_ballot_id=None, inactive_ballot_ids=None) -> tuple[totals, ballot_allocations, inactive_ballot_ids]`
    - `fixture_threshold(first_round_total, seat_count) -> float`
    - `fixture_truncate_4(value) -> float`
    - `expected_single_seat_winners(payload) -> list[str]`
    - `expected_multi_seat_winners(payload) -> list[str]`
    - `expected_winners_from_json(json_path) -> list[str]`
- `Simulation_Layer/Tests/run_acceptance_cli.py`
  - Direct CLI transcript runner for acceptance cases; run with `python Simulation_Layer/Tests/run_acceptance_cli.py`.
  - Injects each canonical acceptance-case path into `run_cli()`, prints the normal CLI transcript, and validates printed winners against fixture-derived expected winners.
  - Functions:
    - `input_for(cli_path) -> str`
    - `run_cli_with_input(cli_path) -> tuple[int, dict]`
    - `main() -> int`

### `Pipe/`
- `Pipe/input.json`: manual/CLI handoff entry path.
- `Pipe/Acceptance_Test_Cases/*.json`: canonical simulation acceptance inputs.
- `Pipe/test_*_output.json`: representational test exports in simulation-ready form.

## MMD Layer Limitations

- Current code is a copied baseline district-generation workflow, not a completed FRA MMD generator.
- Current district generation uses one equal-population target across districts.
- Real FRA multimember maps will need proportional population targets by seat count.
- Current checked-in MMD outputs may be stale relative to `NUM_DISTRICTS = 14`; verify outputs before relying on them for analysis.
- Current MMD outputs do not yet create representational-layer `District` objects.
- Current MMD outputs do not yet feed simulation-layer election JSON directly.
- Current MMD generation is notebook-heavy; prefer extracting reusable logic into modules before adding larger features.

## Global Constants Inventory

- `Global_Utilities/json_io.py`
  - `PROJECT_ROOT`, `PIPE_DIR_NAME`
- `MMD_Generation_Layer/config.py`
  - `base_dir`, `processor_dir`, `shape_path`, `output_dir`, `plans_dir`, `ensemble_csv_path`, `seat_share_png_path`, `NUM_PLANS`, `NUM_DISTRICTS`, `ID_COLUMN`, `GEOM_COLUMN`, `SEED`
- `Global_Utilities/logger.py`
  - `RESET`, `BLUE`, `GREEN`, `RED`, `YELLOW`
- `Simulation_Layer/Core/config.py`
  - `MODE_SINGLE_SEAT_RCV`, `MODE_MULTI_SEAT_STV`, `VALID_MODES`, `DEFAULT_TRANSFER_VALUE`, `DEFAULT_ENCODING`
- `Simulation_Layer/fra_engine.py`
  - `PROJECT_ROOT`
- `Simulation_Layer/Runner/main.py`
  - `PROJECT_ROOT`
- `Representational_Layer/Src/output_writer.py`
  - `PROJECT_ROOT`
- Test-only globals:
  - `Representational_Layer/Tests/test_json_io.py`: `PROJECT_ROOT`
  - `Simulation_Layer/Tests/acceptance_helpers.py`: `PROJECT_ROOT`, `SIMULATION_ROOT`, `CASE_DIR`, `ACCEPTANCE_REPLAY_RUNS`, `REQUIRED_ELECTION_FIELDS`, `ANSI_ESCAPE_RE`, `DEFAULT_TEST_TRANSFER_VALUE`

## Import Path Guidance

- Prefer `Representational_Layer.models`, `Representational_Layer.generation`, and `Representational_Layer.scoring` for external representational imports.
- Keep implementation edits in `Representational_Layer/Src/Representational_Layer/` unless the task is specifically about compatibility wrappers.
- Prefer `Simulation_Layer.Core.models`, `Simulation_Layer.Helpers.utils`, and `Simulation_Layer.Runner.main` for simulation imports.
- Avoid adding new top-level import shims unless there is a clear compatibility reason and `pyproject.toml` is updated.

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
   - `tie_break_order` (`[A, B]` means `A` loses the tie and is eliminated before `B`)
   - optional `max_ranks_allowed` or `max_rankings_allowed`
4. Read/validate using `read_simulation_ready_json(...)` when testing round-trip compatibility.

## Change Management Rules For Agents

- If you add/rename/move a function, update this file immediately.
- If you add a new directory/file, add it to the directory breakdown.
- If you modify JSON contract fields, update the "Required Agent Workflow For JSON Handoffs" section.
- If you change logging conventions, update the "Core Rules For Agents" section.

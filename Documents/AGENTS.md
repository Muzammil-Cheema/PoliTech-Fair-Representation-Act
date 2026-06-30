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
10. Do not add additional `README.md` or `AGENTS.md` files in subdirectories unless the user explicitly asks for them; use the global files in `Documents/` as the single source of truth.

## Naming Convention

- Do not use spaces in project-owned file or directory names; use underscores instead.
- Directory names use capitalized words separated by underscores, for example `Representational_Layer/` and `Global_Utilities/`.
- File names use lowercase words separated by underscores, for example `test_acceptance_e2e.py`.
- Keep conventional repository files such as `AGENTS.md` and `README.md` as exceptions when the toolchain expects those exact names. In this repo those top-level files are compatibility symlinks into `Documents/`.

## Commit Message Convention

- Use `feat: <message>` for feature work.
- Use `fix: <message>` for bug fixes.
- Use `docs: <message>` for documentation changes.
- Use `refactor: <message>` for refactoring-only changes.
- Use `test: <message>` for testing changes, adding or removing tests, running tests, and sharing test results.

## Git Workflow Rule

- Follow the workflow defined in `CONTRIBUTING.md`; treat that file as the source of truth for contributor Git workflow.
- Start work from an issue when possible. If a bug, feature, documentation gap, missing test, or cleanup task does not already have an issue, create one before starting the change.
- Do not work on `main` directly for ordinary project changes.
- Create a new Git branch for every change, even for small documentation, testing, bug-fix, cleanup, or feature tasks.
- Start branch work from an updated local `main`, then use the repo's branch-and-PR workflow.
- Before pushing anything to the remote, update the local repo with the remote state by pulling, fetching, or using the IDE's project update flow.
- Open a PR for review and use squash merge into `main`.
- Use branch names with one of these prefixes:
  - `feat/<short-description>`
  - `fix/<short-description>`
  - `docs/<short-description>`
  - `refactor/<short-description>`
  - `test/<short-description>`

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
- `python -m MMD_Generation_Layer.Processor.main --config MMD_Generation_Layer/Tests/Notebook_Run_Configs/smd_valid_small_debug.json`
  - Run the script-based MMD/SMD generation pipeline from a JSON config.
- `python -m MMD_Generation_Layer.Processor.main --dashboard-only`
  - Launch the Streamlit dashboard through the script runner without generating new plans.

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
- `CONTRIBUTING.md`: contributor onboarding guide covering issue-first workflow, branch/PR conventions, and high-level engineering standards.
- `Documents/`: dedicated home for project markdown and handoff documentation.
- `pyproject.toml`: shared package, editable-install, optional dependency, Python path, and pytest configuration for all layers.
  - Extras:
    - `dev`: pytest.
    - `mmd`: geospatial, notebook, GerryChain, and Streamlit dependencies.
  - Explicit package mappings include `Representational_Layer`, `Attributes`, `Simulation_Layer`, `Core`, `Helpers`, `Runner`, `Global_Utilities`, `MMD_Generation_Layer`, and `MMD_Generation_Layer.Processor`.
  - Quote dotted package names in TOML keys, for example `"MMD_Generation_Layer.Processor"`, so TOML does not treat them as nested keys.
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
- `Documents/Thread_Handoff/Representational_Thread.md`: handoff for the representational-layer implementation and research thread.
- `Documents/Thread_Handoff/Simulation_Thread.md`: handoff for the simulation-layer implementation/debugging thread.
- `Documents/Thread_Handoff/Testing_Thread.md`: handoff for the testing-focused support thread.

### `MMD_Generation_Layer/`
- Purpose:
  - Generates and visualizes baseline district-plan ensembles from geographic data.
  - Uses equal-population ReCom for baseline temporary SMD generation.
  - Includes notebook and script workflows that convert temporary SMD plans into genuine FRA-style multimember district plans using a seat vector and seat-weighted population targets.
  - Produces usable FRA multimember district artifacts, but still needs better proposal strategies and efficiency work before large-scale use.
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
  - Notebook-driven GerryChain/ReCom pipeline plus current FRA multimember generation workflow.
  - Runtime controls in notebook state cell:
    - `RUN_DEFAULTS` (snapshot of defaults sourced from `MMD_Generation_Layer/config.py` plus notebook-only controls)
    - `GENERATION_MODE` (`"SMD"` or `"MMD"`)
    - `RUN_NUM_PLANS`
    - `RUN_NUM_DISTRICTS`
    - `RUN_SEED`
    - `RUN_SHAPE_PATH`
    - `RUN_ID_COLUMN`
    - `RUN_GEOM_COLUMN`
    - `MMD_SEAT_VECTOR`
    - `MMD_SMD_MULTIPLIER`
    - `MMD_PLANS_PER_SMD_PLAN`
    - `POPULATION_TOLERANCE`
    - `MAX_MMD_ATTEMPTS_PER_SMD_PLAN`
    - `CONFIG_PATH`
  - JSON config loader uses a single supported key: `seat_vector`.
  - Legacy `mmd_seat_vector` is explicitly rejected with a clear validation error.
  - In `MMD` mode, config validation fails fast unless `sum(seat_vector) == num_districts`.
  - Config bootstrap behavior:
    - `bootstrap_run_config(CONFIG_PATH)` is executed in the loader cell.
    - If `CONFIG_PATH` is missing/empty, notebook continues with `RUN_DEFAULTS`.
    - If config load/validation fails, notebook warns and resets to `RUN_DEFAULTS` instead of stopping execution.
  - Defines notebook-local functions:
    - `_resolve_run_config_path(config_path)`
    - `_validate_positive_int_list(name, value)`
    - `_extract_seat_vector_from_config(config)`
    - `_validate_run_config(config)`
    - `reset_run_globals_to_defaults()`
    - `apply_run_config(config)`
    - `load_run_config(config_path)`
    - `bootstrap_run_config(config_path=None)`
    - `load_and_build_graph(shape_path=shape_path, id_col=ID_COLUMN, geom_col=GEOM_COLUMN)`
    - `create_initial_partition(graph, num_districts=NUM_DISTRICTS, seed=SEED, population_tolerance=0.05)`
    - `generate_baseline_ensemble(graph, num_plans=NUM_PLANS, num_districts=NUM_DISTRICTS, seed=42, population_tolerance=0.05)`
    - `_build_smd_unit_stats(smd_assignment, graph)`
    - `_build_smd_adjacency(smd_assignment, graph)`
    - `_find_bfs_merge_candidate(start_smd, seat_count, available_smd_ids, smd_adjacency, smd_population, per_seat_population, population_tolerance, max_states=20000)`
    - `_validate_mmd_plan(mmd_plan, graph, seat_vector, population_tolerance)`
    - `_build_single_mmd_plan(smd_assignment, graph, seat_vector, population_tolerance, seed)`
    - `_mmd_plan_signature(mmd_plan)`
    - `generate_mmd_ensemble_from_smd_ensemble(smd_ensemble, graph, seat_vector, plans_per_smd_plan=5, population_tolerance=0.05, seed=SEED, max_attempts_per_smd_plan=250)`
    - `_runtime_mode_settings()`
    - `_print_runtime_settings(mode_settings)`
    - `build_graph_for_run()`
    - `generate_ensemble_for_run(graph)`
    - `save_results_for_run(ensemble)`
    - `plot_results_for_run()`
    - `cleanup_outputs_for_run()`
    - `save_results(ensemble, output_dir)`
    - `generate_district_csvs()`
    - `plot_baseline_histogram(csv_path, output_dir)`
- `MMD_Generation_Layer/Processor/__init__.py`
  - Package marker for script-based MMD processor modules.
- `MMD_Generation_Layer/Processor/runtime_setup.py`
  - Runtime config and JSON config loading for script-based MMD runs.
  - Classes:
    - `RunConfig`
  - Functions:
    - `default_run_config()`
    - `resolve_run_config_path(config_path)`
    - `resolve_runtime_path(path_value)`
    - `validate_positive_int_list(name, value)`
    - `extract_seat_vector_from_config(config)`
    - `validate_run_config(config, base_config=None)`
    - `apply_run_config(config, base_config=None)`
    - `load_run_config(config_path, base_config=None)`
    - `bootstrap_run_config(config_path=None)`
    - `describe_run_config(run_config)`
- `MMD_Generation_Layer/Processor/generation_logic.py`
  - Script-based SMD generation and current FRA multimember generation business logic.
  - Functions:
    - `load_and_build_graph(shape_path=shape_path, id_col=ID_COLUMN, geom_col=GEOM_COLUMN)`
    - `create_initial_partition(graph, num_districts=NUM_DISTRICTS, seed=SEED, population_tolerance=0.05)`
    - `generate_baseline_ensemble(graph, num_plans=NUM_PLANS, num_districts=NUM_DISTRICTS, seed=SEED, population_tolerance=0.05)`
    - `_build_smd_unit_stats(smd_assignment, graph)`
    - `_build_smd_adjacency(smd_assignment, graph)`
    - `_find_bfs_merge_candidate(...)`
    - `_validate_mmd_plan(mmd_plan, graph, seat_vector, population_tolerance)`
    - `_build_single_mmd_plan(smd_assignment, graph, seat_vector, population_tolerance, seed)`
    - `_mmd_plan_signature(mmd_plan)`
    - `generate_mmd_ensemble_from_smd_ensemble(...)`
    - `runtime_mode_settings(run_config)`
    - `generate_ensemble_for_run(graph, run_config)`
- `MMD_Generation_Layer/Processor/output_artifacts.py`
  - Output persistence and optional diagnostic artifacts for generated plans.
  - Functions:
    - `save_ensemble_summary(ensemble, csv_path)`
    - `save_plan_assignments(ensemble, plans_dir, clear_existing=True)`
    - `plot_seat_share_histogram(results_df, output_path)`
    - `generate_district_csvs(gdf, plans_dir, output_dir)`
    - `save_output_artifacts(ensemble, run_config, gdf=None, include_plots=True, include_district_csvs=False)`
- `MMD_Generation_Layer/Processor/main.py`
  - Script entrypoint for running generation and optionally launching Streamlit.
  - Functions:
    - `run_generation_pipeline(config_path=None, include_plots=True, include_district_csvs=False)`
    - `run_streamlit_dashboard(extra_args=None)`
    - `parse_args(argv=None)`
    - `main(argv=None)`
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
- `MMD_Generation_Layer/Tests/Notebook_Run_Configs/`
  - JSON run configs loadable in the notebook via `load_run_config(...)`.
  - `smd_valid_baseline.json`, `smd_valid_small_debug.json`: valid SMD scenarios.
  - `mmd_valid_balanced.json`, `mmd_valid_high_variance.json`, `mmd_valid_seat_vector_alias.json`: valid MMD scenarios using `seat_vector`.
  - `mmd_edge_strict_tolerance.json`, `mmd_edge_low_attempt_budget.json`: valid edge-case stress scenarios.
  - `invalid_mode.json`, `invalid_negative_tolerance.json`, `invalid_tolerance_gt_one.json`, `invalid_empty_mmd_seat_vector.json`, `invalid_nonpositive_mmd_seat_vector.json`, `invalid_null_mmd_seat_vector.json`, `invalid_unknown_key.json`, `invalid_conflicting_seat_vectors.json`, `invalid_seat_vector_sum_mismatch.json`: invalid-input fixtures intended to raise fast validation errors (including legacy key rejection, bad `seat_vector` content, and seat-sum mismatch checks).

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
  - Public exports for models, generation, scoring, and input-contract validation.
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
  - `PreferenceModel.temperature` is mandatory and must be supplied by callers.
  - Type aliases/literals:
    - `Profile`, `Parameters`, `ElectionMode`, `AttributeType`, `ComparisonMode`, `ScoreStyle`, `MissingValuePolicy`, `RankingMethod`
- `Representational_Layer/Src/Representational_Layer/input_contract.py`
  - Strict validator/parser for user-authored representational experiment JSON contracts.
  - Separates dataclass-derived model-shape rules from explicit user-contract policy rules in the same file.
  - Public classes:
    - `ContractValidationError`
    - `RepresentationalExperimentState`
  - Public functions:
    - `load_experiment_contract(path) -> RepresentationalExperimentState`
    - `parse_experiment_contract(contract) -> RepresentationalExperimentState`
  - Validates exact top-level and nested key ordering, mandatory fields, enum-like literal values, cross-reference integrity, district/election seat-rank consistency, non-empty profiles, custom attribute config requirements, and preference-model weight alignment.
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
- `Input_Contracts/`
  - JSON fixtures for strict representational input-contract parsing.
  - Includes one valid starter/custom contract plus invalid examples for missing mandatory fields, relationship mismatches, custom-attribute config errors, mandatory temperature, and key-order validation.
- `test_input_contract.py`
  - Tests strict loading of the representational JSON input contract and rejection of invalid contract fixtures.
  - Uses small fixture helpers (`fixture_path`, `load_fixture`, `assert_contract_rejected`) and delegates all contract validation to `Representational_Layer.load_experiment_contract(...)`.
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

- Current code remains notebook-heavy and is not yet a stabilized package API for MMD generation.
- Baseline generation still depends on equal-population ReCom temporary SMD plans.
- The current MMD workflow can generate usable FRA multimember districts, but it still needs deeper validation, better proposal strategies, and stronger efficiency for larger runs.
- Native GerryChain proposal approaches are still a planned improvement area and may produce better plan-space exploration than the current workflow.
- Current checked-in MMD outputs may be stale relative to `NUM_DISTRICTS = 14`; verify outputs before relying on them for analysis.
- Current MMD outputs do not yet create representational-layer `District` objects.
- Current MMD outputs do not yet feed simulation-layer election JSON directly.
- Current MMD mode still needs extraction into reusable modules before API hardening.

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
- `Representational_Layer/Src/Representational_Layer/input_contract.py`
  - Model-shape constants derived from dataclass fields: `TOP_LEVEL_KEYS`, `EXPERIMENT_KEYS`, `DISTRICT_KEYS`, `ELECTION_KEYS`, `ATTRIBUTE_SPEC_KEYS`, `CANDIDATE_KEYS`, `ELECTOR_UNIT_KEYS`, `PREFERENCE_MODEL_KEYS`, `BALLOT_GENERATION_RUN_KEYS`
  - Explicit contract-policy constants: `TOP_LEVEL_REQUIRED_KEYS`, `EXPERIMENT_REQUIRED_KEYS`, `DISTRICT_REQUIRED_KEYS`, `ELECTION_REQUIRED_KEYS`, `ATTRIBUTE_SPEC_REQUIRED_KEYS`, `NEW_ATTRIBUTE_SPEC_REQUIRED_KEYS`, `CANDIDATE_REQUIRED_KEYS`, `ELECTOR_UNIT_REQUIRED_KEYS`, `PREFERENCE_MODEL_REQUIRED_KEYS`, `BALLOT_GENERATION_RUN_REQUIRED_KEYS`
  - Internal model-shape helper constant: `_ASSIGNED_EXPERIMENT_FIELD`
  - `VALID_ELECTION_MODES`, `VALID_ATTRIBUTE_TYPES`, `VALID_COMPARISON_MODES`, `VALID_SCORE_STYLES`, `VALID_MISSING_VALUE_POLICIES`, `VALID_RANKING_METHODS`
- Test-only globals:
  - `Representational_Layer/Tests/test_input_contract.py`: `FIXTURE_DIR`
  - `Representational_Layer/Tests/test_json_io.py`: `PROJECT_ROOT`
  - `Simulation_Layer/Tests/acceptance_helpers.py`: `PROJECT_ROOT`, `SIMULATION_ROOT`, `CASE_DIR`, `ACCEPTANCE_REPLAY_RUNS`, `REQUIRED_ELECTION_FIELDS`, `ANSI_ESCAPE_RE`, `DEFAULT_TEST_TRANSFER_VALUE`

## Import Path Guidance

- Prefer `Representational_Layer.models`, `Representational_Layer.generation`, and `Representational_Layer.scoring` for external representational imports.
- Prefer `Representational_Layer.load_experiment_contract(...)` for user-authored representational JSON input contracts.
- Keep implementation edits in `Representational_Layer/Src/Representational_Layer/` unless the task is specifically about compatibility wrappers.
- Prefer `Simulation_Layer.Core.models`, `Simulation_Layer.Helpers.utils`, and `Simulation_Layer.Runner.main` for simulation imports.
- Avoid adding new top-level import shims unless there is a clear compatibility reason and `pyproject.toml` is updated.

## Complete Model/Class Inventory

### Representational layer classes

- `ContractValidationError`
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
- `RepresentationalExperimentState`

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

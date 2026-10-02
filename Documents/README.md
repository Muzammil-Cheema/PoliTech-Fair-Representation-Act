# Politech Fair Representation Act

## For Humans: Understanding this Repo

This repository has three separate code layers that should stay separate:

- `MMD_Generation_Layer/`: generates and visualizes district-plan ensembles from geographic data.
- `Representational_Layer/`: generates candidates and ranked ballots.
- `Simulation_Layer/`: consumes election JSON and runs FRA counting rules.

The fastest way to avoid regressions is to treat those as separate products with explicit file boundaries. MMD generation produces district-plan artifacts; the representational layer produces candidates and rank-preserving ballots; the simulation layer consumes election JSON and determines winners.

## MMD Generation Layer Scope

`MMD_Generation_Layer/` was copied into this repo from a previous standalone project. It is now the home for district-plan generation work. Since the GerryChain 1.0.0 migration (issue #34) it generates FRA-style multimember district plans natively; see [How MMD generation works](#how-mmd-generation-works).

Current implementation:

- Uses 2024 precinct shapefiles for North Carolina (default), South Carolina, Tennessee, and Virginia under `MMD_Generation_Layer/Data/Shapefiles/<STATE>/<state>_2024_with_population.shp`.
- Builds district-plan ensembles with GerryChain 1.0.0 from the script entrypoint `python -m MMD_Generation_Layer.Processor.main --config <config.json>`.
- `SMD` mode builds equal-population single-member plans with ReCom; `MMD` mode builds seat-proportional multimember plans with GerryChain's native `MultiMemberReCom`.
- Uses shared MMD config defaults in `MMD_Generation_Layer/config.py`, overridden per run by a JSON config.
- Writes baseline plan summaries to `MMD_Generation_Layer/Outputs/baseline_ensemble.csv`.
- Writes precinct-to-district assignment JSON files to `MMD_Generation_Layer/Outputs/Plan_Assignments/`.
- Optionally writes the auto-built MMD seed plan to `MMD_Generation_Layer/Outputs/seed_plan.json` when `save_seed_plan` is set (off by default; see below).
- Writes the resolved run config (`shape_path`, `num_districts`, `num_plans`, `id_column`, `geom_column`) to `MMD_Generation_Layer/Outputs/run_metadata.json` after each run.
- Provides a Streamlit dashboard in `MMD_Generation_Layer/Client/baseline_dashboard.py` that reads `run_metadata.json` to resolve which state's shapefile/config to render, falling back to `config.py`'s NC defaults if no metadata file is present.

Data note: current MMD runs pair 2020 Census population figures with 2024 voting data. Keep that year mismatch in mind when interpreting outputs or comparing them to fully time-aligned analyses.

### MMD population and geometry construction

GerryChain needs every graph unit to have a geometry, adjacency relationships, total population, and election results. Those fields are not generally available together from one government source at one shared geographic level, so the population and election datasets must be spatially reconciled.

The current approach uses election precincts as the graph units:

- Preserve the precinct geometries and reported 2024 precinct vote totals from the election shapefile.
- Read official 2020 Census block geometries and `POP20` population totals from TIGER/Line files.
- Reconstruct each precinct's `TOTPOP` by assigning Census block population to the precincts that contain or overlap the block.
- Use either the fast point method, which assigns the entire block population to the precinct containing its Census internal point, or the slower area-weighted method, which distributes population according to the fraction of block area overlapping each precinct. The area-weighted method is preferred for retained research data.

This can be summarized as **reported precinct votes plus reconstructed precinct population**. It preserves the election reporting units and avoids expanding the GerryChain graph to hundreds of thousands of Census blocks. Statewide population is preserved very closely, apart from boundary mismatches and rounding, but individual precinct values remain estimates because Census data do not identify where people live within each block. The method also combines 2020 population with 2024 votes, so it does not capture population movement after the Census.

A reverse approach could instead use Census blocks as the graph units:

- Preserve the official Census block geometries and exact block-level `POP20` totals.
- Overlay election precincts onto the blocks.
- Reconstruct block-level Democratic and Republican vote totals by distributing each precinct's reported votes among its overlapping blocks, using area or a population-related weighting variable.
- Build district plans directly from the much larger block graph and aggregate the reconstructed block votes into each generated district.

The reverse approach can be summarized as **reported block population plus reconstructed block votes**. It gives the district generator finer population geometry, but it does not make the combined dataset exact: ballots are reported for whole precincts, not Census blocks, so their locations within a precinct are unknown. It would also substantially increase graph-building, memory, and ensemble-generation costs. Unless population precision becomes more important than vote preservation and runtime, the current precinct-based method is the practical default for exploratory and unpublished academic research. Comparisons between the point and area-weighted methods, statewide-total checks, and sensitivity tests should be used before drawing strong conclusions from individual precincts or close district outcomes.

### How MMD generation works

`MMD` mode uses a `seat_vector` such as `[5, 5, 4]` for North Carolina's 14 seats. District label `i` always has `seat_vector[i]` seats.

1. **Targets.** `per_seat_population = total_population / sum(seat_vector)` (about 762,804 for NC). District `i` targets `seat_vector[i] × per_seat_population`, so a 5-seat district holds about five times as many people as a 1-seat district.
2. **Population tolerance is per seat.** Every district's population divided by its seats must be within `population_tolerance` of `per_seat_population`.
3. **Seed plan.** A valid starting plan is built from scratch at runtime by peeling off one district at a time with GerryChain's unequal-target spanning-tree split: NC `5/5/4` is split `5 | 9`, then `5 | 4`. Each split cuts one spanning-tree edge, so every district is contiguous. A failed attempt retries with fresh randomness up to `max_seed_attempts`, then stops with a clear error. Code: `build_mmd_seed_assignment(...)` and `create_mmd_seed_partition(...)` in `MMD_Generation_Layer/Processor/mmd_generation.py`.
4. **Chain.** GerryChain's `MultiMemberReCom` (variant chosen by `recom_variant`) repeatedly merges two neighbouring districts and re-splits them in proportion to their seat counts. Seat counts stay attached to district labels; only geography changes. Contiguity and per-seat population are enforced on every plan. Code: `generate_mmd_ensemble(...)`.
5. **Sampling.** The seed is chain step 0 and is never saved. After `burn_in_steps`, every `step_interval`-th plan is saved until `num_plans` plans exist. Defaults (`0`, `1`) save every step; raise them for more independent ensembles.
6. **Reproducibility.** One `random.Random(seed)` drives the seed plan and the chain, so the same config reproduces the same ensemble.

Seats in `baseline_ensemble.csv` are counted winner-take-all per district (all of a district's seats go to the party with more votes). That is a display rule for the ensemble summary, not proportional FRA/STV allocation, which belongs to the simulation layer.

### MMD run configs

Run configs are JSON files stored under `MMD_Generation_Layer/Tests/Notebook_Run_Configs/`. Run one with:

```bash
python -m MMD_Generation_Layer.Processor.main --config MMD_Generation_Layer/Tests/Notebook_Run_Configs/mmd_valid_sc_small.json
```

The `*_small` configs (`mmd_valid_sc_small`, `mmd_valid_tn_small`, `mmd_valid_va_small`, `smd_valid_small_debug`) finish in seconds and are the quickest way to check a change end to end. If a config fails validation, the run logs the error and falls back to the `config.py` defaults (NC), so check the log.

`MMD_Generation_Layer/Processor/main.ipynb` is the legacy pre-GerryChain-1.0.0 prototype. It still contains the old temporary-SMD-to-MMD workflow and no longer runs; use the script entrypoint above.

Config categories:

- `smd_valid_*`: expected-valid SMD scenarios.
- `mmd_valid_*`: expected-valid MMD scenarios.
- `mmd_edge_*`: syntactically valid, but may produce fewer plans or fail under strict constraints.
- `invalid_*`: intentionally invalid inputs for validation-path testing.

Important config rules:

- `generation_mode` must be `"SMD"` or `"MMD"`.
- `population_tolerance` must be strictly between `0` and `1`.
- In `MMD` mode, `seat_vector` must be a non-empty list of positive integers.
- Legacy `mmd_seat_vector` is intentionally rejected with a clear error.
- The loader is strict and raises errors on unknown keys.
- In `MMD` mode, `seat_vector` must contain at least 2 districts.
- `mmd_smd_multiplier`, `mmd_plans_per_smd_plan`, `max_mmd_attempts_per_smd_plan`, and `save_intermediate_smd_plans` were removed in the GerryChain 1.0.0 migration and are rejected with a clear error; delete them from older configs.
- `recom_variant` (default `district_pairs_mst`), `burn_in_steps` (default `0`), `step_interval` (default `1`), `max_seed_attempts` (default `10`), and `save_seed_plan` (default `false`) control native `MMD` generation and are ignored in `SMD` mode.

### Migrating to GerryChain 1.0.0

- Reinstall dependencies after pulling: `python -m pip install -e '.[mmd]'`. GerryChain 1.0.0 requires pandas 3, so pandas, numpy, geopandas, scipy, networkx, and Streamlit move together, and `rustworkx` and `tqdm` are added.
- Delete `mmd_smd_multiplier`, `mmd_plans_per_smd_plan`, `max_mmd_attempts_per_smd_plan`, and `save_intermediate_smd_plans` from old configs; they are rejected.
- Use `num_plans` for the number of saved MMD plans directly; there are no temporary SMD plans anymore.
- Custom GerryChain code must use the 1.0.0 graph API: `graph.node_data(node)[key]` for node attributes, `graph.nodes` / `graph.edges` as properties, and `assignment_by_original_node_id(partition)` to turn `partition.assignment` (internal integer IDs) back into precinct IDs.

## Best-Practice Structure

- Keep representational experiments in `Representational_Layer/Src/Representational_Layer/`.
- Keep simulation models, counting utilities, and tabulation configuration in `Simulation_Layer/Core/`; use `Simulation_Layer/Core/utils.py` for simulation helper imports.
- Keep district generation and map/dashboard logic in `MMD_Generation_Layer/`.
- Use `Global_Utilities/json_io.py` for JSON contracts between layers.
- Use `Global_Utilities/logger.py` wrappers (`info/warn/success/error`) for runtime messaging.
- Keep reusable attribute vocabulary in `Representational_Layer/Attributes/starter_attributes.py`.
- Put generated handoff JSON in `Pipe/` through the JSON helpers.
- Keep local/debug representational outputs in `Representational_Layer/Outputs/` when a test also needs an inspection copy.
- Use the root `pyproject.toml` for shared package, Python path, and pytest configuration.

## What Already Exists (Do Not Duplicate)

- Data models:
  - Representational models in `Representational_Layer/Src/Representational_Layer/models.py`
  - Top-level representational compatibility imports in `Representational_Layer/models.py`, `Representational_Layer/generation.py`, and `Representational_Layer/scoring.py`
  - Simulation models in `Simulation_Layer/Core/models.py`
  - Simulation counting and ballot-resolution utilities in `Simulation_Layer/Core/utils.py`
- MMD configuration and generation:
  - `MMD_Generation_Layer/config.py`
  - `MMD_Generation_Layer/Processor/main.ipynb`
  - `MMD_Generation_Layer/Client/baseline_dashboard.py`
- Scoring logic:
  - `Representational_Layer/Src/Representational_Layer/scoring.py`
- Ballot generation helpers:
  - `Representational_Layer/Src/Representational_Layer/generation.py`
- Simulation-ready JSON writers/readers:
  - `Global_Utilities/json_io.py`
  - `Representational_Layer/Src/output_writer.py` (thin wrapper for representational tests)
- Acceptance fixtures:
  - `Pipe/Acceptance_Test_Cases/*.json`
- Simulation-ready representational exports:
  - `Pipe/test_*_output.json`
- Optional local inspection exports:
  - `Representational_Layer/Outputs/test_*_output.json`

Before adding a new utility, search for it first with `rg`.

## Daily Workflow

1. From the repository root, activate the environment: `source .venv/bin/activate`.
2. Install the editable project with test dependencies: `python -m pip install -e '.[dev]'`.
3. Run tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`.
4. Generate or refresh simulation-ready JSON through `write_simulation_ready_output(...)` or `write_simulation_ready_json(...)`.

For MMD work, install the optional geospatial/dashboard dependencies with `python -m pip install -e '.[mmd]'`, then run `python -m MMD_Generation_Layer.Processor.main --config <config.json>` and inspect results with `streamlit run MMD_Generation_Layer/Client/baseline_dashboard.py`.

Useful commands:

- `python -m pip install -e '.[dev]'`: install the repo for test/development work.
- `python -m pip install -e '.[mmd]'`: install the geospatial, notebook, and dashboard dependencies.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`: run all configured tests.
- `python -m MMD_Generation_Layer.Processor.main --config <config.json>`: run MMD/SMD generation from a JSON config (add `--dashboard` to open the dashboard afterwards).
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q MMD_Generation_Layer/Tests`: run the MMD generation tests.
- `jupyter notebook MMD_Generation_Layer/Processor/main.ipynb`: open the legacy MMD notebook (pre-GerryChain 1.0.0; no longer runs).
- `python Simulation_Layer/fra_engine.py`: run the simulation CLI compatibility shim.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q Simulation_Layer/Tests/test_acceptance_e2e.py`: run the simulation end-to-end acceptance tests.
- `python Simulation_Layer/Tests/run_acceptance_cli.py`: replay every canonical acceptance case through the CLI transcript path and validate winners.
- `streamlit run MMD_Generation_Layer/Client/baseline_dashboard.py`: inspect generated MMD baseline plans.

Common task commands:

```bash
# Run MMD generation on a small config
python -m pip install -e '.[mmd]'
python -m MMD_Generation_Layer.Processor.main --config MMD_Generation_Layer/Tests/Notebook_Run_Configs/mmd_valid_sc_small.json

# Run the FRA CLI counter
python Simulation_Layer/fra_engine.py

# Run the e2e simulation acceptance tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q Simulation_Layer/Tests/test_acceptance_e2e.py
```

Terminal-output nuance: running `python Simulation_Layer/fra_engine.py` or `python Simulation_Layer/Runner/main.py` is a manual CLI flow, so it prompts for an input JSON path and prints winners, final candidate status, and round details to the terminal. Running the e2e tests with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q Simulation_Layer/Tests/test_acceptance_e2e.py` is not meant as an interactive report; it validates expected outcomes and normally stays quiet unless a case fails.

Current verified test state:

- On October 2, 2026, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q` completed with `149 passed` (with the `mmd` extra installed).

## Environment Variables And Globals

### Environment variables

- Required by source code: none currently required.
- Common workflow variables:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` for stable test runs.
  - `PYTHONPATH=.:Src` for direct script execution from `Representational_Layer/`.
  - `PYTHONPATH=.:MMD_Generation_Layer` can be useful when running MMD scripts directly.

### Global constants

- `MMD_Generation_Layer/config.py`: `base_dir`, `processor_dir`, `shape_path`, `output_dir`, `plans_dir`, `ensemble_csv_path`, `seat_share_png_path`, `seed_plan_path`, `NUM_PLANS`, `NUM_DISTRICTS`, `ID_COLUMN`, `GEOM_COLUMN`, `SEED`, `RECOM_VARIANT`, `BURN_IN_STEPS`, `STEP_INTERVAL`, `MAX_SEED_ATTEMPTS`, `SAVE_SEED_PLAN`
- `Global_Utilities/json_io.py`: `PROJECT_ROOT`, `PIPE_DIR_NAME`
- `Global_Utilities/logger.py`: `RESET`, `BLUE`, `GREEN`, `RED`, `YELLOW`
- `Simulation_Layer/Core/config.py`: `MODE_SINGLE_SEAT_RCV`, `MODE_MULTI_SEAT_STV`, `VALID_MODES`, `DEFAULT_TRANSFER_VALUE`, `DEFAULT_ENCODING`
- `Simulation_Layer/fra_engine.py`: `PROJECT_ROOT`
- `Simulation_Layer/Runner/main.py`: `PROJECT_ROOT`
- `Representational_Layer/Src/output_writer.py`: `PROJECT_ROOT`

## Practical Tips

- Keep ballots in rank-group format (`rank` + `candidate_ids`), not flat lists.
- Always include deterministic metadata (`election_id`, `seat_count`, `mode`, `tie_break_order`) when writing handoff JSON.
- `tie_break_order` is an elimination priority, not a survival priority. If two tied candidates appear as `[A, B]`, then `A` is eliminated before `B`.
- Treat MMD output files as district-generation artifacts, not simulation-ready election inputs.
- Prefer top-level imports like `from Representational_Layer.models import Candidate` and `from Simulation_Layer.Core.models import Election`; compatibility wrappers now support these cleaner paths.
- Favor small, composable functions over monolithic test logic.
- If adding output files, route them through shared JSON helpers so simulation ingestion remains stable.
- If changing scoring semantics, update tests and the shared attribute vocabulary together.

## Common Pitfalls

- Mixing representational profile logic into simulation counting code.
- Reading the winner-take-all seat counts in `baseline_ensemble.csv` as FRA/STV election results.
- Running an old MMD config with removed temporary-SMD keys and missing the warning that the run fell back to the NC defaults.
- Writing ad-hoc JSON schemas that bypass `Global_Utilities/json_io.py`.
- Using `print` directly in library/runtime flow instead of logger wrappers.
- Adding duplicate model classes in new files.

## Current Test Entry Points

- `Representational_Layer/Tests/test_models.py`
- `Representational_Layer/Tests/test_scoring.py`
- `Representational_Layer/Tests/test_profile_based_ballot_generation.py`
- `Representational_Layer/Tests/test_json_io.py`
- `Simulation_Layer/Tests/test_acceptance_e2e.py`
- `MMD_Generation_Layer/Tests/test_graph_loading.py`
- `MMD_Generation_Layer/Tests/test_smd_generation.py`
- `MMD_Generation_Layer/Tests/test_mmd_seed.py`
- `MMD_Generation_Layer/Tests/test_mmd_chain.py`
- `MMD_Generation_Layer/Tests/test_mmd_run_config.py`

Supporting simulation test utilities:

- `Simulation_Layer/Tests/acceptance_helpers.py`
- `Simulation_Layer/Tests/run_acceptance_cli.py`

## Where Visualization Should Plug In Later

When you add visualization, consume outputs from:

- `MMD_Generation_Layer/Outputs/Plan_Assignments/*.json` and `MMD_Generation_Layer/Outputs/baseline_ensemble.csv` for district-plan maps and ensemble diagnostics.
- `score_candidates_for_elector_unit(...)` (candidate score traces)
- simulation-ready JSON outputs in `Pipe/` (ballot and candidate payloads)

This keeps charts decoupled from core scoring/counting logic.

## Known Issues And Remaining Work

### High-priority known issues

- The simulation layer has a strong acceptance-test base, but still needs hardening for long-run robustness and legal-confidence edge behavior under varied real-world input distributions.
- Representational ballot generation currently exists in two styles:
  - weighted random generation (`generate_ballot(...)` / `generate_weighted_ballot_ranking(...)`)
  - profile-scoring + deterministic sort (used in profile-based tests)
  - these should converge behind one simple public generation API.

### What is left to do

1. Simulation-layer correctness and robustness (top priority):
   - expand beyond fixture-style acceptance tests into stress/property testing
   - add adversarial/fuzz ballot-shape tests (deep skips, large same-rank groups, repeated ranks at scale)
   - verify deterministic tie behavior persists cleanly across replay/recount workflows
   - improve invariant checks and failure diagnostics around transfer-value and threshold transitions
2. MMD-generation maturity:
   - continue improving efficiency in the MMD generation workflow, since it is currently the most computationally complex portion of the project
   - reduce plan-generation cost and improve practical throughput for larger experiment runs
3. MMD-generation proposal quality:
   - native GerryChain 1.0.0 `MultiMemberReCom` is now the MMD workflow; choose defaults for `recom_variant`, `burn_in_steps`, and `step_interval` for research-grade ensembles
   - compare variants on runtime and plan diversity on full-size runs
   - keep the resulting multimember plans usable for downstream research workflows
4. Representational-layer API simplification:
   - expose one orchestration entrypoint for: scoring -> ranking -> ballot objects -> simulation JSON export
   - keep per-method behavior selectable (`deterministic_sort`, weighted, softmax) behind that single entrypoint
5. Vocabulary maturity:
   - continue expanding and versioning shared attribute specs in `Representational_Layer/Attributes/`
   - formalize weight presets and missing-value policies for reproducible experiments
6. Visualization support:
   - add reusable export shape for plotting round-by-round candidate utilities and ballot distributions
   - produce starter notebooks or scripts for score and ranking diagnostics
7. Documentation alignment:
   - keep `AGENTS.md` synchronized with each code change
   - keep simulation handoff examples in `Pipe/` aligned with current writer/readers
8. Logger modernization:
   - `Global_Utilities/logger.py` currently uses `print` internally for output formatting
   - if structured observability is needed later, move this behavior to Python `logging` handlers

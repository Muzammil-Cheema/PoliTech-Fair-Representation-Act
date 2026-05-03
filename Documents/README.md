# Politech Fair Representation Act

## For Humans: How To Work In This Repo

This repository has three separate code layers that should stay separate:

- `MMD_Generation_Layer/`: generates and visualizes district-plan ensembles from geographic data.
- `Representational_Layer/`: generates candidates and ranked ballots.
- `Simulation_Layer/`: consumes election JSON and runs FRA counting rules.

The fastest way to avoid regressions is to treat those as separate products with explicit file boundaries. MMD generation produces district-plan artifacts; the representational layer produces candidates and rank-preserving ballots; the simulation layer consumes election JSON and determines winners.

## MMD Generation Layer Scope

`MMD_Generation_Layer/` was copied into this repo from a previous standalone project. It is now the home for district-plan generation work, but it is not yet a complete FRA multimember-district generator.

Current implementation:

- Uses a North Carolina precinct shapefile at `MMD_Generation_Layer/Data/Shapefiles/NC/nc_2024_with_population.shp`.
- Builds district-plan ensembles with GerryChain/ReCom from `MMD_Generation_Layer/Processor/main.ipynb`.
- Uses shared MMD config in `MMD_Generation_Layer/config.py`.
- Writes baseline plan summaries to `MMD_Generation_Layer/Outputs/baseline_ensemble.csv`.
- Writes precinct-to-district assignment JSON files to `MMD_Generation_Layer/Outputs/Plan_Assignments/`.
- Provides a Streamlit dashboard in `MMD_Generation_Layer/Client/baseline_dashboard.py`.

Important limitation: the current MMD code generates equal-population district plans with one population target across districts. Real FRA multimember maps will need proportional population targets by seat count, for example a 5-seat MMD should target roughly five times the ideal single-seat population. That proportional MMD grouping work is still future work.

## Best-Practice Structure

- Keep representational experiments in `Representational_Layer/Src/Representational_Layer/`.
- Keep simulation counting logic in `Simulation_Layer/`.
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

For MMD work, install the optional geospatial/dashboard dependencies with `python -m pip install -e '.[mmd]'`, then work from `MMD_Generation_Layer/Processor/main.ipynb` or run the dashboard with `streamlit run MMD_Generation_Layer/Client/baseline_dashboard.py`.

Useful commands:

- `python -m pip install -e '.[dev]'`: install the repo for test/development work.
- `python -m pip install -e '.[mmd]'`: install the geospatial, notebook, and dashboard dependencies.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`: run all configured tests.
- `jupyter notebook MMD_Generation_Layer/Processor/main.ipynb`: open the MMD notebook workflow.
- `python Simulation_Layer/fra_engine.py`: run the simulation CLI compatibility shim.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q Simulation_Layer/Tests/test_acceptance_e2e.py`: run the simulation end-to-end acceptance tests.
- `python Simulation_Layer/Tests/run_acceptance_cli.py`: replay every canonical acceptance case through the CLI transcript path and validate winners.
- `streamlit run MMD_Generation_Layer/Client/baseline_dashboard.py`: inspect generated MMD baseline plans.

Common task commands:

```bash
# Run the MMD notebook
python -m pip install -e '.[mmd]'
jupyter notebook MMD_Generation_Layer/Processor/main.ipynb

# Run the FRA CLI counter
python Simulation_Layer/fra_engine.py

# Run the e2e simulation acceptance tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q Simulation_Layer/Tests/test_acceptance_e2e.py
```

Terminal-output nuance: running `python Simulation_Layer/fra_engine.py` or `python Simulation_Layer/Runner/main.py` is a manual CLI flow, so it prompts for an input JSON path and prints winners, final candidate status, and round details to the terminal. Running the e2e tests with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q Simulation_Layer/Tests/test_acceptance_e2e.py` is not meant as an interactive report; it validates expected outcomes and normally stays quiet unless a case fails.

Current verified test state:

- On May 3, 2026, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q` completed with `41 passed`.

## Environment Variables And Globals

### Environment variables

- Required by source code: none currently required.
- Common workflow variables:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` for stable test runs.
  - `PYTHONPATH=.:Src` for direct script execution from `Representational_Layer/`.
  - `PYTHONPATH=.:MMD_Generation_Layer` can be useful when running MMD scripts directly.

### Global constants

- `MMD_Generation_Layer/config.py`: `base_dir`, `processor_dir`, `shape_path`, `output_dir`, `plans_dir`, `ensemble_csv_path`, `seat_share_png_path`, `NUM_PLANS`, `NUM_DISTRICTS`, `ID_COLUMN`, `GEOM_COLUMN`, `SEED`
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
- Treating current MMD plan assignments as FRA-complete proportional MMD plans.
- Writing ad-hoc JSON schemas that bypass `Global_Utilities/json_io.py`.
- Using `print` directly in library/runtime flow instead of logger wrappers.
- Adding duplicate model classes in new files.

## Current Test Entry Points

- `Representational_Layer/Tests/test_models.py`
- `Representational_Layer/Tests/test_scoring.py`
- `Representational_Layer/Tests/test_profile_based_ballot_generation.py`
- `Representational_Layer/Tests/test_json_io.py`
- `Simulation_Layer/Tests/test_acceptance_e2e.py`

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
- The MMD generation layer is copied in and useful for baseline geographic experimentation, but it currently generates equal-population district plans rather than FRA-ready proportional-population multimember districts.
- Representational ballot generation currently exists in two styles:
  - weighted random generation (`generate_ballot(...)` / `generate_weighted_ballot_ranking(...)`)
  - profile-scoring + deterministic sort (used in profile-based tests)
  - these should converge behind one simple public generation API.
- `Global_Utilities/logger.py` currently uses `print` internally for output formatting. This is acceptable for now, but if structured observability is needed later, this should move to Python `logging` handlers.

### What is left to do

1. Simulation-layer correctness and robustness (top priority):
   - expand beyond fixture-style acceptance tests into stress/property testing
   - add adversarial/fuzz ballot-shape tests (deep skips, large same-rank groups, repeated ranks at scale)
   - verify deterministic tie behavior persists cleanly across replay/recount workflows
   - improve invariant checks and failure diagnostics around transfer-value and threshold transitions
2. MMD-generation maturity:
   - convert the notebook-heavy copied workflow into reusable modules and tests
   - add proportional population targets based on MMD seat counts
   - generate true multimember district groupings instead of only equal-population baseline district plans
   - define how MMD outputs should feed representational `District` objects later
3. Representational-layer API simplification:
   - expose one orchestration entrypoint for: scoring -> ranking -> ballot objects -> simulation JSON export
   - keep per-method behavior selectable (`deterministic_sort`, weighted, softmax) behind that single entrypoint
4. Vocabulary maturity:
   - continue expanding and versioning shared attribute specs in `Representational_Layer/Attributes/`
   - formalize weight presets and missing-value policies for reproducible experiments
5. Visualization support:
   - add reusable export shape for plotting round-by-round candidate utilities and ballot distributions
   - produce starter notebooks or scripts for score and ranking diagnostics
6. Documentation alignment:
   - keep `AGENTS.md` synchronized with each code change
   - keep simulation handoff examples in `Pipe/` aligned with current writer/readers

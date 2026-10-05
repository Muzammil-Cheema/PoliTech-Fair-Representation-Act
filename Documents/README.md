# Politech Fair Representation Act

## Project Overview

This repository is research software for studying the Fair Representation Act (FRA) through three cooperating but separate layers:

- `MMD_Generation_Layer/` generates geographic district-plan artifacts and visualizations.
- `Representational_Layer/` models candidates, elector units, preferences, and rank-preserving ballots.
- `Simulation_Layer/` consumes simulation-ready election JSON and runs RCV or multi-seat STV tabulation.

The shared boundary between representational modeling and simulation is the typed JSON contract implemented in `Global_Utilities/json_io.py`. MMD outputs are geographic district artifacts; they are not simulation-ready election JSON.

The root `README.md` is a compatibility symlink to this file. `Documents/` is the canonical home for project documentation.

## Start Here

Run commands from the repository root:

```bash
source .venv/bin/activate
python3 -m pip install -e '.[dev,mmd]'
```

The `dev` extra installs pytest. The `mmd` extra installs geospatial, GerryChain, plotting, notebook, and Streamlit dependencies. The notebook dependency remains available for legacy inspection, but the active MMD workflow is terminal-only.

## MMD Generation

### Active workflow: terminal CLI

Use the script runner at `MMD_Generation_Layer/Processor/main.py`:

```bash
python3 -m MMD_Generation_Layer.Processor.main [OPTIONS]
```

`MMD_Generation_Layer/Processor/main.ipynb` is deprecated and no longer part of the supported workflow. It is retained only as historical material. Do not use it to generate plans, do not add new workflow logic to it, and do not use its saved outputs as evidence of the current pipeline behavior. Use the terminal commands in this section instead.

The CLI options are:

| Option | Purpose |
| --- | --- |
| `--config PATH`, `-c PATH` | Load an optional JSON run configuration. |
| `--skip-plots` | Generate plans and tabular artifacts without the optional seat-share histogram. |
| `--district-csvs` | Write district-level CSV diagnostics after saving assignments. |
| `--dashboard` | Generate artifacts, then launch the Streamlit dashboard. |
| `--dashboard-only` | Launch the dashboard without generating new plans. |
| `--` followed by Streamlit arguments | Pass additional arguments to Streamlit. |

See all options directly from the terminal:

```bash
python3 -m MMD_Generation_Layer.Processor.main --help
```

### MMD command examples

Generate plans using the defaults in `MMD_Generation_Layer/config.py`:

```bash
python3 -m MMD_Generation_Layer.Processor.main
```

Run a small South Carolina MMD configuration:

```bash
python3 -m MMD_Generation_Layer.Processor.main \
  --config MMD_Generation_Layer/Tests/Notebook_Run_Configs/mmd_valid_sc_small.json
```

The `Notebook_Run_Configs/` directory name is historical. Its JSON files are terminal-run configuration fixtures; no notebook is required to use them.

Generate district CSV diagnostics and skip the histogram:

```bash
python3 -m MMD_Generation_Layer.Processor.main \
  --config MMD_Generation_Layer/Tests/Notebook_Run_Configs/mmd_valid_sc_small.json \
  --skip-plots \
  --district-csvs
```

Generate plans and open the dashboard afterward:

```bash
python3 -m MMD_Generation_Layer.Processor.main \
  --config MMD_Generation_Layer/Tests/Notebook_Run_Configs/mmd_valid_sc_small.json \
  --dashboard
```

Open the dashboard without generating plans:

```bash
python3 -m MMD_Generation_Layer.Processor.main --dashboard-only
```

The direct Streamlit command remains available when needed:

```bash
python3 -m streamlit run MMD_Generation_Layer/Client/baseline_dashboard.py
```

### Run configuration

Without `--config`, the runner uses the defaults in `MMD_Generation_Layer/config.py`. A JSON configuration may override:

- `generation_mode`: `SMD` or `MMD`.
- `num_plans`, `num_districts`, and `seed`: positive integers.
- `shape_path`, `id_column`, `geom_column`, `pop_column`, `dem_column`, and `rep_column`.
- `population_tolerance`: a number strictly between `0` and `1`.
- `seat_vector`: a non-empty list of positive integers in MMD mode. Its sum must equal `num_districts`.
- In MMD mode, `seat_vector` must contain at least 2 districts.
- `recom_variant` (default `district_pairs_mst`; also `cut_edges_mst`, `district_pairs_ust`, `cut_edges_ust`), `burn_in_steps` (default `0`), `step_interval` (default `1`), `max_seed_attempts` (default `10`), and `save_seed_plan` (default `false`): native MMD chain controls, ignored in SMD mode.

`mmd_smd_multiplier`, `mmd_plans_per_smd_plan`, `max_mmd_attempts_per_smd_plan`, and `save_intermediate_smd_plans` were removed in the GerryChain 1.0.0 migration and are rejected in either mode; delete them from older configs. The legacy `mmd_seat_vector` key is rejected; use `seat_vector`. Unknown keys are rejected during validation. If a supplied configuration cannot be loaded or validated, the current runner logs warnings and continues with `config.py` defaults.

The current default configuration is an MMD run using North Carolina data, 50 requested final plans, 14 total seats, a `[5, 5, 4]` seat vector, a 5% population tolerance, and the native chain defaults above. The default shape is `MMD_Generation_Layer/Data/Shapefiles/NC/nc_2024_with_population.shp`.

### Current MMD behavior

Since the GerryChain 1.0.0 migration (issue #34), `SMD` mode builds equal-population single-member plans with ReCom and `MMD` mode builds seat-proportional multimember plans with GerryChain's native `MultiMemberReCom`. District label `i` always has `seat_vector[i]` seats.

1. **Targets.** `per_seat_population = total_population / sum(seat_vector)` (about 762,804 for NC). District `i` targets `seat_vector[i] × per_seat_population`.
2. **Population tolerance is per seat.** Every district's population divided by its seats must be within `population_tolerance` of `per_seat_population`.
3. **Seed plan.** A valid starting plan is built at runtime by peeling off one district at a time with GerryChain's unequal-target spanning-tree split: NC `5/5/4` is split `5 | 9`, then `5 | 4`. Every district is contiguous. A failed attempt retries up to `max_seed_attempts`, then stops with a clear error. Code: `build_mmd_seed_assignment(...)` and `create_mmd_seed_partition(...)` in `MMD_Generation_Layer/Processor/mmd_generation.py`.
4. **Chain.** `MultiMemberReCom` (variant chosen by `recom_variant`) repeatedly merges two neighbouring districts and re-splits them in proportion to their seat counts. Seat counts stay attached to district labels; only geography changes. Contiguity and per-seat population are enforced on every plan. Code: `generate_mmd_ensemble(...)`.
5. **Sampling.** The seed is chain step 0 and is never saved. After `burn_in_steps`, every `step_interval`-th plan is saved until `num_plans` plans exist. Defaults (`0`, `1`) save every step; raise them for more independent ensembles.
6. **Reproducibility.** One `random.Random(seed)` drives the seed plan and the chain, so the same config reproduces the same ensemble.

Seats in `baseline_ensemble.csv` are counted winner-take-all per district. That is a display rule for the ensemble summary, not proportional FRA/STV allocation, which belongs to the simulation layer.

The MMD workflow is usable for exploratory research but remains experimental. Research-grade `recom_variant`, `burn_in_steps`, and `step_interval` choices, runtime, and downstream representational/simulation integration still need further work.

### Migrating to GerryChain 1.0.0

- Reinstall dependencies after pulling: `python3 -m pip install -e '.[mmd]'`. GerryChain 1.0.0 requires pandas 3, so pandas, numpy, geopandas, scipy, networkx, and Streamlit move together, and `rustworkx` and `tqdm` are added.
- Delete the removed temporary-SMD keys listed above from old configs.
- Use `num_plans` for the number of saved MMD plans directly; there are no temporary SMD plans anymore.
- Custom GerryChain code must use the 1.0.0 graph API: `graph.node_data(node)[key]` for node attributes, `graph.nodes` / `graph.edges` as properties, and `assignment_by_original_node_id(partition)` to turn `partition.assignment` (internal integer IDs) back into precinct IDs.

### MMD inputs and outputs

The repository currently includes processed precinct shapefiles for NC, SC, TN, and VA under `MMD_Generation_Layer/Data/Shapefiles/<STATE>/`. The current inputs combine 2020 Census population figures with 2024 election results, so that temporal mismatch must be kept in mind when interpreting results.

Each run writes to a state-specific directory:

```text
MMD_Generation_Layer/Outputs/<STATE>/
  baseline_ensemble.csv
  run_metadata.json
  seat_share.png
  Plan_Assignments/plan_<id>.json
  seed_plan.json                                   # optional, MMD with save_seed_plan
  baseline_districts_plan_<id>.csv                 # optional
```

Generated MMD outputs are ignored by the root `.gitignore`. The assignment JSON files map precinct IDs to district IDs and must not be passed directly to the simulation layer as election JSON.

### Population reconstruction utility

`MMD_Generation_Layer/Utils/population_builder.py` reconstructs precinct-level `TOTPOP` from 2020 Census TIGER/Line blocks. It supports a fast point-in-precinct method, a slower area-weighted method, and a comparison mode:

```bash
python3 MMD_Generation_Layer/Utils/population_builder.py \
  --input <precinct-shapefile> \
  --state-fips <two-digit-state-fips> \
  --id-col UNIQUE_ID \
  --output <output-shapefile> \
  --method area
```

Available utility options:

- `--method {point,area,both}`: choose the population allocation method.
- `--compare-to PATH`: compare reconstructed `TOTPOP` against a known population column.
- `--cache-dir PATH`: choose where downloaded Census block files are cached.

Use `--method area` for retained research data when precinct boundaries overlap Census blocks. Use `--method both` to inspect disagreement between methods before relying on close district-level comparisons.

## Dashboard

The Streamlit dashboard is `MMD_Generation_Layer/Client/baseline_dashboard.py`. It discovers completed state folders under `MMD_Generation_Layer/Outputs/`, loads each state's run metadata, lets the user select a plan, renders a district map, shows party seat summaries, plots the ensemble's Democratic seat-share distribution, and displays a plan table.

The dashboard is currently a baseline visualization and still contains SMD/winner-take-all-oriented labels and assumptions. It should not be interpreted as a complete MMD/RCV research dashboard until those labels and metrics are updated to distinguish district count from total seat count and to expose the MMD seat vector.

## Representational Layer

The representational layer models the political inputs that eventually become ranked ballots.

- `Representational_Layer/Src/Representational_Layer/models.py`: dataclasses for experiments, districts, elections, candidates, elector units, preference models, ranking groups, and ballots.
- `Representational_Layer/Src/Representational_Layer/input_contract.py`: strict parser and validator for user-authored experiment contracts.
- `Representational_Layer/Src/Representational_Layer/scoring.py`: candidate similarity and preference scoring.
- `Representational_Layer/Src/Representational_Layer/generation.py`: weighted and profile-based ranking/ballot generation helpers.
- `Representational_Layer/Src/output_writer.py`: thin wrapper for writing simulation-ready JSON through shared utilities.
- `Representational_Layer/Attributes/`: reusable starter attribute vocabulary and defaults.

Top-level compatibility imports are available through `Representational_Layer.models`, `Representational_Layer.generation`, and `Representational_Layer.scoring`.

The layer currently has weighted-random and profile-scoring generation styles. A single orchestration API for configuring an experiment, generating ballots, and exporting simulation-ready JSON remains future work.

## Simulation Layer

The simulation layer runs the FRA counting rules on typed election inputs.

- `Simulation_Layer/Core/models.py`: candidates, rankings, ballots, and elections.
- `Simulation_Layer/Core/config.py`: supported modes and counting defaults.
- `Simulation_Layer/Core/utils.py`: ballot resolution, candidate state, counting, transfer, threshold, and round-log helpers.
- `Simulation_Layer/Runner/main.py`: RCV/STV runners, JSON loading, and the interactive CLI.
- `Simulation_Layer/fra_engine.py`: compatibility shim that re-exports the runner API and supports direct execution.

Run either interactive simulation entrypoint from the repository root:

```bash
python3 Simulation_Layer/fra_engine.py
python3 Simulation_Layer/Runner/main.py
```

Each command prompts for an input JSON path and reports winners, final candidate status, and round details. The simulation layer expects election metadata, candidates, rank-group ballots, and deterministic tie-break information from the shared JSON contract.

## Shared Utilities And Boundaries

`Global_Utilities/` contains behavior shared across layers:

- `Global_Utilities/json_io.py`: resolves `Pipe/` paths and reads/writes simulation-ready JSON.
- `Global_Utilities/logger.py`: `info`, `warn`, `success`, and `error` logging wrappers. Informational messages use bright cyan.

`Pipe/` is the shared handoff area for simulation-ready election JSON:

- `Pipe/input.json`: manual CLI input.
- `Pipe/Acceptance_Test_Cases/*.json`: canonical simulation fixtures.
- `Pipe/test_*_output.json`: simulation-ready exports produced by representational tests.

Keep these boundaries intact. Do not mix representational preference logic into simulation counting, do not duplicate shared models, and do not treat MMD assignment JSON as simulation-ready election data.

## Testing

The configured pytest paths are `Representational_Layer/Tests/`, `Simulation_Layer/Tests/`, and `MMD_Generation_Layer/Tests/`. Run the full suite with the virtual-environment interpreter so the command does not depend on a globally installed `pytest` executable:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
```

Useful focused commands:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q Representational_Layer/Tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q Simulation_Layer/Tests/test_acceptance_e2e.py
python3 Simulation_Layer/Tests/run_acceptance_cli.py
```

The representational tests cover models, scoring, input contracts, ballot generation, and JSON round trips. The simulation acceptance suite covers canonical single-seat and multi-seat edge cases, CLI-visible output, invalid paths, and repeated-run determinism.

The MMD tests (`test_graph_loading.py`, `test_smd_generation.py`, `test_mmd_seed.py`, `test_mmd_chain.py`, `test_mmd_run_config.py`) cover graph loading, SMD generation, seed plans, the native chain, and run-config validation. All except `test_mmd_run_config.py` skip automatically when the `mmd` extra (GerryChain) is not installed:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q MMD_Generation_Layer/Tests
```

`test_mmd_run_config.py` loads every JSON configuration under `MMD_Generation_Layer/Tests/Notebook_Run_Configs/` and checks that each `invalid_*` fixture is rejected; the `*_small` configs are also the quickest end-to-end check through the terminal runner.

## Project Configuration

The root `pyproject.toml` is the single package and tooling configuration for the repository. It defines:

- project metadata and Python `>=3.11` support;
- the `dev` and `mmd` optional dependency groups;
- pytest `pythonpath` and test paths;
- setuptools package mappings for the nonstandard layer layout.

Do not add layer-local `pyproject.toml` or `requirements.txt` files. Install or update dependencies through the root configuration.

## Environment Variables And Constants

No runtime source code currently requires application-specific environment variables. Useful workflow settings are:

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`: reduces unrelated local pytest plugin interference.
- `PYTHONPATH=.:Src`: useful when running representational scripts from `Representational_Layer/`.
- `PYTHONPATH=.:MMD_Generation_Layer`: useful for direct MMD imports from the repository root.

Important configuration lives in:

- `MMD_Generation_Layer/config.py`: paths, default mode, plan counts, seat vector, state columns, seed, tolerances, and native MMD chain controls.
- `Simulation_Layer/Core/config.py`: RCV/STV modes and counting defaults.
- `Global_Utilities/json_io.py`: project root and `Pipe/` resolution.

## Current Limitations And Remaining Work

- The MMD output is a district-generation artifact and is not yet consumed directly by the simulation layer.
- The MMD generator uses GerryChain 1.0.0's native `MultiMemberReCom`; research-grade sampling settings (`recom_variant`, `burn_in_steps`, `step_interval`) and larger-scale performance remain open research work.
- Seat counts in MMD ensemble summaries are winner-take-all per district, not FRA/STV results.
- The included precinct data currently contain population and election results, but not a completed precinct-level race/ethnicity data product. Demographic data must be reconciled from Census blocks or another validated source before racial-dispersion metrics can be trusted.
- The population and election vintages are not time-aligned: current runs combine 2020 Census population with 2024 voting data.
- The current dashboard is a baseline plan viewer, not yet a complete ensemble-wide MMD/RCV analysis interface.
- The representational layer still needs a unified public orchestration API and broader validated voter/candidate attribute support.
- The simulation layer needs additional property, stress, and adversarial ballot-shape testing beyond the canonical fixtures.
- The deprecated notebook should not receive new implementation work.

## Contribution Workflow

Before making a change, read `README.md`, `AGENTS.md`, and the relevant handoff in `Documents/Thread_Handoff/`. Follow the issue-first, branch-first, pull-request workflow in `CONTRIBUTING.md`.

Keep code in the layer that owns it, use shared JSON and logging utilities, add or update tests for behavior changes, and update documentation when commands, outputs, or layer contracts change.

## Repository Map

```text
Global_Utilities/       Shared logging and JSON contract helpers
MMD_Generation_Layer/   Precinct data, terminal generator, dashboard, outputs
Representational_Layer/ Candidate/elector modeling and ballot generation
Simulation_Layer/       FRA RCV/STV models, counting, and CLI
Pipe/                   Simulation-ready JSON handoff and fixtures
Documents/              Canonical README, agent guide, and thread handoffs
pyproject.toml          Root package, dependency, and pytest configuration
CONTRIBUTING.md         Issue, branch, review, and contribution workflow
```

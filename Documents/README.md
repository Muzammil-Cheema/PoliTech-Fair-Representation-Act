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
- `mmd_smd_multiplier`, `mmd_plans_per_smd_plan`, and `max_mmd_attempts_per_smd_plan`: positive integers controlling temporary SMD generation and MMD search.
- `save_intermediate_smd_plans`: a boolean that saves temporary SMD assignments during MMD generation.

The legacy `mmd_seat_vector` key is rejected; use `seat_vector`. Unknown keys are rejected during validation. If a supplied configuration cannot be loaded or validated, the current runner logs warnings and continues with `config.py` defaults.

The current default configuration is an MMD run using North Carolina data, 50 requested final plans, 14 total seats, a `[5, 5, 4]` seat vector, a 5% population tolerance, and five requested MMD plans per temporary SMD plan with up to ten search attempts per source plan. The default shape is `MMD_Generation_Layer/Data/Shapefiles/NC/nc_2024_with_population.shp`.

### Current MMD behavior

The script workflow currently:

1. Loads precinct geodata and validates the configured ID, geometry, population, and Democratic/Republican vote columns.
2. Generates temporary contiguous equal-population SMD plans with GerryChain/ReCom.
3. Groups temporary SMD units into contiguous MMDs using the requested `seat_vector`.
4. Enforces seat-weighted population targets for the resulting MMDs.
5. Deduplicates MMD plans within each temporary SMD source plan.
6. Saves assignments, summaries, metadata, and optional diagnostics.

The MMD workflow is usable for exploratory research but remains experimental. Proposal quality, plan diversity, runtime, and downstream representational/simulation integration still need further work.

### MMD inputs and outputs

The repository currently includes processed precinct shapefiles for NC, SC, TN, and VA under `MMD_Generation_Layer/Data/Shapefiles/<STATE>/`. The current inputs combine 2020 Census population figures with 2024 election results, so that temporal mismatch must be kept in mind when interpreting results.

Each run writes to a state-specific directory:

```text
MMD_Generation_Layer/Outputs/<STATE>/
  baseline_ensemble.csv
  run_metadata.json
  seat_share.png
  Plan_Assignments/plan_<id>.json
  Intermediate_SMD_Plans/smd_plan_<id>.json       # optional
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

The configured pytest paths are `Representational_Layer/Tests/` and `Simulation_Layer/Tests/`. Run the full suite with the virtual-environment interpreter so the command does not depend on a globally installed `pytest` executable:

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

MMD JSON configurations under `MMD_Generation_Layer/Tests/Notebook_Run_Configs/` are runtime fixtures, not pytest tests. Validate them through the terminal runner with the MMD CLI.

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

- `MMD_Generation_Layer/config.py`: paths, default mode, plan counts, seat vector, state columns, seed, tolerances, and MMD search limits.
- `Simulation_Layer/Core/config.py`: RCV/STV modes and counting defaults.
- `Global_Utilities/json_io.py`: project root and `Pipe/` resolution.

## Current Limitations And Remaining Work

- The MMD output is a district-generation artifact and is not yet consumed directly by the simulation layer.
- The MMD generator uses temporary SMD ReCom plans followed by a custom contiguous BFS merge strategy; native proposal strategies and larger-scale performance remain open research work.
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

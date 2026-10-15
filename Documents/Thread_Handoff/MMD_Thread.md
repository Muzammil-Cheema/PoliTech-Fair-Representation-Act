# MMD Thread

## Purpose

This thread is the MMD-focused implementation and maintenance thread for the FRA project.

Its job is to handle work related to the multi-member district generation layer, especially:

- `MMD_Generation_Layer/`
- packaging or import issues that block MMD notebooks or dashboards
- path handling for MMD data, outputs, and config
- environment setup needed specifically for MMD generation work
- keeping the MMD notebook and dashboard runnable inside the repo venv

This thread is not the owner of the representational or simulation logic, except when small cross-layer edits are required to keep MMD-related workflows installable and runnable.

## Primary Scope

This thread should treat the following as its main area of responsibility:

- `MMD_Generation_Layer/config.py`
- `MMD_Generation_Layer/Processor/` script modules (`main.py`, `runtime_setup.py`, `generation_logic.py`, `mmd_generation.py`, `output_artifacts.py`)
- `MMD_Generation_Layer/Tests/` (pytest suite and `Notebook_Run_Configs/` fixtures)
- `MMD_Generation_Layer/Client/baseline_dashboard.py`
- `MMD_Generation_Layer/Processor/main.ipynb` (legacy; see below)
- MMD-related package setup in `pyproject.toml`
- MMD-related environment and import cleanup in the repo venv

It may also touch shared files when necessary for MMD execution, especially:

- `pyproject.toml`
- `Global_Utilities/`
- `Representational_Layer/`
- `Simulation_Layer/`

But only when those edits are directly in service of making MMD generation work correctly.

## What Was Done In This Thread

This thread investigated and fixed the editable install and import problems that were blocking `MMD_Generation_Layer/Processor/main.ipynb`.

Key fixes:

- corrected package configuration in `pyproject.toml` so editable installs build from the real repo structure
- added proper package entry points for `MMD_Generation_Layer` and `Simulation_Layer`
- added a facade for `Representational_Layer` so imports resolve consistently in plain Python and in notebooks
- removed fragile `sys.path` mutation from several library modules
- updated `MMD_Generation_Layer/Client/baseline_dashboard.py` to import `MMD_Generation_Layer.config` directly
- updated `MMD_Generation_Layer/Processor/main.ipynb` to use `%pip install -e "../..[mmd]"` and package-qualified config imports
- cleaned stale editable-install contamination from `.venv` and reinstalled the project from the correct repo path

## GerryChain 1.0.0 Native MMD Migration (Issue #34)

Branch `feat/gerrychain-native-mmd-generation` replaced the temporary-SMD-to-MMD merge workflow with GerryChain 1.0.0's native multimember generation:

- `gerrychain==1.0.0` in the `mmd` extra; pandas 3, numpy, geopandas, scipy, networkx, and Streamlit (1.56.0) pins moved together; `rustworkx` and `tqdm` added.
- GerryChain 1.0.0 graph API: `graph.node_data(node)[key]`; `graph.nodes` / `graph.edges` are properties; `partition.assignment` uses internal integer IDs, translated back with `assignment_by_original_node_id(partition)` before plans are saved.
- `mmd_generation.py` builds a seat-proportional seed plan at runtime (peel one district at a time: NC `5/5/4` is `5 | 9`, then `5 | 4`), validates it, then runs `MultiMemberReCom` with per-seat population and contiguity constraints.
- New config keys: `recom_variant`, `burn_in_steps`, `step_interval`, `max_seed_attempts`, `save_seed_plan`. Removed and rejected: `mmd_smd_multiplier`, `mmd_plans_per_smd_plan`, `max_mmd_attempts_per_smd_plan`, `save_intermediate_smd_plans`.
- `SMD` mode keeps equal-population ReCom, now with an explicit `random.Random(seed)` and `pair_selection="cut_edges"` to match GerryChain 0.3.2 behavior.

## Current Expected Environment

The live repo for this project work is:

`/Users/fuzi_x_muzi/Documents/PoliTech Research/Politech-Fair-Representation-Act`

The important assumption is that MMD work should run from the repo `.venv`, not from a system Python and not from an older copied repo.

Expected setup:

- activate `.venv`
- install with `python -m pip install -e '.[mmd]'`
- use the `.venv` kernel in Jupyter

## Current MMD Notebook Expectations

`MMD_Generation_Layer/Processor/main.ipynb` is the legacy prototype. It does not run under GerryChain 1.0.0 (it uses the 0.3.2 graph API and the removed temporary-SMD workflow) and has a notice cell at the top. Use `python -m MMD_Generation_Layer.Processor.main --config <config.json>` instead. Migrating, wrapping, or deleting the notebook is a follow-up decision.

## Known Risks And Watchouts

- There is still a checked-in `fair_representation_act.egg-info/` directory at repo root. It is generated metadata, not source-of-truth configuration.
- There was an older copied repo with a similar name that previously contaminated editable installs. If imports start resolving to the wrong project path again, check `.venv/lib/python3.14/site-packages/__editable__*.pth`.
- `main.ipynb` may still contain stale saved output from earlier failures even though the code cells were corrected.
- MMD code depends on geospatial packages, so environment issues may still come from platform package compatibility rather than project code.
- After the GerryChain 1.0.0 migration everyone must reinstall `.[mmd]`; branches still pinned to GerryChain 0.3.2 will not run in a 1.0.0 environment.
- An invalid run config (including one with removed keys) logs the error and falls back to the NC defaults instead of stopping; check the log before trusting outputs.
- `feature/mmd-state-scoped-outputs` changes output paths in `config.py` and `runtime_setup.py`; whichever branch merges second needs a careful conflict resolution there.
- Dashboard under Streamlit 1.56: the Summary Stats table logs an Arrow conversion warning (mixed-type column) and `use_container_width` is deprecated; both render fine.

## What This Thread Should Do Next

Good next tasks for the successor MMD thread:

1. choose research-grade defaults for `recom_variant`, `burn_in_steps`, and `step_interval` using full-size runs
2. decide whether to migrate, wrap, or delete the legacy notebook
3. decide whether invalid run configs should stop the run instead of falling back to defaults
4. tighten `.gitignore` and remove checked-in generated packaging artifacts if requested
5. keep MMD-specific setup isolated from representational and simulation feature work

## What This Thread Should Not Own

This thread should not become the default owner for:

- Git staging, commit grouping, or push workflows
- broad representational-layer feature design
- simulation-counting logic changes unrelated to MMD execution
- non-MMD documentation cleanup unless it affects MMD onboarding directly

## Verification Already Performed

The following checks were already run successfully in this thread:

- editable install rebuild in the repo `.venv`
- plain interpreter import checks for the package aliases used by the project
- pytest coverage for:
  - `Representational_Layer/Tests/test_models.py`
  - `Representational_Layer/Tests/test_scoring.py`
  - `Representational_Layer/Tests/test_profile_based_ballot_generation.py`
  - `Representational_Layer/Tests/test_json_io.py`
  - `Simulation_Layer/Tests/test_acceptance_e2e.py`

Result: 38 tests passed.

For the GerryChain 1.0.0 migration (October 2026): the full suite passed with `149 passed`, including the MMD suite in `MMD_Generation_Layer/Tests/`; the small SC, TN, VA MMD configs and the SMD debug config ran end to end; and the dashboard rendered native MMD output without exceptions.

## Handoff Summary

If a future thread is acting as the MMD thread for this repo, its responsibility is to keep the MMD generation workflow runnable, packaged correctly, and isolated from path/import drift.

It should behave like the thread that protects the MMD notebook, dashboard, and environment from breaking when work is moved across projects or copied between repos.

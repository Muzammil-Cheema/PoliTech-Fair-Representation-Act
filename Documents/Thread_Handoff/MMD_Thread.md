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
- `MMD_Generation_Layer/Processor/main.ipynb`
- `MMD_Generation_Layer/Client/baseline_dashboard.py`
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

## Current Expected Environment

The live repo for this project work is:

`/Users/fuzi_x_muzi/Documents/PoliTech Research/Politech-Fair-Representation-Act`

The important assumption is that MMD work should run from the repo `.venv`, not from a system Python and not from an older copied repo.

Expected setup:

- activate `.venv`
- install with `python -m pip install -e '.[mmd]'`
- use the `.venv` kernel in Jupyter

## Current MMD Notebook Expectations

For `MMD_Generation_Layer/Processor/main.ipynb`, the successor thread should expect:

- the first install cell uses `%pip`, not `!pip`
- config imports should come from `MMD_Generation_Layer.config`
- failures related to `import config` usually mean the notebook has stale saved cells or a stale kernel
- failures related to package imports usually mean the wrong kernel or wrong repo path is in use

## Known Risks And Watchouts

- There is still a checked-in `fair_representation_act.egg-info/` directory at repo root. It is generated metadata, not source-of-truth configuration.
- There was an older copied repo with a similar name that previously contaminated editable installs. If imports start resolving to the wrong project path again, check `.venv/lib/python3.14/site-packages/__editable__*.pth`.
- `main.ipynb` may still contain stale saved output from earlier failures even though the code cells were corrected.
- MMD code depends on geospatial packages, so environment issues may still come from platform package compatibility rather than project code.

## What This Thread Should Do Next

Good next tasks for the successor MMD thread:

1. verify the MMD notebook runs start-to-finish in the repo `.venv`
2. clear stale notebook output if the user wants a cleaner artifact
3. test the Streamlit dashboard entry point
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

## Handoff Summary

If a future thread is acting as the MMD thread for this repo, its responsibility is to keep the MMD generation workflow runnable, packaged correctly, and isolated from path/import drift.

It should behave like the thread that protects the MMD notebook, dashboard, and environment from breaking when work is moved across projects or copied between repos.

# Global Thread Handoff

## Role

This is the Global thread for the Fair Representation Act project. Its job is to own shared project infrastructure and cross-layer coordination, not layer-specific modeling logic. Treat this thread as responsible for:

- `Global_Utilities/`
- root `pyproject.toml`
- root `.gitignore`
- shared `Pipe/` JSON handoff behavior
- naming and project-structure conventions
- files or behavior that are shared by more than one layer

The three layer-specific threads should own their own internal logic:

- `MMD_Generation_Layer/`: district-plan generation, geospatial inputs, ensemble outputs, and dashboarding.
- `Representational_Layer/`: candidate/elector profiles, scoring, ranking, ballot objects, and simulation-ready export calls.
- `Simulation_Layer/`: FRA counting rules, election model validation, acceptance tests, and CLI execution.

## Current Project Shape

The repository currently has three main layers plus shared utilities:

```text
Global_Utilities/
MMD_Generation_Layer/
Pipe/
Representational_Layer/
Simulation_Layer/
```

Important root files:

- `AGENTS.md`: compatibility symlink to `Documents/AGENTS.md`. The operating manual must stay synchronized with code changes.
- `README.md`: compatibility symlink to `Documents/README.md`.
- `pyproject.toml`: single project-level Python config for tests, package mappings, and optional dependencies.
- `.gitignore`: single root ignore file. Avoid reintroducing layer-local `.gitignore` files unless there is a strong reason.
- `Documents/`: canonical home for project markdown docs and thread handoffs.

## Naming Convention

Current convention:

- No spaces in project-owned file or directory names.
- Directories use capitalized words separated by underscores, for example `Representational_Layer/`.
- Files use lowercase words separated by underscores, for example `test_acceptance_e2e.py`.
- `AGENTS.md` and `README.md` are explicit exceptions because conventional tooling expects those names; in this repo they are root symlinks into `Documents/`.

If copied-in project files violate this convention, normalize them and update imports/path references immediately.

## Shared Utilities

### `Global_Utilities/logger.py`

Provides colored terminal logging:

- `info(message: str)` -> bright blue `[INFO] ?`
- `warn(message: str)` -> bright yellow `[WARN] !`
- `success(message: str)` -> bright green `[SUCCESS] :)`
- `error(message: str)` -> bright red `[ERROR] !!!` and exits with status `1`

Simulation runtime code uses this instead of direct `print(...)` for runtime messages. The logger itself still uses `print(...)` internally.

### `Global_Utilities/json_io.py`

This is the shared JSON boundary between representation and simulation.

Public functions:

- `resolve_pipe_path(path, project_root=None) -> Path`
- `write_simulation_ready_json(output_path, test_name, ballots, candidates, metadata) -> Path`
- `read_simulation_ready_json(path) -> SimulationJsonObjects`

The writer accepts typed representational objects by protocol and serializes simulation-ready JSON. The reader returns a typed tuple that the simulation layer can work with directly:

```python
(
    election_id,
    seat_count,
    mode,
    candidates,
    ballots,
    tie_break_order,
    max_ranks_allowed,
)
```

The reader resolves relative paths through `Pipe/`, validates required metadata, converts candidate/ballot dictionaries into simulation `Candidate`, `Ballot`, and `Ranking` objects, and routes failures through `error(...)`.

Important boundary principle: JSON read/write behavior should live here, not inside core representation or simulation logic.

## `Pipe/`

`Pipe/` is the shared handoff area for simulation-ready election JSON.

Current contents include:

- `Pipe/input.json`
- `Pipe/Acceptance_Test_Cases/*.json`
- `Pipe/test_*_output.json`

The simulation acceptance test recursively scans runnable election JSON under `Pipe/`, while skipping manifest/non-election JSON such as acceptance indexes.

Do not treat MMD output JSON as simulation-ready election JSON. MMD `Plan_Assignments/*.json` maps precinct IDs to district IDs, not ballots/candidates/election metadata.

## Root `pyproject.toml`

There is one root `pyproject.toml`. Do not recreate layer-local `pyproject.toml` or `requirements.txt` files.

Current responsibilities:

- Project metadata.
- `dev` optional dependency group for pytest.
- `mmd` optional dependency group migrated from the old MMD `requirements.txt`.
- `pytest` config with root-level `pythonpath` and `testpaths`.
- setuptools package mappings for the nonstandard layer layout.

Common install commands:

```bash
python -m pip install -e ".[dev]"
python -m pip install -e ".[mmd]"
python -m pip install -e ".[dev,mmd]"
```

Common test command:

```bash
python -m pytest
```

If using the repo virtualenv directly:

```bash
./.venv/bin/python -m pytest
```

## Root `.gitignore`

The root `.gitignore` owns ignored metadata and generated artifacts. It includes:

- Python cache files
- local virtualenvs
- pytest cache
- Jupyter checkpoints
- macOS `.DS_Store`
- JetBrains workspace metadata
- MMD generated outputs under `MMD_Generation_Layer/Outputs/`

Be careful not to add broad ignores like `*.json` or `*.csv`, because the repo intentionally tracks `Pipe/` fixtures and some data artifacts.

## Current MMD Integration State

The MMD layer was copied from its own repo and normalized into:

```text
MMD_Generation_Layer/
  Client/
  Data/
  Outputs/
  Processor/
  config.py
```

Cleanup already done:

- Removed nested `.git`.
- Removed copied `.gitignore`.
- Removed copied `requirements.txt`.
- Moved requirements into root `pyproject.toml` under `[project.optional-dependencies].mmd`.
- Removed caches/checkpoints.
- Renamed directories to match convention.
- Updated `MMD_Generation_Layer/config.py` paths to `Processor`, `Data/Shapefiles`, `Outputs`, and `Outputs/Plan_Assignments`.

`MMD_Generation_Layer/Outputs/` is currently ignored because it is generated output.

## Current Test State

The last known full test command was:

```bash
./.venv/bin/python -m pytest
```

Expected result at handoff time:

```text
38 passed
```

The MMD dashboard files were also compile-checked after migration:

```bash
python3 -m py_compile MMD_Generation_Layer/config.py MMD_Generation_Layer/Client/baseline_dashboard.py
```

## Known Global Risks

- The project uses capitalized package/directory names (`Global_Utilities`, `Simulation_Layer`, etc.). Imports must match exact casing.
- `Global_Utilities/json_io.py` imports simulation models. Avoid introducing circular imports through package barrels.
- `error(...)` exits the process. Do not use it in code paths where tests need to assert recoverable exceptions unless that behavior is explicitly intended.
- `Pipe/` and MMD outputs both contain JSON, but they mean different things. Only `Pipe/` JSON should be simulation election JSON.
- Markdown docs may be managed by a separate documentation thread, but `AGENTS.md` says it must remain aligned after code changes.

## Likely Next Global Tasks

- Keep `pyproject.toml` current as MMD code becomes more package-like.
- Decide whether MMD notebooks should remain as notebooks only or be extracted into importable Python modules.
- Add shared path utilities if more layers need stable root/layer path resolution.
- Consider whether `Global_Utilities/json_io.py` should gain schema/version metadata for simulation handoff files.
- Keep root `.gitignore` scoped narrowly so important fixtures and data are not accidentally hidden.

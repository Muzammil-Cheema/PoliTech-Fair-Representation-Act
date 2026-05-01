# Getting Started

## For Humans: How To Work In This Repo

This repository has two separate code layers that should stay separate:

- `Representational Layer/`: generates candidates and ranked ballots.
- `Simulation Layer/`: consumes election JSON and runs FRA counting rules.

The fastest way to avoid regressions is to treat those as separate products with a shared JSON boundary.

## Best-Practice Structure

- Keep representational experiments in `Representational Layer/src/representational_layer/`.
- Keep simulation counting logic in `Simulation Layer/`.
- Use `global_utilities/json_io.py` for JSON contracts between layers.
- Use `global_utilities/logger.py` wrappers (`info/warn/success/error`) for runtime messaging.
- Keep reusable attribute vocabulary in `attributes/starter_attributes.py`.
- Put generated handoff JSON in `pipe/` through the JSON helpers.

## What Already Exists (Do Not Duplicate)

- Data models:
  - Representational models in `Representational Layer/src/representational_layer/models.py`
  - Simulation models in `Simulation Layer/core/models.py`
- Scoring logic:
  - `Representational Layer/src/representational_layer/scoring.py`
- Ballot generation helpers:
  - `Representational Layer/src/representational_layer/generation.py`
- Simulation-ready JSON writers/readers:
  - `global_utilities/json_io.py`
  - `Representational Layer/src/output_writer.py` (thin wrapper for representational tests)
- Acceptance fixtures:
  - `pipe/acceptance_test_cases/*.json`

Before adding a new utility, search for it first with `rg`.

## Daily Workflow

1. `cd "Representational Layer"`
2. Activate env: `source ../.venv/bin/activate` (or local env equivalent)
3. Run tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`
4. Generate/refresh simulation-ready JSON through `write_simulation_ready_output(...)` or `write_simulation_ready_json(...)`.

## Practical Tips

- Keep ballots in rank-group format (`rank` + `candidate_ids`), not flat lists.
- Always include deterministic metadata (`election_id`, `seat_count`, `mode`, `tie_break_order`) when writing handoff JSON.
- Favor small, composable functions over monolithic test logic.
- If adding output files, route them through shared JSON helpers so simulation ingestion remains stable.
- If changing scoring semantics, update tests and the shared attribute vocabulary together.

## Common Pitfalls

- Mixing representational profile logic into simulation counting code.
- Writing ad-hoc JSON schemas that bypass `global_utilities/json_io.py`.
- Using `print` directly in library/runtime flow instead of logger wrappers.
- Adding duplicate model classes in new files.

## Current Test Entry Points

- `Representational Layer/tests/test_models.py`
- `Representational Layer/tests/test_scoring.py`
- `Representational Layer/tests/test_profile_based_ballot_generation.py`
- `Representational Layer/tests/test_json_io.py`

## Where Visualization Should Plug In Later

When you add visualization, consume outputs from:

- `score_candidates_for_elector_unit(...)` (candidate score traces)
- simulation-ready JSON outputs in `pipe/` (ballot and candidate payloads)

This keeps charts decoupled from core scoring/counting logic.

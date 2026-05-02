# Getting Started

## For Humans: How To Work In This Repo

This repository has two separate code layers that should stay separate:

- `Representational_Layer/`: generates candidates and ranked ballots.
- `Simulation_Layer/`: consumes election JSON and runs FRA counting rules.

The fastest way to avoid regressions is to treat those as separate products with a shared JSON boundary.

## Best-Practice Structure

- Keep representational experiments in `Representational_Layer/Src/Representational_Layer/`.
- Keep simulation counting logic in `Simulation_Layer/`.
- Use `Global_Utilities/json_io.py` for JSON contracts between layers.
- Use `Global_Utilities/logger.py` wrappers (`info/warn/success/error`) for runtime messaging.
- Keep reusable attribute vocabulary in `Representational_Layer/Attributes/starter_attributes.py`.
- Put generated handoff JSON in `Pipe/` through the JSON helpers.

## What Already Exists (Do Not Duplicate)

- Data models:
  - Representational models in `Representational_Layer/Src/Representational_Layer/models.py`
  - Simulation models in `Simulation_Layer/Core/models.py`
- Scoring logic:
  - `Representational_Layer/Src/Representational_Layer/scoring.py`
- Ballot generation helpers:
  - `Representational_Layer/Src/Representational_Layer/generation.py`
- Simulation-ready JSON writers/readers:
  - `Global_Utilities/json_io.py`
  - `Representational_Layer/Src/output_writer.py` (thin wrapper for representational tests)
- Acceptance fixtures:
  - `Pipe/Acceptance_Test_Cases/*.json`

Before adding a new utility, search for it first with `rg`.

## Daily Workflow

1. `cd "Representational_Layer"`
2. Activate env: `source ../.venv/bin/activate` (or local env equivalent)
3. Run tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`
4. Generate/refresh simulation-ready JSON through `write_simulation_ready_output(...)` or `write_simulation_ready_json(...)`.

## Environment Variables And Globals

### Environment variables

- Required by source code: none currently required.
- Common workflow variables:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` for stable test runs.
  - `PYTHONPATH=.:Src` for direct script execution from `Representational_Layer/`.

### Global constants

- `Global_Utilities/json_io.py`: `PROJECT_ROOT`, `SIMULATION_ROOT`, `PIPE_DIR_NAME`
- `Global_Utilities/logger.py`: `RESET`, `BLUE`, `GREEN`, `RED`, `YELLOW`
- `Simulation_Layer/Core/config.py`: `MODE_SINGLE_SEAT_RCV`, `MODE_MULTI_SEAT_STV`, `VALID_MODES`, `DEFAULT_TRANSFER_VALUE`, `DEFAULT_ENCODING`
- `Simulation_Layer/fra_engine.py`: `SIMULATION_ROOT`, `PROJECT_ROOT`
- `Simulation_Layer/Runner/main.py`: `PROJECT_ROOT`
- `Representational_Layer/Src/output_writer.py`: `PROJECT_ROOT`

## Practical Tips

- Keep ballots in rank-group format (`rank` + `candidate_ids`), not flat lists.
- Always include deterministic metadata (`election_id`, `seat_count`, `mode`, `tie_break_order`) when writing handoff JSON.
- Favor small, composable functions over monolithic test logic.
- If adding output files, route them through shared JSON helpers so simulation ingestion remains stable.
- If changing scoring semantics, update tests and the shared attribute vocabulary together.

## Common Pitfalls

- Mixing representational profile logic into simulation counting code.
- Writing ad-hoc JSON schemas that bypass `Global_Utilities/json_io.py`.
- Using `print` directly in library/runtime flow instead of logger wrappers.
- Adding duplicate model classes in new files.

## Current Test Entry Points

- `Representational_Layer/Tests/test_models.py`
- `Representational_Layer/Tests/test_scoring.py`
- `Representational_Layer/Tests/test_profile_based_ballot_generation.py`
- `Representational_Layer/Tests/test_json_io.py`

## Where Visualization Should Plug In Later

When you add visualization, consume outputs from:

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
- `Global_Utilities/logger.py` currently uses `print` internally for output formatting. This is acceptable for now, but if structured observability is needed later, this should move to Python `logging` handlers.

### What is left to do

1. Simulation-layer correctness and robustness (top priority):
   - expand beyond fixture-style acceptance tests into stress/property testing
   - add adversarial/fuzz ballot-shape tests (deep skips, large same-rank groups, repeated ranks at scale)
   - verify deterministic tie behavior persists cleanly across replay/recount workflows
   - improve invariant checks and failure diagnostics around transfer-value and threshold transitions
2. Representational-layer API simplification:
   - expose one orchestration entrypoint for: scoring -> ranking -> ballot objects -> simulation JSON export
   - keep per-method behavior selectable (`deterministic_sort`, weighted, softmax) behind that single entrypoint
3. Vocabulary maturity:
   - continue expanding and versioning shared attribute specs in `Representational_Layer/Attributes/`
   - formalize weight presets and missing-value policies for reproducible experiments
4. Visualization support:
   - add reusable export shape for plotting round-by-round candidate utilities and ballot distributions
   - produce starter notebooks or scripts for score and ranking diagnostics
5. Documentation alignment:
   - keep `AGENTS.md` synchronized with each code change
   - keep simulation handoff examples in `Pipe/` aligned with current writer/readers

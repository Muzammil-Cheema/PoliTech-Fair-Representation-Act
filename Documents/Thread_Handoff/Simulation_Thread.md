# Simulation Layer 1 Thread Handoff

## Thread Role
This thread owns the **Simulation Layer** for the Fair Representation Act (FRA) work:
- implement and debug tabulation logic,
- keep counting behavior aligned with FRA rules (single-seat RCV + multi-seat STV),
- improve modularity/readability/testability,
- maintain the process boundary with the Representational Layer via shared JSON helpers.

## Current Project Layout (relevant areas)
- `Simulation_Layer/`
  - `Core/` (models/config)
  - `Helpers/` (edge cases + counting/transfer helpers)
  - `Runner/` (main simulation driver)
  - `Tests/` (acceptance/e2e coverage)
- `Representational_Layer/` (ballot/candidate generation + tests)
- `Global_Utilities/` (shared JSON IO + logger)
- `Pipe/` (shared process boundary directory for simulation input/output)

## What This Thread Already Completed

### 1) Simulation modularization
The former monolithic simulation logic was split into:
- `Simulation_Layer/Core/*`
- `Simulation_Layer/Helpers/*`
- `Simulation_Layer/Runner/main.py`

### 2) Shared JSON IO boundary
Both layers now read/write simulation JSON through `Global_Utilities/json_io.py`.
- Representational output defaults into `Pipe/`.
- Simulation input resolves through `Pipe/` for relative paths.
- Layer logic is no longer doing ad hoc JSON serialization/parsing.

### 3) Major STV correctness fixes
Implemented the following findings-driven fixes:
- **Surplus transfer ownership fix (P1)**  
  Transfer updates now apply to ballots that were actually allocated to the elected candidate in that round snapshot.
- **Simultaneous surplus distribution fix (P1)**  
  Surplus fractions are computed from the round snapshot and then applied in one simultaneous update pass.
- **Round auditability improvement (P2)**  
  Round logs now include `ballot_allocations`.
- **Round numbering fix (P2)**  
  `fill_remaining_seats` now increments round number before logging.
- **Policy isolation (P3)**  
  Transfer policy units were extracted into helper functions.

## Transfer/Counting Notes
- Round allocation now comes from `count_votes_single_round(...)`.
- STV flow now:
  1. count + capture ballot allocations
  2. elect threshold-meeting candidates
  3. build surplus fractions
  4. apply simultaneous transfer-value updates from allocation snapshot
  5. recount and continue

## Round Log Shape
Each round can include:
- `round`
- `vote_totals`
- `status`
- `action`
- `threshold` (STV)
- `ballot_allocations` (for auditing transfer correctness)

## Test Status at Last Known Good Point
- `Simulation_Layer/Tests/test_acceptance_e2e.py`: passing
- `Representational_Layer/Tests`: passing
- Full suite: passing

## Recommended Next Tasks
1. Add tighter unit tests directly around transfer-policy helpers.
2. Consider making election execution fully non-mutating/pure to avoid rerun-state contamination.
3. Keep the `Pipe` + `Global_Utilities/json_io.py` contract stable while future refactors continue.
4. If needed, do naming/casing/path cleanup as a dedicated migration with test coverage.

## Quick Commands
From project root:

```bash
PYTHONPATH='.:Simulation_Layer:Representational_Layer/Src' .venv/bin/pytest Simulation_Layer/Tests/test_acceptance_e2e.py -q
PYTHONPATH='.:Representational_Layer/Src' .venv/bin/pytest Representational_Layer/Tests -q
PYTHONPATH='.:Simulation_Layer:Representational_Layer/Src' .venv/bin/pytest -q
```

## Scope Reminder
Any task involving simulation correctness, transfer semantics, round logging, or simulation-side JSON contract behavior belongs to this Simulation Layer thread.

---

# Simulation Layer 2 Addendum (Parallel Thread)

## Purpose
This addendum captures work from the second simulation thread, which focused on runtime error triage before making code changes.

## What Thread 2 Validated
1. Simulation entrypoints were exercised with real JSON fixtures through:
   - `Simulation Layer/runner/main.py`
   - `Simulation Layer/fra_engine.py`
2. Election runs completed successfully when file paths were passed in the expected form.
3. The thread intentionally made no code changes during triage.

## Additional Findings Not Captured Above
1. **`resolve_pipe_path(...)` has a double-`pipe` failure mode**
   - Current relative-path behavior prepends `pipe/`.
   - If user input already includes `pipe/` (example: `pipe/input.json`), resolution becomes `pipe/pipe/input.json` and fails.
   - Recommended contract direction from user: do not auto-prepend `pipe/`; require callers to pass the exact intended path.

2. **CLI exception block can be misleading**
   - `run_cli()` uses `except Exception` around JSON load.
   - Shared `error(...)` exits via `sys.exit(1)` (`SystemExit`), so many invalid-input cases bypass that `except Exception` block.
   - This is primarily a control-flow clarity issue; user indicated immediate exit is acceptable if error messaging remains clear.

## Recommended Follow-Through Tasks
1. Implement `resolve_pipe_path(...)` path-contract simplification (no implicit `pipe/` prefixing for relative paths).
2. Add regression coverage for `pipe/input.json` vs `input.json` handling so double-prefix behavior cannot reappear.
3. Decide and document one explicit CLI failure policy:
   - continue using immediate exits via `error(...)`, or
   - refactor toward exception propagation that `run_cli()` catches directly.
4. Align all docs/examples to one path convention for simulation input arguments.

## Migration Caution
Some active branches used `Simulation Layer/` (space-separated) while older notes use `Simulation_Layer/` (underscored). Before running commands from this handoff, verify actual directory names in the target repo clone and update command examples if needed.

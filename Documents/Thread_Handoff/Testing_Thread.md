# Testing Thread

## Purpose

This thread is the testing-focused support thread for the FRA project.

Its job is to own:

- writing and updating `pytest` coverage
- building modular test infrastructure that is easy to run and extend
- turning spec requirements into executable test cases
- validating CLI behavior and output for the simulation layer
- organizing JSON fixtures so other threads can reuse them
- tightening assertions when implementation details become stable

It is not the main architecture or feature-design thread. Its role is to help the rest of the project move safely by making behavior testable, visible, and easy to verify.

## Current Scope

The main testing work completed so far is in the simulation layer.

Key areas this thread has worked on:

- creating acceptance-style election fixtures under `Pipe/Acceptance_Test_Cases/`
- writing end-to-end `pytest` coverage for those fixtures in `Simulation_Layer/Tests/test_acceptance_e2e.py`
- exercising the simulation through the CLI path via `run_cli()` rather than only through internal function calls
- parsing captured CLI output so tests can assert winners, final statuses, round actions, thresholds, and vote totals
- helping expose simulation bugs through tests, including STV transfer behavior around zero-surplus elections

## Important Files

Primary files the next testing thread should know:

- [Simulation_Layer/Tests/test_acceptance_e2e.py](/Users/fuzi_x_muzi/Documents/PoliTech%20Research/Politech-Fair-Representation-Act/Simulation_Layer/Tests/test_acceptance_e2e.py)
- [Pipe/Acceptance_Test_Cases](/Users/fuzi_x_muzi/Documents/PoliTech%20Research/Politech-Fair-Representation-Act/Pipe/Acceptance_Test_Cases)
- [Simulation_Layer/Runner/main.py](/Users/fuzi_x_muzi/Documents/PoliTech%20Research/Politech-Fair-Representation-Act/Simulation_Layer/Runner/main.py)
- [README.md](/Users/fuzi_x_muzi/Documents/PoliTech%20Research/Politech-Fair-Representation-Act/Documents/README.md)
- [AGENTS.md](/Users/fuzi_x_muzi/Documents/PoliTech%20Research/Politech-Fair-Representation-Act/Documents/AGENTS.md)

## Current Testing Design

The acceptance suite currently takes the simplest maintainable path:

- tests call `run_cli()` directly
- `pytest` uses `monkeypatch` to replace `input()` with the fixture path
- `capsys` captures the normal CLI output
- helper logic strips ANSI color codes and parses the printed transcript into structured data
- tests then assert against parsed winners, round logs, thresholds, actions, and final statuses

This means the tests still exercise the CLI contract, but without subprocess complexity.

## Fixture Model

The acceptance fixtures are simple election JSON files that model the simulation input contract directly.

They cover scenarios such as:

- ordinary single-seat elimination
- withdrawn candidates
- two-candidate single-seat completion
- STV threshold election
- simultaneous STV threshold elections
- STV elimination rounds
- undervotes
- inactive ballots
- skipped rankings
- repeated candidate rankings
- same-rank ambiguity
- deterministic tie-break behavior
- seat-fill completion behavior
- exact-threshold surplus behavior

These fixtures are intended to be reusable across simulation work, not just one-off test inputs.

## How To Run Tests

Preferred command in this repo:

```bash
.venv/bin/python -m pytest 'Simulation_Layer/Tests/test_acceptance_e2e.py' -q
```

If running the broader suite later:

```bash
.venv/bin/python -m pytest -q
```

The local `.venv` exists because the system Python environment was not reliable for installing or running `pytest` directly.

## Expected Working Style

When acting as the testing thread, a future thread should usually:

1. read the relevant spec or implementation notes first
2. convert requirements into explicit test cases before or alongside code changes
3. prefer fixtures and helper functions over repeated inline setup
4. keep tests close to user-visible behavior when possible
5. use the CLI path when validating the simulation contract
6. keep assertions specific enough to catch regressions, but not so brittle that harmless refactors break them

## Boundaries To Respect

Testing should respect project layer boundaries:

- `Simulation_Layer/` tests should validate counting behavior
- `Representational_Layer/` tests should validate candidate and ballot generation behavior
- `Global_Utilities/` tests should validate shared parsing and IO behavior
- `Pipe/` should remain the reusable handoff zone for realistic JSON inputs

Avoid mixing unrelated infra, feature, and testing work in one change if it makes ownership muddy.

## Good Next Steps

If another testing thread picks this up, strong next tasks would be:

- add validation-failure tests for malformed election JSON and expected error messages
- split reusable parsing and CLI test helpers into a dedicated shared test utility module if the suite grows
- add layer-specific test commands to documentation so other threads run the right subset quickly
- expand simulation tests around ties, surplus transfer edge cases, and recount-stability assumptions
- add representational-layer fixture-driven tests if that layer begins sharing more stable contracts with simulation

## Handoff Summary

If a future thread is acting as the testing thread for this repo, its responsibility is simple:

It should behave like the project’s verification and test-infrastructure owner, turning spec language and user expectations into clear `pytest` coverage, with an emphasis on modular fixtures, CLI-visible simulation behavior, and easy-to-run checks that help other threads move safely.

# Contributing

## Purpose

This project combines district generation, representational modeling, and election simulation. New contributors should treat it as a research software project with clear layer boundaries, strong testing expectations, and a review-based Git workflow.

Before changing code, read:

- `README.md`
- `AGENTS.md`
- the relevant handoff document in `Documents/Thread_Handoff/`

That should give you the project structure, the current state of the repo, and the boundaries for the area you are touching.

## Core Contribution Rules

### Respect layer boundaries

The repository has three main layers:

- `MMD_Generation_Layer/`
- `Representational_Layer/`
- `Simulation_Layer/`

Do not blur responsibilities across those layers unless the change is explicitly about integration.

Examples:

- district generation changes belong in `MMD_Generation_Layer/`
- candidate, preference, and ballot generation changes belong in `Representational_Layer/`
- counting and tabulation logic changes belong in `Simulation_Layer/`

### Reuse shared utilities

Do not create ad hoc replacements for shared infrastructure that already exists.

Use:

- `Global_Utilities/json_io.py` for shared simulation JSON contracts
- `Global_Utilities/logger.py` for runtime logging helpers
- `Pipe/` as the shared handoff boundary for simulation-ready election JSON

### Keep changes focused

Prefer small, reviewable changes over large mixed-purpose edits.

A good contribution usually does one of the following:

- adds or improves a feature
- fixes a bug
- refactors one area without changing behavior
- adds or improves tests
- updates docs to match the current code state

## Git Workflow

### Start with an issue

Contributions should begin with an issue.

If you find:

- a bug
- a missing feature
- a documentation gap
- test coverage that should exist but does not
- cleanup work that should be done

then first check whether an issue already exists for that work.

If an issue does not already exist, create one before starting the change so the work is visible, discussable, and easier to assign.

This helps the team:

- track open work
- avoid duplicate effort
- onboard new contributors faster
- separate “what should be done” from “what code was written”

### Issue title guidelines

Issue titles should be short, specific, and action-oriented.

Good examples:

- `Set up project README`
- `Implement contract parser`
- `Fix packet delay calculation`
- `Add test cases for routing logic`
- `Clean up unused files`

Prefer titles that clearly say what needs to happen rather than vague summaries.

### Issue labels

Use labels to make issue triage easier.

Common labels for this project:

- `bug`
- `feature`
- `documentation`
- `cleanup`
- `homework`
- `priority-high`
- `priority-low`
- `good-first-issue`
- `needs-review`
- `blocked`

Use the smallest useful set of labels. A typical issue might have one type label and one priority label.

### No direct commits to `main`

Do not commit directly to `main`.

All changes must use:

1. an issue
1. a branch
2. a pull request
3. at least one review before merge

### Branch naming convention

Use short descriptive branch names with one of these prefixes:

- `feat/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `refactor/<short-description>`
- `test/<short-description>`

Examples:

- `feat/representational-orchestration-api`
- `fix/stv-surplus-transfer-rounding`
- `docs/update-onboarding-guide`
- `test/add-json-roundtrip-regression`

### Merge strategy

Use **squash merges** into `main`.

This keeps the main branch history cleaner and makes it easier to understand project milestones without reading every intermediate commit from a feature branch.

## Commit Message Convention

Use this template:

```text
{feat|fix|docs|refactor|test}[optional scope]: <description>
```

Examples:

- `feat: add representational ballot export helper`
- `fix(simulation): correct tied-elimination ordering`
- `docs: update MMD workflow instructions`
- `refactor(representation): simplify scoring helper flow`
- `test(json-io): add pipe-path regression coverage`

Guidelines:

- keep the description short and specific
- use the scope when it adds useful context
- write messages based on the user-facing or architectural change, not just the file name

## How To Read And Modify Files

### Start with existing docs

Before editing, read the relevant project docs and thread handoff for the area you are changing.

At minimum:

- `README.md`
- `AGENTS.md`
- the relevant file(s) you plan to modify

### Understand the existing abstraction first

Before adding code:

- check whether the repo already has a model, helper, utility, or wrapper for the behavior you need
- prefer extending the existing structure over creating parallel patterns
- keep compatibility wrappers intact unless the task is specifically about changing the public import surface

### Avoid duplication

Do not duplicate:

- models
- JSON serializers
- logging behavior
- test fixtures
- configuration logic

If similar logic already exists, reuse or refactor it instead.

### Keep docs aligned

If your change affects:

- repo structure
- commands
- expected behavior
- contracts between layers

then update the relevant docs in the same pull request.

## Feature Development Standards

When building a feature:

1. identify which layer owns the change
2. confirm whether a shared contract is affected
3. make the smallest clean change that fits the current architecture
4. add or update tests
5. update docs if the workflow or behavior changed

Good feature work should:

- fit the current layer boundaries
- be testable
- avoid hidden behavior changes
- preserve existing contracts unless the contract change is intentional and documented

## Bug Fix Standards

When fixing a bug:

1. reproduce or clearly describe the failure
2. identify the narrowest responsible area
3. fix the root cause, not just the visible symptom
4. add a regression test whenever practical
5. document behavior changes if users or future contributors need to know

Avoid:

- unrelated cleanup mixed into a bug fix PR
- speculative refactors while fixing urgent correctness issues
- changing external behavior without updating tests or docs

## Testing Standards

Every contributor is expected to test their work.

At a high level:

- feature changes should include tests for the new behavior
- bug fixes should include regression coverage when practical
- refactors should preserve existing test behavior
- doc-only changes do not usually require test runs

### Test design guidelines

Write tests that are:

- focused on one behavior
- readable by someone new to the project
- deterministic when possible
- close to the layer being changed

Prefer:

- unit-style tests for local logic
- contract tests for shared JSON boundaries
- acceptance tests for simulation behavior and CLI-facing workflows

### Useful test habits

- test expected behavior, not just implementation details
- cover edge cases when they are relevant to election logic
- avoid brittle tests that depend on incidental formatting or unrelated environment behavior
- keep fixtures realistic but minimal

### Common command

From the repository root:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

Use narrower test commands when working in one layer, but make sure the tests you changed actually run before opening a PR.

## Pull Request Expectations

Each PR should be understandable without deep archaeology.

A good PR:

- is linked to a clear issue
- has one clear purpose
- explains why the change was needed
- lists how it was tested
- updates docs when needed
- avoids unrelated generated files or junk artifacts

## PR Template

```md
## Summary
What changed?

## Why
Why was this needed?

## Testing
How did you test this?

## Checklist
- [ ] I pulled latest main before opening this PR
- [ ] I tested my changes
- [ ] I updated docs/README if needed
- [ ] I did not commit secrets or generated junk files
```

## Final Checklist Before Opening A PR

- an issue exists for the work
- the change is in the correct layer
- branch name follows the convention
- commit messages follow the convention
- tests were run at the right level
- docs were updated if behavior or workflow changed
- no secrets, environment files, or generated junk were added

# Git Thread

## Purpose

This thread is the Git-focused support thread for the FRA project.

Its job is to handle:

- issue-first workflow support and task-to-branch mapping
- `git status`, diff review, and change grouping
- creating the correct branch before publishable work begins
- staging related files together
- making reasonable commits
- writing commit messages in the required format
- pushing committed work to the remote when asked

It is not the main implementation thread. It should not take ownership of feature design, architecture, or broad code changes unless the user explicitly asks for Git-related cleanup that requires a small edit.

## Workflow Rule

`CONTRIBUTING.md` is the source of truth for Git workflow in this repo. This handoff should follow that workflow exactly.

The default expected workflow is:

1. start with an issue
2. update local `main`
3. create a new branch for the issue or task
4. make the change on that branch
5. update local state with the remote before pushing
6. open a PR for review
7. squash merge after review

This applies even to small changes such as:

- documentation edits
- tests
- cleanup work
- minor bug fixes

If a bug, feature, documentation gap, missing test, or cleanup task does not already have an issue, this thread should recommend creating one before the work proceeds.

Do not use `main` as the default working branch for ordinary repo changes.

## Branch Naming Convention

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

Do not skip branch creation just because a change seems small or simple.

## Issue Guidance

Issue titles should be short, specific, and action-oriented.

Examples:

- `Set up project README`
- `Implement contract parser`
- `Fix packet delay calculation`
- `Add test cases for routing logic`
- `Clean up unused files`

Common labels in this repo include:

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

## Commit Message Rules

Use the commit prefixes defined in `AGENTS.md`:

- `feat: <message>` for feature work
- `fix: <message>` for bug fixes
- `docs: <message>` for documentation changes
- `refactor: <message>` for refactoring-only changes
- `test: <message>` for testing changes, adding or removing tests, running tests, and sharing test results

Messages should be descriptive and specific. Avoid vague commits like:

- `fix: updates`
- `feat: changes`
- `refactor: cleanup`

Prefer messages like:

- `feat: add baseline MMD generation layer and packaging support`
- `fix: exercise simulation acceptance cases through the CLI`
- `refactor: document layer boundaries and AI collaboration workflow`

## Working Style

When asked to publish changes, this thread should:

1. inspect the working tree first
2. confirm the work maps to an issue
3. confirm the work is on an appropriate non-`main` branch
4. update local state with the remote before pushing by pulling, fetching, or using the IDE's project update flow
5. identify distinct groups of changes
6. separate unrelated work into multiple commits
7. avoid mega commits
8. preserve the boundaries described in `AGENTS.md`

Reasonable grouping usually means:

- package/import cleanup in one commit
- behavior or bug fixes in another
- new features in their own commit
- docs-only or workflow guidance in a refactor commit

## Repo Boundaries To Respect

This repo has separate layers. Git grouping should respect those boundaries:

- `MMD_Generation_Layer/` for district-generation work
- `Representational_Layer/` for candidate and ballot generation
- `Simulation_Layer/` for FRA counting
- `Global_Utilities/` for shared helpers
- `Pipe/` for simulation handoff fixtures and JSON inputs

Do not lump together unrelated MMD, representational, simulation, and docs changes unless the user explicitly wants that.

## Safety Rules

- Always check `git status` before staging.
- Do not treat `main` as a normal development branch.
- Do not silently commit unrelated user changes.
- Do not revert user work unless explicitly asked.
- Prefer multiple small commits over one large commit when the changes address different problems.
- If generated artifacts, caches, or environment files appear, keep them out of commits unless the user clearly wants them versioned.

## Expected Outputs

When this thread finishes a Git task, it should usually provide:

- the issue it mapped to, if one exists
- the branch name
- the commit IDs
- the commit messages
- whether the changes were pushed
- any remaining unstaged or untracked files

## Handoff Summary

If a future thread is acting as the Git thread for this repo, its responsibility is simple:

It should behave like a careful release assistant for local work already done by the user or other Codex threads, and turn that work into clear, scoped, well-named Git history.

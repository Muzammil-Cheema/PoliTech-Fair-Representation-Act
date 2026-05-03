# Git Thread

## Purpose

This thread is the Git-focused support thread for the FRA project.

Its job is to handle:

- `git status`, diff review, and change grouping
- staging related files together
- making reasonable commits
- writing commit messages in the required format
- pushing committed work to the remote when asked

It is not the main implementation thread. It should not take ownership of feature design, architecture, or broad code changes unless the user explicitly asks for Git-related cleanup that requires a small edit.

## Commit Message Rules

Use the commit prefixes defined in `AGENTS.md`:

- `feat: <message>` for feature work
- `fix: <message>` for bug fixes
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
2. identify distinct groups of changes
3. separate unrelated work into multiple commits
4. avoid mega commits
5. preserve the boundaries described in `AGENTS.md`

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
- Do not silently commit unrelated user changes.
- Do not revert user work unless explicitly asked.
- Prefer multiple small commits over one large commit when the changes address different problems.
- If generated artifacts, caches, or environment files appear, keep them out of commits unless the user clearly wants them versioned.

## Expected Outputs

When this thread finishes a Git task, it should usually provide:

- the commit IDs
- the commit messages
- whether the changes were pushed
- any remaining unstaged or untracked files

## Handoff Summary

If a future thread is acting as the Git thread for this repo, its responsibility is simple:

It should behave like a careful release assistant for local work already done by the user or other Codex threads, and turn that work into clear, scoped, well-named Git history.

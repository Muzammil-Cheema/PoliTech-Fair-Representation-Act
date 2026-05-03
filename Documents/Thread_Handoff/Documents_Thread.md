# Documents / Questioning Thread Handoff

## Role

This thread is the project’s documentation, questioning, and design-review thread. It is not primarily an implementation thread. Its purpose is to help the user reason through Fair Representation Act design decisions, ask and answer clarifying questions, compare project behavior to the FRA bill and design documents, and keep project-facing markdown documents aligned with the current codebase.

Future Codex threads should treat this file as the handoff for the “Documents / Questioning” lane of work.

## Primary Responsibilities

- Answer general questions about the FRA project, repo structure, and current architecture.
- Help evaluate design and refactor ideas before implementation.
- Explain current code behavior in human-readable terms, especially simulation-layer and representational-layer behavior.
- Compare implemented behavior against source documents when asked.
- Keep documentation current, especially `Documents/README.md`, `Documents/AGENTS.md`, and future project-context handoff files.
- Identify risks, limitations, and known issues in a clear way that can be passed to implementation threads.
- Preserve layer boundaries in documentation and recommendations.

## Work This Thread Has Been Doing

This thread has repeatedly updated project documentation as the repo changed shape. The major documentation updates included:

- Mapping the repo from an earlier two-layer framing into the current three-layer framing:
  - `MMD_Generation_Layer/`
  - `Representational_Layer/`
  - `Simulation_Layer/`
- Updating file and directory names after the project was renamed and moved to:
  - `/Users/fuzi_x_muzi/Documents/PoliTech Research/Politech-Fair-Representation-Act`
- Documenting the MMD layer copied in from the old standalone MMD project.
- Recording that the current MMD generation code is a baseline equal-population district-plan workflow, not a complete FRA proportional-population multimember-district generator.
- Explaining the difference between running the simulation CLI manually and running the e2e pytest acceptance tests.
- Keeping `Documents/AGENTS.md` aligned with changing function names, package shims, commands, and directory structure.

## Current Repo Understanding

The active project root is:

```text
/Users/fuzi_x_muzi/Documents/PoliTech Research/Politech-Fair-Representation-Act
```

The project currently has three conceptual layers:

- `MMD_Generation_Layer/`: geographic district-plan generation and dashboarding.
- `Representational_Layer/`: experiments for candidates, elector units, preference profiles, scoring, and ballot generation.
- `Simulation_Layer/`: FRA counting engine for single-seat RCV and multi-seat STV.

Shared handoff JSON goes through:

- `Global_Utilities/json_io.py`
- `Representational_Layer/Src/output_writer.py`
- `Pipe/`

The documentation thread should keep reminding future work not to blur these boundaries unless the user explicitly asks for an integration refactor.

## Important Current Nuances

### MMD Generation

The MMD code currently uses GerryChain/ReCom through:

- `MMD_Generation_Layer/Processor/main.ipynb`
- `MMD_Generation_Layer/config.py`
- `MMD_Generation_Layer/Client/baseline_dashboard.py`

The current implementation uses one equal-population target across districts. Real FRA multimember maps with different seat counts will need proportional population targets by seat count. For example, a 5-seat MMD should target about five times the ideal single-seat population, not the same population as a 3-seat MMD.

Also note that checked-in MMD outputs may be stale relative to `NUM_DISTRICTS = 14`; verify outputs before treating them as analytical ground truth.

### Simulation CLI vs E2E Tests

Manual simulation runs:

```bash
python Simulation_Layer/fra_engine.py
python Simulation_Layer/Runner/main.py
```

These are interactive/manual CLI flows. They prompt for an input JSON path and print winners, final candidate status, and round details to the terminal.

Acceptance tests:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q Simulation_Layer/Tests/test_acceptance_e2e.py
```

These validate outcomes and normally stay quiet unless a case fails. They should not be expected to produce the same report-style terminal output as the manual CLI.

### Simulation Transfer Policy Discussion

This thread previously reviewed the simulation layer’s STV surplus-transfer behavior against the FRA bill. Earlier issues were found around surplus transfer assumptions, especially when surplus transfers were based on inferred ballot ownership rather than round allocation snapshots.

The current code appears to have moved toward:

- `build_surplus_fractions(...)`
- `apply_simultaneous_surplus_transfer_values(...)`
- `count_votes_single_round(...) -> tuple[totals, ballot_allocations]`

Future documentation/review work should verify current code before repeating older findings, because implementation may have changed in another thread.

## Documentation Files To Keep Current

- `Documents/README.md`
  - Human-facing overview, setup, commands, known issues, layer purpose, and practical workflow.
- `Documents/AGENTS.md`
  - LLM-facing operating manual.
  - Must be updated after every LLM-authored code change.
  - Should list current files, functions, directories, commands, globals, and workflow rules.
- `Documents/Thread_Handoff/Documents_Thread.md`
  - This handoff file for the documentation/questioning thread.

If future documentation files are created, this thread should keep them synchronized with the codebase and with each other.

## How Future Threads Should Use This Handoff

Before asking this lane of work to answer questions or update docs, future threads should read:

```text
Documents/README.md
Documents/AGENTS.md
Documents/Thread_Handoff/Documents_Thread.md
```

If the question involves a specific layer, inspect the current source files before answering. The repo has been moving quickly, so code is the source of truth over earlier chat summaries or older design documents.

## Preferred Style For This Thread

- Be careful, questioning, and explicit about uncertainty.
- Use current code as ground truth.
- Use FRA bill/design documents as source material when requested, but call out when code and docs diverge.
- Avoid making implementation changes unless the user explicitly asks.
- Markdown-only updates are allowed when the user asks for documentation alignment.
- When giving findings, phrase them so implementation threads can act on them directly.

## Known Limits

This thread cannot directly see other Codex chats. It can only use:

- This thread’s conversation history.
- Files currently in the repo.
- Documents the user provides.
- Summaries or excerpts pasted by the user from other chats.

If other threads have important context, ask those threads to create their own markdown handoffs, then consolidate them into a project-level context document.

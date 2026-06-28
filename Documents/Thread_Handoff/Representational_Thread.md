# Representational Thread

## Purpose

This thread is the representational-layer implementation and research thread for the FRA project.

Its job is to handle work related to the political-representation side of the system, especially:

- `Representational_Layer/`
- candidate and elector-unit modeling
- attribute vocabulary and scoring behavior
- ballot-generation behavior and ranking semantics
- simulation-ready export from representational objects
- keeping representational workflows aligned with the shared JSON contract and simulation input requirements

This thread is not the owner of simulation counting rules or MMD district-generation logic, except when small cross-layer edits are required to keep the representational workflow compatible with shared interfaces.

## Primary Scope

This thread should treat the following as its main area of responsibility:

- `Representational_Layer/Src/Representational_Layer/models.py`
- `Representational_Layer/Src/Representational_Layer/scoring.py`
- `Representational_Layer/Src/Representational_Layer/generation.py`
- `Representational_Layer/Src/output_writer.py`
- `Representational_Layer/Attributes/starter_attributes.py`
- `Representational_Layer/Tests/`

It may also touch shared files when necessary for representational-layer execution, especially:

- `Global_Utilities/json_io.py`
- `Global_Utilities/logger.py`
- `Pipe/`
- `pyproject.toml`
- `Simulation_Layer/` when a change is directly about the representation-to-simulation contract

But only when those edits are directly in service of keeping representational generation, export, and test workflows correct.

## Current State Of The Project

The repository currently has three main technical layers plus shared utilities:

- `MMD_Generation_Layer/`: generates district-plan artifacts from geographic data
- `Representational_Layer/`: generates candidates, elector units, scores, and ranked ballots
- `Simulation_Layer/`: consumes election JSON and counts elections under single-seat RCV and multi-seat STV rules
- `Global_Utilities/` and `Pipe/`: provide shared JSON handoff and logging support across layers

The current project state is best understood as:

- the architecture is much clearer and more maintainable than earlier in the semester
- the simulation layer is the most operationally mature piece
- the representational layer already has reusable models, scoring logic, ballot generation, and simulation-ready export
- the biggest remaining project-level gap is integration: the layers still mostly work independently instead of behind one simple research interface

The representational layer is therefore an important middle layer. It is the bridge between upstream districting/research concepts and downstream simulation-ready election inputs.

## What The Representational Layer Is

The representational layer is the project area that models the political and behavioral side of the workflow.

It is responsible for:

- defining representational domain objects such as candidates, elector units, elections, districts, and ballots
- defining attribute vocabularies and weights
- scoring candidates relative to elector units
- generating ranked ballots in rank-group form
- exporting those representational objects into the shared simulation JSON contract

Conceptually:

- `MMD_Generation_Layer/` answers: "What district artifacts exist?"
- `Representational_Layer/` answers: "Who exists in the election, how are preferences modeled, and what ballots get produced?"
- `Simulation_Layer/` answers: "Given those ballots and candidates, who wins under the counting rules?"

## Current File Structure And Purpose

### `Representational_Layer/`

- `Representational_Layer/__init__.py`
  - Public facade re-exporting the implementation package under `Representational_Layer/Src/Representational_Layer`.
- `Representational_Layer/models.py`
  - Compatibility wrapper for `Representational_Layer/Src/Representational_Layer/models.py`.
- `Representational_Layer/generation.py`
  - Compatibility wrapper for `Representational_Layer/Src/Representational_Layer/generation.py`.
- `Representational_Layer/scoring.py`
  - Compatibility wrapper for `Representational_Layer/Src/Representational_Layer/scoring.py`.

These top-level wrappers matter because external code is expected to prefer:

- `Representational_Layer.models`
- `Representational_Layer.generation`
- `Representational_Layer.scoring`

rather than reaching directly into internal source paths.

### `Representational_Layer/Attributes/`

- `Representational_Layer/Attributes/__init__.py`
  - Exports starter attribute specs and defaults.
- `Representational_Layer/Attributes/starter_attributes.py`
  - Holds:
    - `STARTER_SIX_ATTRIBUTE_SPECS`
    - `STARTER_ACTIVE_ATTRIBUTES`
    - `STARTER_ATTRIBUTE_WEIGHTS`
  - Defines:
    - `get_starter_attribute_specs(names: list[str] | None) -> list[AttributeSpec]`

This directory is the seed vocabulary for profile-based representation experiments.

### `Representational_Layer/Src/`

- `Representational_Layer/Src/__init__.py`
  - Source-package container marker.
- `Representational_Layer/Src/output_writer.py`
  - Defines:
    - `write_simulation_ready_output(test_name, ballots, candidates, metadata, project_root=None) -> Path`
  - Thin wrapper around the shared JSON helper that writes simulation-ready outputs into `Pipe/`.

### `Representational_Layer/Src/Representational_Layer/`

- `Representational_Layer/Src/Representational_Layer/__init__.py`
  - Public exports for models, generation, and scoring.
- `Representational_Layer/Src/Representational_Layer/models.py`
  - Core representational dataclasses:
    - `Experiment`
    - `District`
    - `Election`
    - `AttributeSpec`
    - `Candidate`
    - `ElectorUnit`
    - `PreferenceModel`
    - `BallotGenerationRun`
    - `RankGroup`
    - `Ballot`
  - Also defines important type aliases and literals such as:
    - `Profile`
    - `Parameters`
    - `ElectionMode`
    - `AttributeType`
    - `ComparisonMode`
    - `ScoreStyle`
    - `MissingValuePolicy`
    - `RankingMethod`
- `Representational_Layer/Src/Representational_Layer/scoring.py`
  - Main scoring entrypoint:
    - `score_candidates_for_elector_unit(candidates, elector_unit, attribute_specs, preference_model) -> CandidateScores`
  - Internal helper functions support numeric similarity, set overlap, custom scoring, missing-value handling, score normalization, and clamping behavior.
- `Representational_Layer/Src/Representational_Layer/generation.py`
  - Main ballot-generation helpers:
    - `generate_weighted_ballot_ranking(candidates, candidate_probabilities, rng) -> list[RankGroup]`
    - `generate_ballot(ballot_id, generation_run_id, source_elector_unit_id, candidates, candidate_probabilities, rng) -> Ballot`

This internal package is the real implementation home for representational logic.

### `Representational_Layer/Outputs/`

- `Representational_Layer/Outputs/test_generates_deterministic_ballot_from_starter_six_attributes_output.json`
- `Representational_Layer/Outputs/test_generates_many_elector_units_with_multiple_individual_ballots_output.json`

These are local/debug inspection outputs produced by representational tests. They are useful for manually checking what the representational layer is exporting.

### `Representational_Layer/Tests/`

- `Representational_Layer/Tests/test_models.py`
  - Smoke tests for baseline object graphs and weighted ranking generation.
- `Representational_Layer/Tests/test_scoring.py`
  - Tests candidate scoring normalization and missing-value behavior.
- `Representational_Layer/Tests/test_profile_based_ballot_generation.py`
  - Tests deterministic profile-based ballot generation and larger multi-elector-unit scenarios.
  - Uses `write_simulation_ready_output(...)` to export JSON for inspection and simulation compatibility.
- `Representational_Layer/Tests/test_json_io.py`
  - Verifies representational objects round-trip correctly through the shared JSON I/O helpers.
  - Covers `resolve_pipe_path(...)` behavior for both bare relative paths and `Pipe/...` relative paths.

## Shared Utilities This Thread Should Know

The representational thread depends on the following shared utilities:

### `Global_Utilities/json_io.py`

This is the shared JSON boundary between representation and simulation.

Important functions:

- `resolve_pipe_path(path, project_root=None) -> Path`
- `write_simulation_ready_json(output_path, test_name, ballots, candidates, metadata) -> Path`
- `read_simulation_ready_json(path) -> SimulationJsonObjects`

Why it matters:

- representational objects should not use ad hoc serializers
- representational export should preserve deterministic simulation metadata
- the simulation layer depends on this exact contract

### `Global_Utilities/logger.py`

Shared runtime logging wrappers:

- `info(message)`
- `warn(message)`
- `success(message)`
- `error(message)`

Representational reusable modules should use these wrappers instead of direct `print(...)`.

### `Pipe/`

The shared handoff zone for simulation-ready election JSON.

Relevant contents:

- `Pipe/input.json`
- `Pipe/Acceptance_Test_Cases/*.json`
- `Pipe/test_*_output.json`

This thread should treat `Pipe/` as the simulation handoff zone, not as a catch-all output directory.

## Important Current Rules And Constraints

- Ballots must remain in rank-group form using `rank` and `candidate_ids`.
- Representational export must preserve deterministic metadata:
  - `election_id`
  - `seat_count`
  - `mode`
  - `tie_break_order`
  - optional `max_ranks_allowed` or `max_rankings_allowed`
- `tie_break_order` is an elimination priority in the simulation layer, not a "who stays" priority.
- The representational layer should not blur into simulation counting logic.
- The representational layer should not treat current MMD outputs as if they are already simulation-ready election JSON.

## What This Thread Will Be Working On

The representational thread should mainly work on:

1. improving and extending the representational domain model
2. refining candidate-scoring behavior and attribute semantics
3. improving ballot-generation workflows
4. keeping simulation-ready export stable and deterministic
5. strengthening representational tests and fixtures
6. supporting integration work without duplicating simulation or MMD logic

Typical tasks for this thread include:

- adding or refining attribute vocabularies
- adding new preference/scoring strategies
- improving missing-value or weight-handling logic
- designing clearer public APIs for representational experiments
- tightening representational test coverage
- validating that exported JSON remains simulation-compatible

## Planned Upcoming Changes Already Reflected In `Documents/README.md`

The current README already points to several future representational-layer priorities:

### Representational-layer API simplification

The README explicitly calls for:

- exposing one orchestration entrypoint for:
  - scoring
  - ranking
  - ballot objects
  - simulation JSON export
- keeping multiple behaviors selectable behind that single entrypoint:
  - `deterministic_sort`
  - weighted generation
  - `softmax` or related future methods

This is probably the most important planned change for this thread.

### Vocabulary maturity

The README also calls for:

- continuing to expand and version shared attribute specs in `Representational_Layer/Attributes/`
- formalizing weight presets and missing-value policies for reproducible experiments

This means the starter attribute vocabulary is only the beginning, not the final design.

### Visualization support

The README also identifies a future need for:

- reusable export shapes for plotting round-by-round candidate utilities and ballot distributions
- starter scripts or notebooks for score and ranking diagnostics

This is not yet a full interface/GUI task, but the representational thread will likely supply the data structures that make those visualizations possible.

## Known Risks And Watchouts

- The representational layer currently has multiple ballot-generation styles. That is useful for exploration, but it can be confusing if no single public workflow is established.
- Attribute vocabularies and weights can drift if they are expanded informally without clear versioning or defaults.
- The temptation to push simulation-specific rules into representational code should be resisted.
- The temptation to treat MMD district outputs as if they already define representational `District` objects should also be resisted until the integration contract is explicit.
- Exported JSON can appear correct while still violating important metadata expectations unless round-trip tests remain strong.

## Good Next Tasks For The Successor Representational Thread

1. define or prototype a single public representational orchestration API
2. expand starter attributes into more explicit, versioned experiment vocabularies
3. formalize reusable weight presets and missing-value policies
4. add more fixture-driven representational tests
5. add diagnostics or exports that help compare candidate scoring and ballot outcomes
6. coordinate with the integration thread on what the future end-to-end experiment interface should expect from this layer

## What This Thread Should Not Own

This thread should not become the default owner for:

- Git staging, commit grouping, or push workflows
- MMD notebook execution, geospatial setup, or district-plan generation details
- simulation counting rules, transfer semantics, or round-policy design
- broad documentation cleanup unrelated to representational onboarding or behavior

## Quick Commands

From the project root:

```bash
source .venv/bin/activate
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q Representational_Layer/Tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q Representational_Layer/Tests/test_json_io.py
PYTHONPATH=.:Src pytest -q Representational_Layer/Tests/test_profile_based_ballot_generation.py
```

Useful import guidance:

- prefer `Representational_Layer.models`
- prefer `Representational_Layer.generation`
- prefer `Representational_Layer.scoring`

Keep implementation edits in:

- `Representational_Layer/Src/Representational_Layer/`

unless the task is specifically about compatibility wrappers.

## Handoff Summary

If a future thread is acting as the representational thread for this repo, its responsibility is to protect and improve the part of the project that turns political profiles and candidate/elector logic into simulation-ready ballots.

It should behave like the thread that owns candidate modeling, scoring, ballot generation, and representational export discipline while preserving clean boundaries with both MMD generation and simulation counting.

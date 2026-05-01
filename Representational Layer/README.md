# Fair-Representation-Act-Representational-Layer

Minimal Python package for the representational layer of the Fair Representation
Act voting-system project.

Current scope:

- Core dataclasses for experiments, districts, elections, candidates, elector
  units, preference models, ballot generation runs, and ballots.
- `Ballot.rankings` stored as ordered `RankGroup` entries so we can preserve
  explicit ranks, skipped rankings, and tied rankings.
- A small smoke test to validate the first-pass object graph.

Quick start:

```bash
python -m pip install -e '.[dev]'
pytest
```

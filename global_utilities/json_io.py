from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Protocol, Sequence, TypedDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SIMULATION_ROOT = PROJECT_ROOT / "Simulation Layer"
PIPE_DIR_NAME = "pipe"

if str(SIMULATION_ROOT) not in sys.path:
    sys.path.append(str(SIMULATION_ROOT))

from core.config import DEFAULT_ENCODING
from core.models import Ballot, Candidate, Mode, Ranking
from .logger import error


class SimulationJsonMetadata(TypedDict, total=False):
    election_id: str
    seat_count: int
    mode: Mode
    tie_break_order: list[str]
    max_ranks_allowed: int | None
    max_rankings_allowed: int | None


class RepresentationCandidate(Protocol):
    candidate_id: str
    withdrawn: bool


class RepresentationRankGroup(Protocol):
    rank: int
    candidate_ids: list[str]


class RepresentationBallot(Protocol):
    ballot_id: str
    rankings: list[RepresentationRankGroup]


SimulationJsonObjects = tuple[
    str,
    int,
    Mode,
    list[Candidate],
    list[Ballot],
    list[str],
    int | None,
]


def resolve_pipe_path(path: str | Path, project_root: Path | None = None) -> Path:
    """
    Resolve a path through the shared process `pipe/` directory.

    Absolute paths are left unchanged. Relative paths are resolved as:
      <project_root>/pipe/<path>
    """
    path_obj = Path(path)
    if path_obj.is_absolute():
        return path_obj

    root = project_root or PROJECT_ROOT
    return root / PIPE_DIR_NAME / path_obj


def _to_json_compatible(value: Any) -> Any:
    if is_dataclass(value):
        return _to_json_compatible(asdict(value))
    if isinstance(value, Mapping):
        return {key: _to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, set):
        return sorted(_to_json_compatible(item) for item in value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_to_json_compatible(item) for item in value]
    return value


def _get_metadata_value(
    data: Mapping[str, Any],
    metadata: Mapping[str, Any],
    field_name: str,
) -> Any:
    return metadata.get(field_name, data.get(field_name))


def _get_max_ranks_allowed(data: Mapping[str, Any], metadata: Mapping[str, Any]) -> int | None:
    for field_name in (
        "max_ranks_allowed",
        "max_rankings_allowed",
    ):
        if field_name in metadata:
            return metadata[field_name]
        if field_name in data:
            return data[field_name]
    return None


def write_simulation_ready_json(
    *,
    output_path: Path,
    test_name: str,
    ballots: Sequence[RepresentationBallot],
    candidates: Sequence[RepresentationCandidate],
    metadata: SimulationJsonMetadata | Mapping[str, Any],
) -> Path:
    """Write representation-layer objects in the simulation JSON contract."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "test_name": test_name,
        "metadata": _to_json_compatible(metadata),
        "candidates": [_to_json_compatible(candidate) for candidate in candidates],
        "ballots": [_to_json_compatible(ballot) for ballot in ballots],
    }

    output_path.write_text(
        json.dumps(payload, indent=2),
        encoding=DEFAULT_ENCODING,
    )
    return output_path


def read_simulation_ready_json(path: str | Path) -> SimulationJsonObjects:
    """Read simulation JSON into typed objects used by the simulation layer."""
    resolved_path = resolve_pipe_path(path)
    try:
        with resolved_path.open("r", encoding=DEFAULT_ENCODING) as election_file:
            data = json.load(election_file)
    except OSError as exc:
        error(f"Could not read simulation JSON '{resolved_path}'. Details: {exc}")
    except json.JSONDecodeError as exc:
        error(f"Could not parse simulation JSON '{resolved_path}'. Details: {exc}")

    metadata = data.get("metadata", {})
    election_id = _get_metadata_value(data, metadata, "election_id")
    seat_count = _get_metadata_value(data, metadata, "seat_count")
    mode = _get_metadata_value(data, metadata, "mode")
    tie_break_order = _get_metadata_value(data, metadata, "tie_break_order")
    max_ranks_allowed = _get_max_ranks_allowed(data, metadata)

    required_fields = {
        "election_id": election_id,
        "seat_count": seat_count,
        "mode": mode,
        "tie_break_order": tie_break_order,
    }
    for field_name, value in required_fields.items():
        if value is None:
            error(f"Missing required field '{field_name}' (top-level or metadata)")

    try:
        candidates = [
            Candidate(
                candidate_id=candidate["candidate_id"],
                withdrawn=candidate.get("withdrawn", False),
            )
            for candidate in data.get("candidates", [])
        ]
    except KeyError as exc:
        error(f"Candidate entry is missing required field {exc}")

    ballots: list[Ballot] = []
    try:
        for ballot in data.get("ballots", []):
            rankings = [
                Ranking(
                    rank=ranking["rank"],
                    candidate_ids=ranking["candidate_ids"],
                )
                for ranking in ballot.get("rankings", [])
            ]
            ballots.append(Ballot(ballot_id=ballot["ballot_id"], rankings=rankings))
    except KeyError as exc:
        error(f"Ballot entry is missing required field {exc}")

    return (
        election_id,
        seat_count,
        mode,
        candidates,
        ballots,
        tie_break_order,
        max_ranks_allowed,
    )

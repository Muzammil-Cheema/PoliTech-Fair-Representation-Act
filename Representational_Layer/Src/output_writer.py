from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from Global_Utilities import resolve_pipe_path, write_simulation_ready_json
from Representational_Layer.models import Ballot, Candidate


def write_simulation_ready_output(
    test_name: str,
    ballots: list[Ballot],
    candidates: list[Candidate],
    metadata: dict[str, Any],
    project_root: Path | None = None,
) -> Path:
    """Write simulation-ready candidate and ballot objects for a test run."""
    root = project_root or PROJECT_ROOT
    output_path = resolve_pipe_path(f"{test_name}_output.json", project_root=root)
    return write_simulation_ready_json(
        output_path=output_path,
        test_name=test_name,
        ballots=ballots,
        candidates=candidates,
        metadata=metadata,
    )

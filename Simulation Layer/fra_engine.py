from __future__ import annotations

"""
Compatibility shim.

The simulation engine implementation now lives under:
  - core/
  - helpers/
  - runner/main.py
"""

import sys
from pathlib import Path

SIMULATION_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = SIMULATION_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
if str(SIMULATION_ROOT) not in sys.path:
    sys.path.append(str(SIMULATION_ROOT))

from core.models import Ballot, Candidate, Election, Mode, Ranking
from runner.main import (
    load_election_from_json,
    run_cli,
    run_election,
    run_multi_seat_stv,
    run_single_seat_rcv,
)

__all__ = [
    "Ballot",
    "Candidate",
    "Election",
    "Mode",
    "Ranking",
    "load_election_from_json",
    "run_election",
    "run_multi_seat_stv",
    "run_single_seat_rcv",
]


if __name__ == "__main__":
    run_cli()

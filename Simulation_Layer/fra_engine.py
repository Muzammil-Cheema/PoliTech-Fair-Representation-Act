from __future__ import annotations

"""Compatibility shim for the simulation engine public API."""

from Simulation_Layer.Core.models import Ballot, Candidate, Election, Mode, Ranking
from Simulation_Layer.Runner.main import (
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

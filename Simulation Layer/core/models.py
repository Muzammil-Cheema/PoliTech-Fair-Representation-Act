from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

from global_utilities.logger import error

from .config import DEFAULT_TRANSFER_VALUE, VALID_MODES

Mode = Literal["single_seat_rcv", "multi_seat_stv"]


@dataclass
class Candidate:
    candidate_id: str
    withdrawn: bool = False


@dataclass
class Ranking:
    rank: int
    candidate_ids: List[str]


@dataclass
class Ballot:
    ballot_id: str
    rankings: List[Ranking] = field(default_factory=list)
    current_transfer_value: float = DEFAULT_TRANSFER_VALUE


@dataclass
class Election:
    election_id: str
    seat_count: int
    mode: Mode
    candidates: List[Candidate]
    ballots: List[Ballot]
    tie_break_order: List[str]
    max_ranks_allowed: Optional[int] = None

    # Internal state
    round_number: int = 0
    threshold: Optional[float] = None
    round_log: List[Dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.seat_count < 1:
            error("seat_count must be at least 1")

        if self.mode not in VALID_MODES:
            error("mode must be 'single_seat_rcv' or 'multi_seat_stv'")

        ids = [c.candidate_id for c in self.candidates]
        if len(ids) != len(set(ids)):
            error("Candidate IDs must be unique")

        if set(self.tie_break_order) != set(ids):
            error("tie_break_order must contain each candidate exactly once")

        valid_ids = set(ids)

        for ballot in self.ballots:
            for ranking in ballot.rankings:
                if ranking.rank <= 0:
                    error(
                        f"Ballot {ballot.ballot_id} has invalid rank {ranking.rank}"
                    )
                for cid in ranking.candidate_ids:
                    if cid not in valid_ids:
                        error(
                            f"Ballot {ballot.ballot_id} references unknown candidate '{cid}'"
                        )

        if self.max_ranks_allowed is not None:
            for ballot in self.ballots:
                for ranking in ballot.rankings:
                    if ranking.rank > self.max_ranks_allowed:
                        error(
                            f"Ballot {ballot.ballot_id} exceeds max_ranks_allowed={self.max_ranks_allowed}"
                        )

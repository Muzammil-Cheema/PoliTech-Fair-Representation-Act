from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias

Profile: TypeAlias = dict[str, Any]
Parameters: TypeAlias = dict[str, Any]
ElectionMode = Literal["single_seat_rcv", "multi_seat_stv"]
AttributeType = Literal["numeric", "categorical", "boolean", "set", "ordinal"]
ComparisonMode = Literal[
    "similarity",
    "exact_match",
    "set_overlap",
    "candidate_effect",
    "custom",
]
ScoreStyle = Literal["signed", "bonus_only", "penalty_only"]
MissingValuePolicy = Literal["ignore", "zero", "error"]
RankingMethod = Literal[
    "deterministic_sort",
    "weighted_without_replacement",
    "softmax_without_replacement",
]


# Top-level container for one research scenario and its shared configuration.
@dataclass
class Experiment:
    experiment_id: str
    description: str | None = None


# Minimal district record used by the representational layer before geometry
# and district-generation integration are finalized.
@dataclass
class District:
    district_id: str
    experiment_id: str
    population: int
    seat_target: int
    geometry: Any | None = None


# Election-level metadata shared by all candidates, elector units, and ballots
# generated for a single contest.
@dataclass
class Election:
    election_id: str
    experiment_id: str
    district_id: str
    mode: ElectionMode
    max_rankings_allowed: int
    description: str | None = None


# Shared metadata for one profile attribute, including how the attribute should
# be interpreted and compared during candidate scoring.
@dataclass
class AttributeSpec:
    attribute_spec_id: str
    experiment_id: str
    name: str
    attribute_type: AttributeType
    comparison_mode: ComparisonMode
    score_style: ScoreStyle = "signed"
    value_min: float | None = None
    value_max: float | None = None
    config: Parameters = field(default_factory=dict)
    description: str | None = None


# Candidate entity for a single election; the profile stores raw attributes,
# while scoring meaning is defined separately by AttributeSpec and PreferenceModel.
@dataclass
class Candidate:
    candidate_id: str
    election_id: str
    withdrawn: bool = False
    home_district_id: str | None = None
    profile: Profile = field(default_factory=dict)


# Aggregated voter block or source population for ballot generation within a
# single election, using the same shared profile vocabulary as candidates.
@dataclass
class ElectorUnit:
    elector_unit_id: str
    election_id: str
    size: int
    profile: Profile = field(default_factory=dict)


# Behavioral model describing how to score candidates from profile data, which
# attributes are active, how much they matter, and how scores become rankings.
@dataclass
class PreferenceModel:
    preference_model_id: str
    experiment_id: str
    name: str
    active_attributes: list[str] = field(default_factory=list)
    attribute_weights: dict[str, float] = field(default_factory=dict)
    missing_value_policy: MissingValuePolicy = "ignore"
    ranking_method: RankingMethod = "deterministic_sort"
    temperature: float | None = None
    parameters: Parameters = field(default_factory=dict)
    description: str | None = None


# Provenance record for one generated ballot batch so shared generation settings
# do not need to be duplicated on every ballot.
@dataclass
class BallotGenerationRun:
    generation_run_id: str
    election_id: str
    preference_model_id: str
    random_seed: int | None = None
    notes: str | None = None


# One explicit rank position in a ballot, supporting ties and skipped ranks by
# preserving the rank number separately from candidate order.
@dataclass
class RankGroup:
    rank: int
    candidate_ids: list[str]


# One generated ballot linked to both its source elector unit and the ballot
# generation run that produced it.
@dataclass
class Ballot:
    ballot_id: str
    generation_run_id: str
    source_elector_unit_id: str
    rankings: list[RankGroup] = field(default_factory=list)

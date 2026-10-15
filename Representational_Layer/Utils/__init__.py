"""Representational-layer data model for Fair Representation Act experiments."""

from .generation import generate_ballot, generate_weighted_ballot_ranking
from .input_contract import (
    ContractValidationError,
    RepresentationalExperimentState,
    load_experiment_contract,
    parse_experiment_contract,
)
from .models import (
    AttributeSpec,
    AttributeType,
    Ballot,
    BallotGenerationRun,
    Candidate,
    ComparisonMode,
    District,
    Election,
    ElectionMode,
    ElectorUnit,
    Experiment,
    MissingValuePolicy,
    Parameters,
    PreferenceModel,
    Profile,
    RankGroup,
    RankingMethod,
    ScoreStyle,
)
from .scoring import score_candidates_for_elector_unit

__all__ = [
    "AttributeSpec",
    "AttributeType",
    "Ballot",
    "BallotGenerationRun",
    "Candidate",
    "ComparisonMode",
    "ContractValidationError",
    "District",
    "Election",
    "ElectionMode",
    "ElectorUnit",
    "Experiment",
    "MissingValuePolicy",
    "Parameters",
    "PreferenceModel",
    "Profile",
    "RankGroup",
    "RankingMethod",
    "RepresentationalExperimentState",
    "ScoreStyle",
    "generate_ballot",
    "generate_weighted_ballot_ranking",
    "load_experiment_contract",
    "parse_experiment_contract",
    "score_candidates_for_elector_unit",
]

from __future__ import annotations

from copy import deepcopy

from Representational_Layer import AttributeSpec

STARTER_SIX_ATTRIBUTE_SPECS: dict[str, AttributeSpec] = {
    "ideology_score": AttributeSpec(
        attribute_spec_id="attr-ideology-score",
        experiment_id="starter-vocab",
        name="ideology_score",
        attribute_type="numeric",
        comparison_mode="similarity",
        score_style="signed",
        value_min=-1.0,
        value_max=1.0,
        description="Continuous ideology proximity signal.",
    ),
    "party_id": AttributeSpec(
        attribute_spec_id="attr-party-id",
        experiment_id="starter-vocab",
        name="party_id",
        attribute_type="categorical",
        comparison_mode="exact_match",
        score_style="signed",
        description="Partisan alignment signal.",
    ),
    "home_region": AttributeSpec(
        attribute_spec_id="attr-home-region",
        experiment_id="starter-vocab",
        name="home_region",
        attribute_type="categorical",
        comparison_mode="exact_match",
        score_style="bonus_only",
        description="Geographic affinity bonus.",
    ),
    "community_tags": AttributeSpec(
        attribute_spec_id="attr-community-tags",
        experiment_id="starter-vocab",
        name="community_tags",
        attribute_type="set",
        comparison_mode="set_overlap",
        score_style="bonus_only",
        description="Community or identity overlap signal.",
    ),
    "issue_tags": AttributeSpec(
        attribute_spec_id="attr-issue-tags",
        experiment_id="starter-vocab",
        name="issue_tags",
        attribute_type="set",
        comparison_mode="set_overlap",
        score_style="bonus_only",
        description="Policy preference overlap signal.",
    ),
    "candidate_quality": AttributeSpec(
        attribute_spec_id="attr-candidate-quality",
        experiment_id="starter-vocab",
        name="candidate_quality",
        attribute_type="numeric",
        comparison_mode="candidate_effect",
        score_style="bonus_only",
        value_min=0.0,
        value_max=100.0,
        description="Candidate-side appeal/quality effect.",
    ),
}

STARTER_ACTIVE_ATTRIBUTES: list[str] = [
    "ideology_score",
    "party_id",
    "home_region",
    "community_tags",
    "issue_tags",
    "candidate_quality",
]

STARTER_ATTRIBUTE_WEIGHTS: dict[str, float] = {
    "ideology_score": 0.35,
    "party_id": 0.25,
    "home_region": 0.10,
    "community_tags": 0.10,
    "issue_tags": 0.10,
    "candidate_quality": 0.10,
}


def get_starter_attribute_specs(names: list[str] | None = None) -> list[AttributeSpec]:
    """Return detached copies of starter attribute specs for safe reuse in tests."""
    selected_names = names if names is not None else STARTER_ACTIVE_ATTRIBUTES
    return [deepcopy(STARTER_SIX_ATTRIBUTE_SPECS[name]) for name in selected_names]
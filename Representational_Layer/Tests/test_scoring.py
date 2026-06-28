import pytest

from Attributes import STARTER_ATTRIBUTE_WEIGHTS, get_starter_attribute_specs
from Representational_Layer import (
    Candidate,
    ElectorUnit,
    PreferenceModel,
    score_candidates_for_elector_unit,
)


def test_scores_candidates_with_normalized_attribute_and_final_scores() -> None:
    elector_unit = ElectorUnit(
        elector_unit_id="block-001",
        election_id="election-001",
        size=500,
        profile={
            "ideology_score": 0.2,
            "party_id": "D",
            "home_region": "north",
            "community_tags": {"labor", "urban"},
            "issue_tags": {"housing", "education"},
        },
    )
    candidates = [
        Candidate(
            candidate_id="cand-a",
            election_id="election-001",
            profile={
                "ideology_score": 0.1,
                "party_id": "D",
                "home_region": "north",
                "community_tags": {"labor"},
                "issue_tags": {"housing", "climate"},
                "candidate_quality": 80.0,
            },
        ),
        Candidate(
            candidate_id="cand-b",
            election_id="election-001",
            profile={
                "ideology_score": -0.9,
                "party_id": "R",
                "home_region": "south",
                "community_tags": {"rural"},
                "issue_tags": {"public_safety"},
                "candidate_quality": 90.0,
            },
        ),
    ]
    attribute_specs = get_starter_attribute_specs(
        [
            "ideology_score",
            "party_id",
            "home_region",
            "community_tags",
            "issue_tags",
            "candidate_quality",
        ]
    )
    preference_model = PreferenceModel(
        preference_model_id="pref-001",
        experiment_id="exp-001",
        name="normalized-baseline",
        temperature=1.0,
        active_attributes=[
            "ideology_score",
            "party_id",
            "home_region",
            "community_tags",
            "issue_tags",
            "candidate_quality",
        ],
        attribute_weights=STARTER_ATTRIBUTE_WEIGHTS,
        missing_value_policy="ignore",
    )

    scores = score_candidates_for_elector_unit(
        candidates=candidates,
        elector_unit=elector_unit,
        attribute_specs=attribute_specs,
        preference_model=preference_model,
    )

    cand_a = scores["cand-a"]
    cand_b = scores["cand-b"]

    assert cand_a["attribute_scores"]["ideology_score"] == pytest.approx(0.9)
    assert cand_a["attribute_scores"]["party_id"] == pytest.approx(1.0)
    assert cand_a["attribute_scores"]["home_region"] == pytest.approx(1.0)
    assert cand_a["attribute_scores"]["community_tags"] == pytest.approx(0.0)
    assert cand_a["attribute_scores"]["issue_tags"] == pytest.approx(0.0)
    assert cand_a["attribute_scores"]["candidate_quality"] == pytest.approx(0.6)
    assert cand_a["final_score"] == pytest.approx(0.725)

    assert cand_b["attribute_scores"]["ideology_score"] == pytest.approx(-0.1)
    assert cand_b["attribute_scores"]["party_id"] == pytest.approx(-1.0)
    assert cand_b["attribute_scores"]["home_region"] == pytest.approx(0.0)
    assert cand_b["attribute_scores"]["community_tags"] == pytest.approx(0.0)
    assert cand_b["attribute_scores"]["issue_tags"] == pytest.approx(0.0)
    assert cand_b["attribute_scores"]["candidate_quality"] == pytest.approx(0.8)
    assert cand_b["final_score"] == pytest.approx(-0.205)

    for candidate_entry in scores.values():
        assert -1.0 <= candidate_entry["final_score"] <= 1.0
        for attribute_score in candidate_entry["attribute_scores"].values():
            assert -1.0 <= attribute_score <= 1.0


def test_missing_value_ignore_renormalizes_by_valid_weights_only() -> None:
    elector_unit = ElectorUnit(
        elector_unit_id="block-002",
        election_id="election-001",
        size=300,
        profile={"party_id": "D"},
    )
    candidates = [
        Candidate(
            candidate_id="cand-c",
            election_id="election-001",
            profile={"party_id": "D"},
        )
    ]
    attribute_specs = get_starter_attribute_specs(["ideology_score", "party_id"])
    preference_model = PreferenceModel(
        preference_model_id="pref-002",
        experiment_id="exp-001",
        name="missing-ignore",
        temperature=1.0,
        active_attributes=["ideology_score", "party_id"],
        attribute_weights={"ideology_score": 0.8, "party_id": 0.2},
        missing_value_policy="ignore",
    )

    scores = score_candidates_for_elector_unit(
        candidates=candidates,
        elector_unit=elector_unit,
        attribute_specs=attribute_specs,
        preference_model=preference_model,
    )

    cand_c = scores["cand-c"]
    assert "ideology_score" not in cand_c["attribute_scores"]
    assert cand_c["attribute_scores"]["party_id"] == pytest.approx(1.0)
    assert cand_c["final_score"] == pytest.approx(1.0)

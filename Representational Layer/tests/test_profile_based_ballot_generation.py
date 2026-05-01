from attributes import (
    STARTER_ACTIVE_ATTRIBUTES,
    STARTER_ATTRIBUTE_WEIGHTS,
    get_starter_attribute_specs,
)
from output_writer import write_simulation_ready_output
from representational_layer import (
    Ballot,
    BallotGenerationRun,
    Candidate,
    ElectorUnit,
    PreferenceModel,
    RankGroup,
    score_candidates_for_elector_unit,
)


def test_generates_deterministic_ballot_from_starter_six_attributes() -> None:
    """Generate a ranked ballot using the shared 6-attribute starter vocabulary."""
    candidates = [
        Candidate(
            candidate_id="cand-a",
            election_id="election-003",
            profile={
                "ideology_score": 0.10,
                "party_id": "D",
                "home_region": "north",
                "community_tags": {"labor"},
                "issue_tags": {"housing", "climate"},
                "candidate_quality": 80.0,
            },
        ),
        Candidate(
            candidate_id="cand-b",
            election_id="election-003",
            profile={
                "ideology_score": -0.90,
                "party_id": "R",
                "home_region": "south",
                "community_tags": {"rural"},
                "issue_tags": {"public_safety"},
                "candidate_quality": 90.0,
            },
        ),
        Candidate(
            candidate_id="cand-c",
            election_id="election-003",
            profile={
                "ideology_score": 0.40,
                "party_id": "D",
                "home_region": "south",
                "community_tags": {"urban", "college_town"},
                "issue_tags": {"housing", "education"},
                "candidate_quality": 60.0,
            },
        ),
    ]
    elector_unit = ElectorUnit(
        elector_unit_id="block-central",
        election_id="election-003",
        size=1200,
        profile={
            "ideology_score": 0.20,
            "party_id": "D",
            "home_region": "north",
            "community_tags": {"labor", "urban"},
            "issue_tags": {"housing", "education"},
        },
    )
    attribute_specs = get_starter_attribute_specs(STARTER_ACTIVE_ATTRIBUTES)
    preference_model = PreferenceModel(
        preference_model_id="pref-003",
        experiment_id="exp-003",
        name="starter-six-deterministic",
        active_attributes=STARTER_ACTIVE_ATTRIBUTES,
        attribute_weights=STARTER_ATTRIBUTE_WEIGHTS,
        missing_value_policy="ignore",
        ranking_method="deterministic_sort",
    )
    generation_run = BallotGenerationRun(
        generation_run_id="run-003",
        election_id="election-003",
        preference_model_id=preference_model.preference_model_id,
        random_seed=101,
    )

    candidate_scores = score_candidates_for_elector_unit(
        candidates=candidates,
        elector_unit=elector_unit,
        attribute_specs=attribute_specs,
        preference_model=preference_model,
    )
    ordered_candidate_ids = [
        candidate_id
        for candidate_id, _ in sorted(
            candidate_scores.items(),
            key=lambda item: (item[1]["final_score"], item[0]),
            reverse=True,
        )
    ]
    ballot = Ballot(
        ballot_id="ballot-003",
        generation_run_id=generation_run.generation_run_id,
        source_elector_unit_id=elector_unit.elector_unit_id,
        rankings=[
            RankGroup(rank=index + 1, candidate_ids=[candidate_id])
            for index, candidate_id in enumerate(ordered_candidate_ids)
        ],
    )
    output_path = write_simulation_ready_output(
        test_name="test_generates_deterministic_ballot_from_starter_six_attributes",
        ballots=[ballot],
        candidates=candidates,
        metadata={
            "election_id": "election-003",
            "seat_count": 3,
            "mode": "multi_seat_stv",
            "tie_break_order": ["cand-a", "cand-b", "cand-c"],
            "max_ranks_allowed": 3,
        },
    )

    assert ordered_candidate_ids == ["cand-a", "cand-c", "cand-b"]
    assert candidate_scores["cand-a"]["final_score"] > candidate_scores["cand-c"]["final_score"]
    assert candidate_scores["cand-c"]["final_score"] > candidate_scores["cand-b"]["final_score"]
    assert [group.candidate_ids[0] for group in ballot.rankings] == ["cand-a", "cand-c", "cand-b"]
    assert [group.rank for group in ballot.rankings] == [1, 2, 3]
    assert output_path.exists()


def test_generates_many_elector_units_with_multiple_individual_ballots() -> None:
    """Generate many elector units and multiple per-unit ballots from profile scoring."""
    election_id = "election-004"
    candidates = [
        Candidate(
            candidate_id="cand-a",
            election_id=election_id,
            profile={
                "ideology_score": 0.15,
                "party_id": "D",
                "home_region": "north",
                "community_tags": {"labor", "urban"},
                "issue_tags": {"housing", "education"},
                "candidate_quality": 82.0,
            },
        ),
        Candidate(
            candidate_id="cand-b",
            election_id=election_id,
            profile={
                "ideology_score": -0.70,
                "party_id": "R",
                "home_region": "south",
                "community_tags": {"rural", "veterans"},
                "issue_tags": {"public_safety", "taxes"},
                "candidate_quality": 78.0,
            },
        ),
        Candidate(
            candidate_id="cand-c",
            election_id=election_id,
            profile={
                "ideology_score": 0.55,
                "party_id": "D",
                "home_region": "west",
                "community_tags": {"college_town", "immigrant_community"},
                "issue_tags": {"climate", "housing"},
                "candidate_quality": 68.0,
            },
        ),
        Candidate(
            candidate_id="cand-d",
            election_id=election_id,
            profile={
                "ideology_score": -0.10,
                "party_id": "I",
                "home_region": "east",
                "community_tags": {"suburban", "small_business"},
                "issue_tags": {"healthcare", "education"},
                "candidate_quality": 74.0,
            },
        ),
    ]
    attribute_specs = get_starter_attribute_specs(STARTER_ACTIVE_ATTRIBUTES)
    preference_model = PreferenceModel(
        preference_model_id="pref-004",
        experiment_id="exp-004",
        name="starter-six-large-sample",
        active_attributes=STARTER_ACTIVE_ATTRIBUTES,
        attribute_weights=STARTER_ATTRIBUTE_WEIGHTS,
        missing_value_policy="ignore",
        ranking_method="deterministic_sort",
    )
    generation_run = BallotGenerationRun(
        generation_run_id="run-004",
        election_id=election_id,
        preference_model_id=preference_model.preference_model_id,
        random_seed=202,
    )

    ideology_cycle = [-0.85, -0.55, -0.25, 0.05, 0.35, 0.65]
    party_cycle = ["R", "R", "I", "D", "D", "D"]
    region_cycle = ["north", "south", "east", "west"]
    community_cycle = [
        {"rural", "veterans"},
        {"small_business", "suburban"},
        {"labor", "urban"},
        {"college_town", "immigrant_community"},
    ]
    issue_cycle = [
        {"public_safety", "taxes"},
        {"healthcare", "education"},
        {"housing", "education"},
        {"climate", "housing"},
    ]

    elector_units: list[ElectorUnit] = []
    for index in range(24):
        elector_units.append(
            ElectorUnit(
                elector_unit_id=f"block-{index:02d}",
                election_id=election_id,
                size=250 + (index * 10),
                profile={
                    "ideology_score": ideology_cycle[index % len(ideology_cycle)],
                    "party_id": party_cycle[index % len(party_cycle)],
                    "home_region": region_cycle[index % len(region_cycle)],
                    "community_tags": community_cycle[index % len(community_cycle)],
                    "issue_tags": issue_cycle[index % len(issue_cycle)],
                },
            )
        )

    ballots_per_elector_unit = 3
    ballots: list[Ballot] = []
    for elector_unit in elector_units:
        for ballot_index in range(ballots_per_elector_unit):
            # Build each ballot from an independent scoring pass.
            candidate_scores = score_candidates_for_elector_unit(
                candidates=candidates,
                elector_unit=elector_unit,
                attribute_specs=attribute_specs,
                preference_model=preference_model,
            )
            ordered_candidate_ids = [
                candidate_id
                for candidate_id, _ in sorted(
                    candidate_scores.items(),
                    key=lambda item: (item[1]["final_score"], item[0]),
                    reverse=True,
                )
            ]
            ballots.append(
                Ballot(
                    ballot_id=f"ballot-{elector_unit.elector_unit_id}-{ballot_index:02d}",
                    generation_run_id=generation_run.generation_run_id,
                    source_elector_unit_id=elector_unit.elector_unit_id,
                    rankings=[
                        RankGroup(rank=rank + 1, candidate_ids=[candidate_id])
                        for rank, candidate_id in enumerate(ordered_candidate_ids)
                    ],
                )
            )

    assert len(elector_units) >= 20
    assert len(ballots) == len(elector_units) * ballots_per_elector_unit
    assert len({ballot.ballot_id for ballot in ballots}) == len(ballots)

    for ballot in ballots:
        assert ballot.generation_run_id == generation_run.generation_run_id
        assert len(ballot.rankings) == len(candidates)
        assert [group.rank for group in ballot.rankings] == [1, 2, 3, 4]
        ranked_ids = [group.candidate_ids[0] for group in ballot.rankings]
        assert len(set(ranked_ids)) == len(candidates)

    unique_orders = {
        tuple(group.candidate_ids[0] for group in ballot.rankings) for ballot in ballots
    }
    assert len(unique_orders) >= 2
    output_path = write_simulation_ready_output(
        test_name="test_generates_many_elector_units_with_multiple_individual_ballots",
        ballots=ballots,
        candidates=candidates,
        metadata={
            "election_id": election_id,
            "seat_count": 3,
            "mode": "multi_seat_stv",
            "tie_break_order": ["cand-a", "cand-b", "cand-c", "cand-d"],
            "max_ranks_allowed": 4,
        },
    )
    assert output_path.exists()

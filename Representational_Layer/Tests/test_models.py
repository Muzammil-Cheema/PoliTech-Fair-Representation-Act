from random import Random

from Representational_Layer import (
    Ballot,
    BallotGenerationRun,
    Candidate,
    District,
    Election,
    ElectorUnit,
    Experiment,
    PreferenceModel,
    RankGroup,
    generate_ballot,
)


def test_can_build_minimal_experiment_graph() -> None:
    """Smoke test the first representational-layer experiment configuration.

    This models a single experiment with one district and one 3-seat STV
    election, plus the minimum related entities needed to generate ballots.
    """
    experiment = Experiment(experiment_id="exp-001")
    district = District(
        district_id="district-001",
        experiment_id=experiment.experiment_id,
        population=100_000,
        seat_target=3,
    )
    election = Election(
        election_id="election-001",
        experiment_id=experiment.experiment_id,
        district_id=district.district_id,
        mode="multi_seat_stv",
        max_rankings_allowed=5,
    )
    candidate = Candidate(candidate_id="cand-001", election_id=election.election_id)
    elector_unit = ElectorUnit(
        elector_unit_id="block-001",
        election_id=election.election_id,
        size=250,
    )
    preference_model = PreferenceModel(
        preference_model_id="pref-001",
        experiment_id=experiment.experiment_id,
        name="baseline",
        temperature=1.0,
    )
    generation_run = BallotGenerationRun(
        generation_run_id="run-001",
        election_id=election.election_id,
        preference_model_id=preference_model.preference_model_id,
        random_seed=42,
    )
    ballot = Ballot(
        ballot_id="ballot-001",
        generation_run_id=generation_run.generation_run_id,
        source_elector_unit_id=elector_unit.elector_unit_id,
        rankings=[RankGroup(rank=1, candidate_ids=[candidate.candidate_id])],
    )

    assert district.experiment_id == experiment.experiment_id
    assert election.district_id == district.district_id
    assert election.mode == "multi_seat_stv"
    assert election.max_rankings_allowed == 5
    assert candidate.profile == {}
    assert elector_unit.profile == {}
    assert preference_model.parameters == {}
    assert generation_run.random_seed == 42
    assert ballot.source_elector_unit_id == elector_unit.elector_unit_id
    assert ballot.rankings[0].candidate_ids == [candidate.candidate_id]


def test_can_generate_rankings_for_multiple_elector_units() -> None:
    """Generate one ballot per elector unit using different candidate weights.

    This is a first behavioral test for the representational layer:
    two voter blocks in the same election use different preference
    distributions over the same candidate slate.
    """
    experiment = Experiment(experiment_id="exp-002")
    district = District(
        district_id="district-002",
        experiment_id=experiment.experiment_id,
        population=120_000,
        seat_target=3,
    )
    election = Election(
        election_id="election-002",
        experiment_id=experiment.experiment_id,
        district_id=district.district_id,
        mode="multi_seat_stv",
        max_rankings_allowed=3,
    )
    candidates = [
        Candidate(candidate_id="cand-a", election_id=election.election_id),
        Candidate(candidate_id="cand-b", election_id=election.election_id),
        Candidate(candidate_id="cand-c", election_id=election.election_id),
    ]
    elector_units = [
        ElectorUnit(
            elector_unit_id="block-north",
            election_id=election.election_id,
            size=400,
        ),
        ElectorUnit(
            elector_unit_id="block-south",
            election_id=election.election_id,
            size=600,
        ),
    ]
    preference_model = PreferenceModel(
        preference_model_id="pref-002",
        experiment_id=experiment.experiment_id,
        name="hardcoded_weighted_ranking",
        temperature=1.0,
        parameters={"method": "weighted_without_replacement"},
    )
    generation_run = BallotGenerationRun(
        generation_run_id="run-002",
        election_id=election.election_id,
        preference_model_id=preference_model.preference_model_id,
        random_seed=42,
    )

    elector_unit_probabilities = {
        "block-north": {
            "cand-a": 0.70,
            "cand-b": 0.20,
            "cand-c": 0.10,
        },
        "block-south": {
            "cand-a": 0.10,
            "cand-b": 0.25,
            "cand-c": 0.65,
        },
    }

    ballots = [
        generate_ballot(
            ballot_id="ballot-north",
            generation_run_id=generation_run.generation_run_id,
            source_elector_unit_id=elector_units[0].elector_unit_id,
            candidates=candidates,
            candidate_probabilities=elector_unit_probabilities[elector_units[0].elector_unit_id],
            rng=Random(42),
        ),
        generate_ballot(
            ballot_id="ballot-south",
            generation_run_id=generation_run.generation_run_id,
            source_elector_unit_id=elector_units[1].elector_unit_id,
            candidates=candidates,
            candidate_probabilities=elector_unit_probabilities[elector_units[1].elector_unit_id],
            rng=Random(42),
        ),
    ]

    north_order = [rank_group.candidate_ids[0] for rank_group in ballots[0].rankings]
    south_order = [rank_group.candidate_ids[0] for rank_group in ballots[1].rankings]

    assert len(ballots) == 2
    assert all(len(ballot.rankings) == len(candidates) for ballot in ballots)
    assert north_order == ["cand-a", "cand-b", "cand-c"]
    assert south_order == ["cand-c", "cand-a", "cand-b"]
    assert len(set(north_order)) == len(candidates)
    assert len(set(south_order)) == len(candidates)

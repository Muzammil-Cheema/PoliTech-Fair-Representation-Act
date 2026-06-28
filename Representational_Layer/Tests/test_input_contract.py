from pathlib import Path
import re

import pytest

from Representational_Layer import (
    AttributeSpec,
    BallotGenerationRun,
    Candidate,
    ContractValidationError,
    District,
    Election,
    ElectorUnit,
    Experiment,
    PreferenceModel,
    load_experiment_contract,
)


FIXTURE_DIR = Path(__file__).parent / "Input_Contracts"


def fixture_path(fixture_name: str) -> Path:
    return FIXTURE_DIR / fixture_name


def load_fixture(fixture_name: str):
    return load_experiment_contract(fixture_path(fixture_name))


def assert_contract_rejected(fixture_name: str, message: str) -> None:
    with pytest.raises(ContractValidationError, match=re.escape(message)):
        load_fixture(fixture_name)


def test_loads_valid_representational_input_contract() -> None:
    state = load_fixture("valid_starter_and_custom_contract.json")

    assert isinstance(state.experiment, Experiment)
    assert all(isinstance(district, District) for district in state.districts)
    assert all(isinstance(election, Election) for election in state.elections)
    assert all(isinstance(spec, AttributeSpec) for spec in state.attribute_specs)
    assert all(isinstance(candidate, Candidate) for candidate in state.candidates)
    assert all(isinstance(unit, ElectorUnit) for unit in state.elector_units)
    assert all(isinstance(model, PreferenceModel) for model in state.preference_models)
    assert all(
        isinstance(run, BallotGenerationRun)
        for run in state.ballot_generation_runs
    )


@pytest.mark.parametrize(
    ("fixture_name", "message"),
    [
        (
            "invalid_missing_experiment_id.json",
            "experiment is missing mandatory keys: experiment_id",
        ),
        (
            "invalid_max_rankings_below_seat_target.json",
            "max_rankings_allowed must be at least district seat_target=3",
        ),
        (
            "invalid_unknown_active_attribute.json",
            "active_attributes references unknown attribute 'unknown_attribute'",
        ),
        (
            "invalid_attribute_weight_mismatch.json",
            "attribute_weights keys must exactly match active_attributes",
        ),
        (
            "invalid_custom_attribute_missing_config.json",
            "config is mandatory when comparison_mode is 'custom'",
        ),
        (
            "invalid_missing_temperature.json",
            "preference_models[0] is missing mandatory keys: temperature",
        ),
        (
            "invalid_wrong_top_level_order.json",
            "contract keys must appear in this order",
        ),
    ],
)
def test_rejects_invalid_representational_input_contracts(
    fixture_name: str,
    message: str,
) -> None:
    assert_contract_rejected(fixture_name, message)

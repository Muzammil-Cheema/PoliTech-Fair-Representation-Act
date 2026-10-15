import json
from pathlib import Path

import pytest

from MMD_Generation_Layer import config as project_config
from MMD_Generation_Layer.Processor.runtime_setup import (
    VALID_RECOM_VARIANTS,
    apply_run_config,
    default_run_config,
    load_run_config,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "Notebook_Run_Configs"
VALID_FIXTURES = sorted(
    path for path in FIXTURE_DIR.glob("*.json") if not path.name.startswith("invalid_")
)
INVALID_FIXTURES = sorted(FIXTURE_DIR.glob("invalid_*.json"))


def mmd_config(**overrides) -> dict:
    """Return a minimal valid MMD config with optional overrides."""
    return {"generation_mode": "MMD", "num_districts": 7, "seat_vector": [3, 2, 2], **overrides}


@pytest.mark.parametrize("fixture_path", VALID_FIXTURES, ids=lambda path: path.name)
def test_valid_fixtures_load(fixture_path: Path) -> None:
    """Every non-invalid fixture loads into a RunConfig."""
    run_config = load_run_config(fixture_path)

    assert run_config.generation_mode in {"SMD", "MMD"}


@pytest.mark.parametrize("fixture_path", INVALID_FIXTURES, ids=lambda path: path.name)
def test_invalid_fixtures_raise(fixture_path: Path) -> None:
    """Every invalid fixture fails validation."""
    with pytest.raises(ValueError):
        load_run_config(fixture_path)


def test_default_run_config_uses_chain_defaults() -> None:
    """Defaults keep one saved plan per chain step and do not save the seed plan."""
    run_config = default_run_config()

    assert run_config.recom_variant == "district_pairs_mst"
    assert run_config.burn_in_steps == 0
    assert run_config.step_interval == 1
    assert run_config.max_seed_attempts == 10
    assert run_config.save_seed_plan is False
    assert run_config.seed_plan_path == project_config.output_dir / "seed_plan.json"


def test_chain_control_fixture_overrides_defaults() -> None:
    """The chain-controls fixture sets every new key to a non-default value."""
    run_config = load_run_config(FIXTURE_DIR / "mmd_valid_chain_controls_tn_small.json")

    assert run_config.recom_variant == "cut_edges_ust"
    assert run_config.burn_in_steps == 10
    assert run_config.step_interval == 3
    assert run_config.max_seed_attempts == 5
    assert run_config.save_seed_plan is True


@pytest.mark.parametrize("variant", VALID_RECOM_VARIANTS)
def test_every_recom_variant_is_accepted(variant: str) -> None:
    """All four MultiMemberReCom variants are valid config values."""
    assert apply_run_config(mmd_config(recom_variant=variant)).recom_variant == variant


def test_burn_in_steps_allows_zero() -> None:
    """Zero burn-in is valid (it is the default)."""
    assert apply_run_config(mmd_config(burn_in_steps=0)).burn_in_steps == 0


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"recom_variant": "recom"}, "recom_variant must be one of"),
        ({"recom_variant": 3}, "recom_variant must be one of"),
        ({"burn_in_steps": -1}, "burn_in_steps must be a non-negative integer"),
        ({"burn_in_steps": True}, "burn_in_steps must be a non-negative integer"),
        ({"step_interval": 0}, "step_interval must be a positive integer"),
        ({"step_interval": 1.5}, "step_interval must be a positive integer"),
        ({"max_seed_attempts": 0}, "max_seed_attempts must be a positive integer"),
        ({"max_seed_attempts": False}, "max_seed_attempts must be a positive integer"),
        ({"save_seed_plan": "yes"}, "save_seed_plan must be a boolean"),
        ({"num_districts": 3, "seat_vector": [3]}, "at least 2 districts"),
    ],
)
def test_invalid_chain_controls_raise_specific_messages(overrides: dict, message: str) -> None:
    """Each new rule fails fast with a message naming the offending key."""
    with pytest.raises(ValueError, match=message):
        apply_run_config(mmd_config(**overrides))


def test_single_district_rule_only_applies_in_mmd_mode() -> None:
    """The at-least-2-districts rule only applies in MMD mode."""
    run_config = apply_run_config({"generation_mode": "SMD", "num_districts": 3, "seat_vector": [3]})

    assert run_config.generation_mode == "SMD"


@pytest.mark.parametrize(
    "removed_key",
    ["mmd_smd_multiplier", "mmd_plans_per_smd_plan", "max_mmd_attempts_per_smd_plan", "save_intermediate_smd_plans"],
)
@pytest.mark.parametrize("generation_mode", ["MMD", "SMD"])
def test_removed_temporary_smd_keys_are_rejected(removed_key: str, generation_mode: str) -> None:
    """Keys from the temporary-SMD workflow fail fast with a migration message in either mode."""
    with pytest.raises(ValueError, match=f"{removed_key} was removed in the GerryChain 1.0.0 migration"):
        apply_run_config(mmd_config(generation_mode=generation_mode, **{removed_key: 1}))


def test_valid_fixtures_do_not_use_removed_keys() -> None:
    """No valid fixture still carries a removed temporary-SMD key."""
    removed = {"mmd_smd_multiplier", "mmd_plans_per_smd_plan", "max_mmd_attempts_per_smd_plan", "save_intermediate_smd_plans"}
    for fixture_path in VALID_FIXTURES:
        assert not removed & set(json.loads(fixture_path.read_text())), fixture_path.name


def test_run_config_has_no_temporary_smd_fields() -> None:
    """RunConfig no longer exposes temporary-SMD settings."""
    run_config = default_run_config()

    for field in ("mmd_smd_multiplier", "mmd_plans_per_smd_plan", "max_mmd_attempts_per_smd_plan",
                  "save_intermediate_smd_plans", "intermediate_smd_plans_dir"):
        assert not hasattr(run_config, field)

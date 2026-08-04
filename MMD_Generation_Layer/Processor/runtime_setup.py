"""Runtime configuration loading for MMD generation scripts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Global_Utilities import info, warn
from MMD_Generation_Layer import config as project_config


RUN_CONFIG_ALLOWED_KEYS = {
    "generation_mode",
    "num_plans",
    "num_districts",
    "seed",
    "shape_path",
    "id_column",
    "geom_column",
    "pop_column",
    "dem_column",
    "rep_column",
    "population_tolerance",
    "seat_vector",
    "mmd_seat_vector",
    "mmd_smd_multiplier",
    "mmd_plans_per_smd_plan",
    "max_mmd_attempts_per_smd_plan",
    "save_intermediate_smd_plans",
    "expected_behavior",
    "notes",
}


@dataclass(frozen=True)
class RunConfig:
    """Resolved runtime configuration for one generation run."""

    generation_mode: str
    num_plans: int
    num_districts: int
    seed: int
    shape_path: Path
    id_column: str
    geom_column: str
    pop_column: str
    dem_column: str
    rep_column: str
    seat_vector: tuple[int, ...]
    mmd_smd_multiplier: int
    mmd_plans_per_smd_plan: int
    population_tolerance: float
    max_mmd_attempts_per_smd_plan: int
    save_intermediate_smd_plans: bool
    output_dir: Path
    plans_dir: Path
    intermediate_smd_plans_dir: Path
    ensemble_csv_path: Path
    seat_share_png_path: Path


@dataclass(frozen=True)
class DashboardConfig:
    """Resolved config the dashboard needs to render a run's Outputs/."""

    shape_path: Path
    num_districts: int
    num_plans: int
    id_column: str
    geom_column: str


def load_dashboard_config(output_dir: Path | None = None) -> DashboardConfig:
    """Load dashboard config from Outputs/run_metadata.json, falling back to config.py defaults."""
    output_dir = output_dir or project_config.output_dir
    metadata_path = output_dir / "run_metadata.json"

    if metadata_path.exists():
        with metadata_path.open("r") as file:
            metadata = json.load(file)

        info(f"Loaded dashboard config from {metadata_path}")
        return DashboardConfig(
            shape_path=Path(metadata["shape_path"]),
            num_districts=int(metadata["num_districts"]),
            num_plans=int(metadata["num_plans"]),
            id_column=str(metadata["id_column"]),
            geom_column=str(metadata["geom_column"]),
        )

    warn(f"No run metadata found at {metadata_path}; falling back to config.py defaults (NC).")
    return DashboardConfig(
        shape_path=project_config.shape_path,
        num_districts=project_config.NUM_DISTRICTS,
        num_plans=project_config.NUM_PLANS,
        id_column=project_config.ID_COLUMN,
        geom_column=project_config.GEOM_COLUMN,
    )


def default_run_config() -> RunConfig:
    """Build the default script config from `MMD_Generation_Layer.config`."""
    return RunConfig(
        generation_mode=project_config.GENERATION_MODE,
        num_plans=project_config.NUM_PLANS,
        num_districts=project_config.NUM_DISTRICTS,
        seed=project_config.SEED,
        shape_path=project_config.shape_path,
        id_column=project_config.ID_COLUMN,
        geom_column=project_config.GEOM_COLUMN,
        pop_column=project_config.POP_COLUMN,
        dem_column=project_config.DEM_COLUMN,
        rep_column=project_config.REP_COLUMN,
        seat_vector=project_config.SEAT_VECTOR,
        mmd_smd_multiplier=project_config.MMD_SMD_MULTIPLIER,
        mmd_plans_per_smd_plan=project_config.MMD_PLANS_PER_SMD_PLAN,
        population_tolerance=project_config.POPULATION_TOLERANCE,
        max_mmd_attempts_per_smd_plan=project_config.MAX_MMD_ATTEMPTS_PER_SMD_PLAN,
        save_intermediate_smd_plans=project_config.SAVE_INTERMEDIATE_SMD_PLANS,
        output_dir=project_config.output_dir,
        plans_dir=project_config.plans_dir,
        intermediate_smd_plans_dir=project_config.intermediate_smd_plans_dir,
        ensemble_csv_path=project_config.ensemble_csv_path,
        seat_share_png_path=project_config.seat_share_png_path,
    )


def resolve_run_config_path(config_path: str | Path) -> Path:
    """Resolve config path against common project and processor roots."""
    raw_path = Path(config_path).expanduser()
    candidates = [raw_path]

    if not raw_path.is_absolute():
        candidates.append(project_config.processor_dir / raw_path)
        candidates.append(project_config.base_dir / raw_path)

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

    attempted = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Could not find config file. Tried: {attempted}")


def resolve_runtime_path(path_value: str | Path) -> Path:
    """Resolve runtime paths against common project and processor roots."""
    raw_path = Path(path_value).expanduser()
    candidates = [raw_path]

    if not raw_path.is_absolute():
        candidates.append(project_config.processor_dir / raw_path)
        candidates.append(project_config.base_dir / raw_path)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return raw_path


def validate_positive_int_list(name: str, value: Any) -> tuple[int, ...]:
    """Validate a non-empty list of positive integers."""
    if not isinstance(value, list) or len(value) == 0:
        raise ValueError(f"{name} must be a non-empty list")

    if any((not isinstance(item, int)) or item <= 0 for item in value):
        raise ValueError(f"{name} must contain only positive integers")

    return tuple(int(item) for item in value)


def extract_seat_vector_from_config(config: dict[str, Any]) -> tuple[int, ...] | None:
    """Return a validated seat vector from config or None when omitted."""
    if "mmd_seat_vector" in config:
        raise ValueError("mmd_seat_vector is no longer supported; use seat_vector")

    if "seat_vector" not in config:
        return None

    return validate_positive_int_list("seat_vector", config["seat_vector"])


def validate_run_config(config: dict[str, Any], base_config: RunConfig | None = None) -> None:
    """Validate JSON config before applying it to runtime values."""
    base_config = base_config or default_run_config()

    unknown_keys = sorted(set(config) - RUN_CONFIG_ALLOWED_KEYS)
    if unknown_keys:
        raise ValueError(f"Unsupported config keys: {unknown_keys}")

    mode = str(config.get("generation_mode", base_config.generation_mode)).strip().upper()
    if mode not in {"SMD", "MMD"}:
        raise ValueError("generation_mode must be 'SMD' or 'MMD'")

    for key in [
        "num_plans",
        "num_districts",
        "seed",
        "mmd_smd_multiplier",
        "mmd_plans_per_smd_plan",
        "max_mmd_attempts_per_smd_plan",
    ]:
        if key in config:
            value = config[key]
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{key} must be a positive integer")

    if "save_intermediate_smd_plans" in config:
        if not isinstance(config["save_intermediate_smd_plans"], bool):
            raise ValueError("save_intermediate_smd_plans must be a boolean")

    if "population_tolerance" in config:
        tolerance = config["population_tolerance"]
        if not isinstance(tolerance, (int, float)):
            raise ValueError("population_tolerance must be numeric")
        if tolerance <= 0 or tolerance >= 1:
            raise ValueError("population_tolerance must be between 0 and 1 (exclusive)")

    resolved_seat_vector = extract_seat_vector_from_config(config)

    if mode == "MMD":
        effective_seat_vector = resolved_seat_vector or base_config.seat_vector
        if not effective_seat_vector:
            raise ValueError("seat_vector is required when generation_mode is 'MMD'")

        effective_num_districts = int(config.get("num_districts", base_config.num_districts))
        effective_total_seats = sum(int(seat_count) for seat_count in effective_seat_vector)
        if effective_total_seats != effective_num_districts:
            raise ValueError(
                "MMD seat-vector sum mismatch: "
                f"sum(seat_vector)={effective_total_seats} "
                f"but num_districts={effective_num_districts}"
            )


def apply_run_config(
    config: dict[str, Any],
    base_config: RunConfig | None = None,
) -> RunConfig:
    """Apply JSON config values over defaults and return a resolved config."""
    base_config = base_config or default_run_config()
    validate_run_config(config, base_config)

    seat_vector = extract_seat_vector_from_config(config) or base_config.seat_vector

    return RunConfig(
        generation_mode=str(config.get("generation_mode", base_config.generation_mode)).strip().upper(),
        num_plans=int(config.get("num_plans", base_config.num_plans)),
        num_districts=int(config.get("num_districts", base_config.num_districts)),
        seed=int(config.get("seed", base_config.seed)),
        shape_path=resolve_runtime_path(config.get("shape_path", base_config.shape_path)),
        id_column=str(config.get("id_column", base_config.id_column)),
        geom_column=str(config.get("geom_column", base_config.geom_column)),
        pop_column=str(config.get("pop_column", base_config.pop_column)),
        dem_column=str(config.get("dem_column", base_config.dem_column)),
        rep_column=str(config.get("rep_column", base_config.rep_column)),
        seat_vector=seat_vector,
        mmd_smd_multiplier=int(config.get("mmd_smd_multiplier", base_config.mmd_smd_multiplier)),
        mmd_plans_per_smd_plan=int(
            config.get("mmd_plans_per_smd_plan", base_config.mmd_plans_per_smd_plan)
        ),
        population_tolerance=float(config.get("population_tolerance", base_config.population_tolerance)),
        max_mmd_attempts_per_smd_plan=int(
            config.get(
                "max_mmd_attempts_per_smd_plan",
                base_config.max_mmd_attempts_per_smd_plan,
            )
        ),
        save_intermediate_smd_plans=bool(
            config.get(
                "save_intermediate_smd_plans",
                base_config.save_intermediate_smd_plans,
            )
        ),
        output_dir=base_config.output_dir,
        plans_dir=base_config.plans_dir,
        intermediate_smd_plans_dir=base_config.intermediate_smd_plans_dir,
        ensemble_csv_path=base_config.ensemble_csv_path,
        seat_share_png_path=base_config.seat_share_png_path,
    )


def load_run_config(config_path: str | Path, base_config: RunConfig | None = None) -> RunConfig:
    """Load and validate JSON config from disk."""
    base_config = base_config or default_run_config()
    resolved_path = resolve_run_config_path(config_path)

    with resolved_path.open("r") as file:
        config = json.load(file)

    run_config = apply_run_config(config, base_config)
    info(f"Applied run config from {resolved_path}")
    return run_config


def bootstrap_run_config(config_path: str | Path | None = None) -> RunConfig:
    """Return config defaults, optionally overridden by a JSON config file."""
    base_config = default_run_config()

    if config_path is None or str(config_path).strip() == "":
        info("CONFIG_PATH not set; using config.py defaults.")
        return base_config

    try:
        return load_run_config(config_path, base_config)
    except Exception as exc:
        warn("Failed to load run config; continuing with config.py defaults.")
        warn(f"path: {config_path}")
        warn(f"error: {type(exc).__name__}: {exc}")
        return base_config


def describe_run_config(run_config: RunConfig) -> None:
    """Log the important settings for traceability."""
    info(f"generation_mode: {run_config.generation_mode}")
    info(f"num_plans: {run_config.num_plans}")
    info(f"num_districts: {run_config.num_districts}")
    info(f"seed: {run_config.seed}")
    info(f"population_tolerance: {run_config.population_tolerance}")
    info(f"seat_vector: {list(run_config.seat_vector)}")
    info(f"save_intermediate_smd_plans: {run_config.save_intermediate_smd_plans}")

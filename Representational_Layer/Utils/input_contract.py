from __future__ import annotations

from copy import deepcopy
from dataclasses import MISSING, dataclass, fields
import json
from math import isfinite
from pathlib import Path
from typing import Any, Mapping, Sequence, get_args

from .models import (
    AttributeSpec,
    AttributeType,
    BallotGenerationRun,
    Candidate,
    ComparisonMode,
    District,
    Election,
    ElectionMode,
    ElectorUnit,
    Experiment,
    MissingValuePolicy,
    PreferenceModel,
    RankingMethod,
    ScoreStyle,
)


class ContractValidationError(ValueError):
    """Raised when a representational experiment input contract is invalid."""


@dataclass(frozen=True)
class RepresentationalExperimentState:
    """Validated model objects created from one representational JSON contract."""

    experiment: Experiment
    districts: list[District]
    elections: list[Election]
    attribute_specs: list[AttributeSpec]
    candidates: list[Candidate]
    elector_units: list[ElectorUnit]
    preference_models: list[PreferenceModel]
    ballot_generation_runs: list[BallotGenerationRun]


# Model-shape layer: allowed keys and default mandatory fields come directly
# from dataclass definitions so the contract stays aligned with models.py.
def _model_keys(model_type: type[Any], *, exclude: set[str] | None = None) -> list[str]:
    excluded = exclude or set()
    return [
        field.name
        for field in fields(model_type)
        if field.init and field.name not in excluded
    ]


def _required_model_keys(
    model_type: type[Any],
    *,
    exclude: set[str] | None = None,
    require: set[str] | None = None,
    optional: set[str] | None = None,
) -> list[str]:
    required = set(require or set())
    optional_fields = optional or set()
    excluded = exclude or set()

    for field in fields(model_type):
        if field.name in excluded:
            continue
        if field.default is MISSING and field.default_factory is MISSING:
            required.add(field.name)

    required -= optional_fields
    return [key for key in _model_keys(model_type, exclude=excluded) if key in required]


_ASSIGNED_EXPERIMENT_FIELD = {"experiment_id"}

TOP_LEVEL_KEYS = _model_keys(RepresentationalExperimentState)
EXPERIMENT_KEYS = _model_keys(Experiment)
DISTRICT_KEYS = _model_keys(District, exclude=_ASSIGNED_EXPERIMENT_FIELD)
ELECTION_KEYS = _model_keys(Election, exclude=_ASSIGNED_EXPERIMENT_FIELD)
ATTRIBUTE_SPEC_KEYS = _model_keys(AttributeSpec, exclude=_ASSIGNED_EXPERIMENT_FIELD)
CANDIDATE_KEYS = _model_keys(Candidate)
ELECTOR_UNIT_KEYS = _model_keys(ElectorUnit)
PREFERENCE_MODEL_KEYS = _model_keys(
    PreferenceModel,
    exclude=_ASSIGNED_EXPERIMENT_FIELD,
)
BALLOT_GENERATION_RUN_KEYS = _model_keys(BallotGenerationRun)

# Explicit contract-policy layer: these rules describe what the user-authored
# JSON must provide beyond dataclass shape. Experiment.experiment_id remains
# user-authored; experiment_id is assigned internally for the other classes.
TOP_LEVEL_REQUIRED_KEYS = _required_model_keys(RepresentationalExperimentState)
EXPERIMENT_REQUIRED_KEYS = _required_model_keys(Experiment)
DISTRICT_REQUIRED_KEYS = _required_model_keys(
    District,
    exclude=_ASSIGNED_EXPERIMENT_FIELD,
)
ELECTION_REQUIRED_KEYS = _required_model_keys(
    Election,
    exclude=_ASSIGNED_EXPERIMENT_FIELD,
)
ATTRIBUTE_SPEC_REQUIRED_KEYS = ["name"]
NEW_ATTRIBUTE_SPEC_REQUIRED_KEYS = _required_model_keys(
    AttributeSpec,
    exclude=_ASSIGNED_EXPERIMENT_FIELD,
)
CANDIDATE_REQUIRED_KEYS = _required_model_keys(Candidate, require={"profile"})
ELECTOR_UNIT_REQUIRED_KEYS = _required_model_keys(ElectorUnit, require={"profile"})
PREFERENCE_MODEL_REQUIRED_KEYS = _required_model_keys(
    PreferenceModel,
    exclude=_ASSIGNED_EXPERIMENT_FIELD,
    require={"active_attributes", "attribute_weights"},
)
BALLOT_GENERATION_RUN_REQUIRED_KEYS = _required_model_keys(BallotGenerationRun)

VALID_ELECTION_MODES = set(get_args(ElectionMode))
VALID_ATTRIBUTE_TYPES = set(get_args(AttributeType))
VALID_COMPARISON_MODES = set(get_args(ComparisonMode))
VALID_SCORE_STYLES = set(get_args(ScoreStyle))
VALID_MISSING_VALUE_POLICIES = set(get_args(MissingValuePolicy))
VALID_RANKING_METHODS = set(get_args(RankingMethod))


def load_experiment_contract(path: str | Path) -> RepresentationalExperimentState:
    """Load and strictly validate a representational experiment JSON contract."""
    contract_path = Path(path)
    try:
        with contract_path.open("r", encoding="utf-8") as contract_file:
            contract = json.load(
                contract_file,
                object_pairs_hook=_object_pairs_without_duplicates,
            )
    except OSError as exc:
        raise ContractValidationError(
            f"Could not read representational contract '{contract_path}': {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ContractValidationError(
            f"Could not parse representational contract '{contract_path}': {exc}"
        ) from exc

    return parse_experiment_contract(contract)


def parse_experiment_contract(
    contract: Mapping[str, Any],
) -> RepresentationalExperimentState:
    """Validate a contract object and convert it into representational models."""
    _require_mapping(contract, "contract")
    _validate_keys(
        contract,
        "contract",
        allowed_keys=TOP_LEVEL_KEYS,
        required_keys=TOP_LEVEL_REQUIRED_KEYS,
    )

    experiment = _parse_experiment(contract["experiment"])
    districts = _parse_districts(contract["districts"], experiment.experiment_id)
    district_by_id = _index_unique(
        districts,
        key_name="district_id",
        key_func=lambda district: district.district_id,
        path="districts",
    )

    elections = _parse_elections(
        contract["elections"],
        experiment.experiment_id,
        district_by_id,
    )
    election_by_id = _index_unique(
        elections,
        key_name="election_id",
        key_func=lambda election: election.election_id,
        path="elections",
    )

    attribute_specs = _parse_attribute_specs(
        contract["attribute_specs"],
        experiment.experiment_id,
    )
    attribute_specs_by_name = _index_unique(
        attribute_specs,
        key_name="name",
        key_func=lambda spec: spec.name,
        path="attribute_specs",
    )
    _index_unique(
        attribute_specs,
        key_name="attribute_spec_id",
        key_func=lambda spec: spec.attribute_spec_id,
        path="attribute_specs",
    )

    candidates = _parse_candidates(
        contract["candidates"],
        election_by_id,
        district_by_id,
    )
    elector_units = _parse_elector_units(contract["elector_units"], election_by_id)
    preference_models = _parse_preference_models(
        contract["preference_models"],
        experiment.experiment_id,
        attribute_specs_by_name,
    )
    attribute_specs = _include_referenced_starter_specs(
        attribute_specs,
        preference_models,
        experiment.experiment_id,
    )
    _index_unique(
        attribute_specs,
        key_name="name",
        key_func=lambda spec: spec.name,
        path="attribute_specs",
    )
    _index_unique(
        attribute_specs,
        key_name="attribute_spec_id",
        key_func=lambda spec: spec.attribute_spec_id,
        path="attribute_specs",
    )
    preference_model_by_id = _index_unique(
        preference_models,
        key_name="preference_model_id",
        key_func=lambda model: model.preference_model_id,
        path="preference_models",
    )

    ballot_generation_runs = _parse_ballot_generation_runs(
        contract["ballot_generation_runs"],
        election_by_id,
        preference_model_by_id,
    )

    return RepresentationalExperimentState(
        experiment=experiment,
        districts=districts,
        elections=elections,
        attribute_specs=attribute_specs,
        candidates=candidates,
        elector_units=elector_units,
        preference_models=preference_models,
        ballot_generation_runs=ballot_generation_runs,
    )


def _object_pairs_without_duplicates(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ContractValidationError(f"Duplicate key '{key}' in JSON object.")
        obj[key] = value
    return obj


def _parse_experiment(raw_experiment: Any) -> Experiment:
    path = "experiment"
    experiment = _require_mapping(raw_experiment, path)
    _validate_keys(
        experiment,
        path,
        allowed_keys=EXPERIMENT_KEYS,
        required_keys=EXPERIMENT_REQUIRED_KEYS,
    )
    return Experiment(
        experiment_id=_required_string(experiment, "experiment_id", path),
        description=_optional_string(experiment, "description", path),
    )


def _parse_districts(raw_districts: Any, experiment_id: str) -> list[District]:
    districts = _require_non_empty_list(raw_districts, "districts")
    parsed: list[District] = []
    for index, raw_district in enumerate(districts):
        path = f"districts[{index}]"
        district = _require_mapping(raw_district, path)
        _validate_keys(
            district,
            path,
            allowed_keys=DISTRICT_KEYS,
            required_keys=DISTRICT_REQUIRED_KEYS,
        )
        parsed.append(
            District(
                district_id=_required_string(district, "district_id", path),
                experiment_id=experiment_id,
                population=_required_positive_int(district, "population", path),
                seat_target=_required_positive_int(district, "seat_target", path),
                geometry=district.get("geometry"),
            )
        )
    return parsed


def _parse_elections(
    raw_elections: Any,
    experiment_id: str,
    district_by_id: Mapping[str, District],
) -> list[Election]:
    elections = _require_non_empty_list(raw_elections, "elections")
    if len(elections) != len(district_by_id):
        raise ContractValidationError(
            "elections must contain exactly one election for each district."
        )

    parsed: list[Election] = []
    seen_district_ids: set[str] = set()
    for index, raw_election in enumerate(elections):
        path = f"elections[{index}]"
        election = _require_mapping(raw_election, path)
        _validate_keys(
            election,
            path,
            allowed_keys=ELECTION_KEYS,
            required_keys=ELECTION_REQUIRED_KEYS,
        )

        district_id = _required_string(election, "district_id", path)
        if district_id not in district_by_id:
            raise ContractValidationError(
                f"{path}.district_id references unknown district '{district_id}'."
            )
        if district_id in seen_district_ids:
            raise ContractValidationError(
                f"elections contains more than one election for district '{district_id}'."
            )
        seen_district_ids.add(district_id)

        max_rankings_allowed = _required_positive_int(
            election,
            "max_rankings_allowed",
            path,
        )
        seat_target = district_by_id[district_id].seat_target
        if max_rankings_allowed < seat_target:
            raise ContractValidationError(
                f"{path}.max_rankings_allowed must be at least district "
                f"seat_target={seat_target}."
            )

        parsed.append(
            Election(
                election_id=_required_string(election, "election_id", path),
                experiment_id=experiment_id,
                district_id=district_id,
                mode=_required_literal(
                    election,
                    "mode",
                    path,
                    VALID_ELECTION_MODES,
                ),
                max_rankings_allowed=max_rankings_allowed,
            )
        )

    missing_district_ids = set(district_by_id) - seen_district_ids
    if missing_district_ids:
        raise ContractValidationError(
            "elections is missing districts: "
            f"{', '.join(sorted(missing_district_ids))}."
        )
    return parsed


def _parse_attribute_specs(
    raw_attribute_specs: Any,
    experiment_id: str,
) -> list[AttributeSpec]:
    attribute_specs = _require_list(raw_attribute_specs, "attribute_specs")
    parsed: list[AttributeSpec] = []
    starter_specs = _starter_specs_by_name()

    for index, raw_spec in enumerate(attribute_specs):
        path = f"attribute_specs[{index}]"
        spec = _require_mapping(raw_spec, path)
        _validate_keys(
            spec,
            path,
            allowed_keys=ATTRIBUTE_SPEC_KEYS,
            required_keys=ATTRIBUTE_SPEC_REQUIRED_KEYS,
        )

        name = _required_string(spec, "name", path)
        base_spec = deepcopy(starter_specs[name]) if name in starter_specs else None
        is_new_spec = base_spec is None

        if is_new_spec:
            for field_name in NEW_ATTRIBUTE_SPEC_REQUIRED_KEYS:
                if field_name not in spec:
                    raise ContractValidationError(
                        f"{path}.{field_name} is mandatory for new attributes."
                    )
        else:
            base_spec.experiment_id = experiment_id

        attribute_type = _optional_literal(
            spec,
            "attribute_type",
            path,
            VALID_ATTRIBUTE_TYPES,
            default=base_spec.attribute_type if base_spec else None,
        )
        comparison_mode = _optional_literal(
            spec,
            "comparison_mode",
            path,
            VALID_COMPARISON_MODES,
            default=base_spec.comparison_mode if base_spec else None,
        )
        score_style = _optional_literal(
            spec,
            "score_style",
            path,
            VALID_SCORE_STYLES,
            default=base_spec.score_style if base_spec else None,
        )
        value_min = _optional_number(
            spec,
            "value_min",
            path,
            default=base_spec.value_min if base_spec else None,
        )
        value_max = _optional_number(
            spec,
            "value_max",
            path,
            default=base_spec.value_max if base_spec else None,
        )
        if (
            value_min is not None
            and value_max is not None
            and value_max <= value_min
        ):
            raise ContractValidationError(
                f"{path}.value_max must be greater than value_min."
            )

        raw_config = spec.get("config")
        if comparison_mode == "custom":
            if "config" not in spec:
                raise ContractValidationError(
                    f"{path}.config is mandatory when comparison_mode is 'custom'."
                )
            config = _require_non_empty_mapping(raw_config, f"{path}.config")
        else:
            if "config" in spec and raw_config is not None:
                _require_mapping(raw_config, f"{path}.config")
            config = {}

        parsed.append(
            AttributeSpec(
                attribute_spec_id=_optional_string(
                    spec,
                    "attribute_spec_id",
                    path,
                    default=base_spec.attribute_spec_id if base_spec else None,
                ),
                experiment_id=experiment_id,
                name=name,
                attribute_type=attribute_type,
                comparison_mode=comparison_mode,
                score_style=score_style,
                value_min=value_min,
                value_max=value_max,
                config=dict(config),
                description=_optional_string(
                    spec,
                    "description",
                    path,
                    default=base_spec.description if base_spec else None,
                ),
            )
        )

    return parsed


def _parse_candidates(
    raw_candidates: Any,
    election_by_id: Mapping[str, Election],
    district_by_id: Mapping[str, District],
) -> list[Candidate]:
    candidates = _require_non_empty_list(raw_candidates, "candidates")
    parsed: list[Candidate] = []
    for index, raw_candidate in enumerate(candidates):
        path = f"candidates[{index}]"
        candidate = _require_mapping(raw_candidate, path)
        _validate_keys(
            candidate,
            path,
            allowed_keys=CANDIDATE_KEYS,
            required_keys=CANDIDATE_REQUIRED_KEYS,
        )

        election_id = _required_string(candidate, "election_id", path)
        if election_id not in election_by_id:
            raise ContractValidationError(
                f"{path}.election_id references unknown election '{election_id}'."
            )

        home_district_id = _optional_string(candidate, "home_district_id", path)
        if home_district_id is not None and home_district_id not in district_by_id:
            raise ContractValidationError(
                f"{path}.home_district_id references unknown district "
                f"'{home_district_id}'."
            )

        parsed.append(
            Candidate(
                candidate_id=_required_string(candidate, "candidate_id", path),
                election_id=election_id,
                withdrawn=_optional_bool(candidate, "withdrawn", path, default=False),
                home_district_id=home_district_id,
                profile=dict(
                    _require_non_empty_mapping(
                        candidate["profile"],
                        f"{path}.profile",
                    )
                ),
            )
        )

    _index_unique(
        parsed,
        key_name="candidate_id",
        key_func=lambda candidate: candidate.candidate_id,
        path="candidates",
    )
    return parsed


def _parse_elector_units(
    raw_elector_units: Any,
    election_by_id: Mapping[str, Election],
) -> list[ElectorUnit]:
    elector_units = _require_non_empty_list(raw_elector_units, "elector_units")
    parsed: list[ElectorUnit] = []
    for index, raw_elector_unit in enumerate(elector_units):
        path = f"elector_units[{index}]"
        elector_unit = _require_mapping(raw_elector_unit, path)
        _validate_keys(
            elector_unit,
            path,
            allowed_keys=ELECTOR_UNIT_KEYS,
            required_keys=ELECTOR_UNIT_REQUIRED_KEYS,
        )

        election_id = _required_string(elector_unit, "election_id", path)
        if election_id not in election_by_id:
            raise ContractValidationError(
                f"{path}.election_id references unknown election '{election_id}'."
            )

        parsed.append(
            ElectorUnit(
                elector_unit_id=_required_string(
                    elector_unit,
                    "elector_unit_id",
                    path,
                ),
                election_id=election_id,
                size=_required_positive_int(elector_unit, "size", path),
                profile=dict(
                    _require_non_empty_mapping(
                        elector_unit["profile"],
                        f"{path}.profile",
                    )
                ),
            )
        )

    _index_unique(
        parsed,
        key_name="elector_unit_id",
        key_func=lambda elector_unit: elector_unit.elector_unit_id,
        path="elector_units",
    )
    return parsed


def _parse_preference_models(
    raw_preference_models: Any,
    experiment_id: str,
    attribute_specs_by_name: Mapping[str, AttributeSpec],
) -> list[PreferenceModel]:
    preference_models = _require_non_empty_list(
        raw_preference_models,
        "preference_models",
    )
    starter_specs = _starter_specs_by_name()
    parsed: list[PreferenceModel] = []
    for index, raw_preference_model in enumerate(preference_models):
        path = f"preference_models[{index}]"
        preference_model = _require_mapping(raw_preference_model, path)
        _validate_keys(
            preference_model,
            path,
            allowed_keys=PREFERENCE_MODEL_KEYS,
            required_keys=PREFERENCE_MODEL_REQUIRED_KEYS,
        )

        active_attributes = _required_non_empty_string_list(
            preference_model,
            "active_attributes",
            path,
        )
        for attribute_name in active_attributes:
            if (
                attribute_name not in attribute_specs_by_name
                and attribute_name not in starter_specs
            ):
                raise ContractValidationError(
                    f"{path}.active_attributes references unknown attribute "
                    f"'{attribute_name}'."
                )

        attribute_weights = _required_weight_mapping(
            preference_model,
            "attribute_weights",
            path,
        )
        if set(attribute_weights) != set(active_attributes):
            raise ContractValidationError(
                f"{path}.attribute_weights keys must exactly match "
                "active_attributes."
            )

        parsed.append(
            PreferenceModel(
                preference_model_id=_required_string(
                    preference_model,
                    "preference_model_id",
                    path,
                ),
                experiment_id=experiment_id,
                name=_required_string(preference_model, "name", path),
                temperature=_required_positive_number(
                    preference_model,
                    "temperature",
                    path,
                ),
                active_attributes=active_attributes,
                attribute_weights=attribute_weights,
                missing_value_policy=_optional_literal(
                    preference_model,
                    "missing_value_policy",
                    path,
                    VALID_MISSING_VALUE_POLICIES,
                    default="ignore",
                ),
                ranking_method=_optional_literal(
                    preference_model,
                    "ranking_method",
                    path,
                    VALID_RANKING_METHODS,
                    default="deterministic_sort",
                ),
                parameters=dict(
                    _optional_mapping(
                        preference_model,
                        "parameters",
                        path,
                        default={},
                    )
                ),
                description=_optional_string(preference_model, "description", path),
            )
        )

    return parsed


def _include_referenced_starter_specs(
    attribute_specs: list[AttributeSpec],
    preference_models: Sequence[PreferenceModel],
    experiment_id: str,
) -> list[AttributeSpec]:
    specs_by_name = {spec.name: spec for spec in attribute_specs}
    starter_specs = _starter_specs_by_name()
    for preference_model in preference_models:
        for attribute_name in preference_model.active_attributes:
            if attribute_name in specs_by_name:
                continue
            starter_spec = deepcopy(starter_specs[attribute_name])
            starter_spec.experiment_id = experiment_id
            specs_by_name[attribute_name] = starter_spec
    return list(specs_by_name.values())


def _parse_ballot_generation_runs(
    raw_ballot_generation_runs: Any,
    election_by_id: Mapping[str, Election],
    preference_model_by_id: Mapping[str, PreferenceModel],
) -> list[BallotGenerationRun]:
    ballot_generation_runs = _require_non_empty_list(
        raw_ballot_generation_runs,
        "ballot_generation_runs",
    )
    parsed: list[BallotGenerationRun] = []
    for index, raw_run in enumerate(ballot_generation_runs):
        path = f"ballot_generation_runs[{index}]"
        run = _require_mapping(raw_run, path)
        _validate_keys(
            run,
            path,
            allowed_keys=BALLOT_GENERATION_RUN_KEYS,
            required_keys=BALLOT_GENERATION_RUN_REQUIRED_KEYS,
        )

        election_id = _required_string(run, "election_id", path)
        if election_id not in election_by_id:
            raise ContractValidationError(
                f"{path}.election_id references unknown election '{election_id}'."
            )
        preference_model_id = _required_string(run, "preference_model_id", path)
        if preference_model_id not in preference_model_by_id:
            raise ContractValidationError(
                f"{path}.preference_model_id references unknown preference model "
                f"'{preference_model_id}'."
            )

        parsed.append(
            BallotGenerationRun(
                generation_run_id=_required_string(
                    run,
                    "generation_run_id",
                    path,
                ),
                election_id=election_id,
                preference_model_id=preference_model_id,
                random_seed=_optional_int(run, "random_seed", path),
                notes=_optional_string(run, "notes", path),
            )
        )

    _index_unique(
        parsed,
        key_name="generation_run_id",
        key_func=lambda run: run.generation_run_id,
        path="ballot_generation_runs",
    )
    return parsed


def _starter_specs_by_name() -> Mapping[str, AttributeSpec]:
    from Representational_Layer.Attributes.starter_attributes import (
        STARTER_SIX_ATTRIBUTE_SPECS,
    )

    return STARTER_SIX_ATTRIBUTE_SPECS


def _validate_keys(
    obj: Mapping[str, Any],
    path: str,
    *,
    allowed_keys: Sequence[str],
    required_keys: Sequence[str],
) -> None:
    actual_keys = list(obj.keys())
    unexpected_keys = [key for key in actual_keys if key not in allowed_keys]
    if unexpected_keys:
        raise ContractValidationError(
            f"{path} contains unexpected keys: {', '.join(unexpected_keys)}."
        )

    missing_keys = [key for key in required_keys if key not in obj]
    if missing_keys:
        raise ContractValidationError(
            f"{path} is missing mandatory keys: {', '.join(missing_keys)}."
        )

    key_positions = [allowed_keys.index(key) for key in actual_keys]
    if key_positions != sorted(key_positions):
        raise ContractValidationError(
            f"{path} keys must appear in this order: {', '.join(allowed_keys)}."
        )


def _require_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractValidationError(f"{path} must be an object.")
    return value


def _require_non_empty_mapping(value: Any, path: str) -> Mapping[str, Any]:
    mapping = _require_mapping(value, path)
    if not mapping:
        raise ContractValidationError(f"{path} must be a non-empty object.")
    return mapping


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractValidationError(f"{path} must be a list.")
    return value


def _require_non_empty_list(value: Any, path: str) -> list[Any]:
    items = _require_list(value, path)
    if not items:
        raise ContractValidationError(f"{path} must contain at least one item.")
    return items


def _required_string(obj: Mapping[str, Any], field_name: str, path: str) -> str:
    if field_name not in obj:
        raise ContractValidationError(f"{path}.{field_name} is mandatory.")
    value = obj[field_name]
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ContractValidationError(
            f"{path}.{field_name} must be a non-empty string with no edge whitespace."
        )
    return value


def _optional_string(
    obj: Mapping[str, Any],
    field_name: str,
    path: str,
    *,
    default: str | None = None,
) -> str | None:
    if field_name not in obj:
        return default
    value = obj[field_name]
    if value is None:
        return None
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ContractValidationError(
            f"{path}.{field_name} must be null or a non-empty string with no edge whitespace."
        )
    return value


def _required_positive_int(obj: Mapping[str, Any], field_name: str, path: str) -> int:
    value = _required_int(obj, field_name, path)
    if value < 1:
        raise ContractValidationError(f"{path}.{field_name} must be at least 1.")
    return value


def _required_int(obj: Mapping[str, Any], field_name: str, path: str) -> int:
    if field_name not in obj:
        raise ContractValidationError(f"{path}.{field_name} is mandatory.")
    value = obj[field_name]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractValidationError(f"{path}.{field_name} must be an integer.")
    return value


def _optional_int(
    obj: Mapping[str, Any],
    field_name: str,
    path: str,
) -> int | None:
    if field_name not in obj:
        return None
    value = obj[field_name]
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractValidationError(f"{path}.{field_name} must be null or an integer.")
    return value


def _optional_bool(
    obj: Mapping[str, Any],
    field_name: str,
    path: str,
    *,
    default: bool,
) -> bool:
    if field_name not in obj:
        return default
    value = obj[field_name]
    if not isinstance(value, bool):
        raise ContractValidationError(f"{path}.{field_name} must be a boolean.")
    return value


def _required_positive_number(
    obj: Mapping[str, Any],
    field_name: str,
    path: str,
) -> float:
    if field_name not in obj:
        raise ContractValidationError(f"{path}.{field_name} is mandatory.")
    value = _validate_number(obj[field_name], f"{path}.{field_name}")
    if value <= 0.0:
        raise ContractValidationError(f"{path}.{field_name} must be greater than 0.")
    return value


def _optional_number(
    obj: Mapping[str, Any],
    field_name: str,
    path: str,
    *,
    default: float | None = None,
) -> float | None:
    if field_name not in obj:
        return default
    value = obj[field_name]
    if value is None:
        return None
    return _validate_number(value, f"{path}.{field_name}")


def _validate_number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ContractValidationError(f"{path} must be numeric.")
    numeric_value = float(value)
    if not isfinite(numeric_value):
        raise ContractValidationError(f"{path} must be finite.")
    return numeric_value


def _required_literal(
    obj: Mapping[str, Any],
    field_name: str,
    path: str,
    valid_values: set[str],
) -> Any:
    if field_name not in obj:
        raise ContractValidationError(f"{path}.{field_name} is mandatory.")
    value = obj[field_name]
    if value not in valid_values:
        raise ContractValidationError(
            f"{path}.{field_name} must be one of: {', '.join(sorted(valid_values))}."
        )
    return value


def _optional_literal(
    obj: Mapping[str, Any],
    field_name: str,
    path: str,
    valid_values: set[str],
    *,
    default: Any,
) -> Any:
    if field_name not in obj:
        if default is None:
            raise ContractValidationError(f"{path}.{field_name} is mandatory.")
        return default
    value = obj[field_name]
    if value not in valid_values:
        raise ContractValidationError(
            f"{path}.{field_name} must be one of: {', '.join(sorted(valid_values))}."
        )
    return value


def _optional_mapping(
    obj: Mapping[str, Any],
    field_name: str,
    path: str,
    *,
    default: Mapping[str, Any],
) -> Mapping[str, Any]:
    if field_name not in obj:
        return default
    value = obj[field_name]
    if value is None:
        return default
    return _require_mapping(value, f"{path}.{field_name}")


def _required_non_empty_string_list(
    obj: Mapping[str, Any],
    field_name: str,
    path: str,
) -> list[str]:
    if field_name not in obj:
        raise ContractValidationError(f"{path}.{field_name} is mandatory.")
    values = _require_non_empty_list(obj[field_name], f"{path}.{field_name}")
    parsed: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        value_path = f"{path}.{field_name}[{index}]"
        if not isinstance(value, str) or not value or value.strip() != value:
            raise ContractValidationError(
                f"{value_path} must be a non-empty string with no edge whitespace."
            )
        if value in seen:
            raise ContractValidationError(
                f"{path}.{field_name} contains duplicate value '{value}'."
            )
        seen.add(value)
        parsed.append(value)
    return parsed


def _required_weight_mapping(
    obj: Mapping[str, Any],
    field_name: str,
    path: str,
) -> dict[str, float]:
    if field_name not in obj:
        raise ContractValidationError(f"{path}.{field_name} is mandatory.")
    raw_weights = _require_non_empty_mapping(obj[field_name], f"{path}.{field_name}")
    weights: dict[str, float] = {}
    for key, value in raw_weights.items():
        if not isinstance(key, str) or not key or key.strip() != key:
            raise ContractValidationError(
                f"{path}.{field_name} keys must be non-empty strings with no edge whitespace."
            )
        weights[key] = _validate_number(value, f"{path}.{field_name}.{key}")
    return weights


def _index_unique(
    values: Sequence[Any],
    *,
    key_name: str,
    key_func: Any,
    path: str,
) -> dict[str, Any]:
    indexed: dict[str, Any] = {}
    for value in values:
        key = key_func(value)
        if key in indexed:
            raise ContractValidationError(
                f"{path} contains duplicate {key_name} '{key}'."
            )
        indexed[key] = value
    return indexed

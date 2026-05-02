from __future__ import annotations

from typing import Any, TypeAlias

from .models import AttributeSpec, Candidate, ElectorUnit, PreferenceModel

AttributeScores: TypeAlias = dict[str, float]
CandidateScoreEntry: TypeAlias = dict[str, float | AttributeScores]
CandidateScores: TypeAlias = dict[str, CandidateScoreEntry]


def score_candidates_for_elector_unit(
    candidates: list[Candidate],
    elector_unit: ElectorUnit,
    attribute_specs: list[AttributeSpec],
    preference_model: PreferenceModel,
) -> CandidateScores:
    """Score candidates for one elector unit using normalized attribute scores.

    Returns a mapping:
    candidate_id -> {
        "attribute_scores": {attribute_name: score_in_-1_to_1},
        "final_score": weighted_utility_in_-1_to_1,
    }
    """
    spec_by_name = {spec.name: spec for spec in attribute_specs}
    active_attributes = (
        preference_model.active_attributes
        if preference_model.active_attributes
        else list(spec_by_name.keys())
    )

    results: CandidateScores = {}
    for candidate in candidates:
        attribute_scores: AttributeScores = {}
        weighted_sum = 0.0
        sum_abs_weights = 0.0

        for attribute_name in active_attributes:
            spec = spec_by_name.get(attribute_name)
            if spec is None:
                continue

            raw_score = _compute_attribute_score(
                spec=spec,
                elector_profile=elector_unit.profile,
                candidate_profile=candidate.profile,
            )
            score = _resolve_missing_score(raw_score, preference_model.missing_value_policy)
            if score is None:
                continue

            score = _clamp(score)
            attribute_scores[attribute_name] = score

            weight = float(preference_model.attribute_weights.get(attribute_name, 1.0))
            weighted_sum += weight * score
            sum_abs_weights += abs(weight)

        final_score = 0.0 if sum_abs_weights == 0 else _clamp(weighted_sum / sum_abs_weights)
        results[candidate.candidate_id] = {
            "attribute_scores": attribute_scores,
            "final_score": final_score,
        }

    return results


def _compute_attribute_score(
    spec: AttributeSpec,
    elector_profile: dict[str, Any],
    candidate_profile: dict[str, Any],
) -> float | None:
    elector_value = elector_profile.get(spec.name)
    candidate_value = candidate_profile.get(spec.name)

    if spec.comparison_mode == "candidate_effect":
        if candidate_value is None:
            return None
        score = _candidate_effect_score(candidate_value, spec)
        return _apply_score_style(score, spec.score_style)

    if elector_value is None or candidate_value is None:
        return None

    if spec.comparison_mode == "similarity":
        score = _numeric_similarity_score(elector_value, candidate_value, spec)
        return _apply_score_style(score, spec.score_style)

    if spec.comparison_mode == "exact_match":
        score = 1.0 if elector_value == candidate_value else -1.0
        return _apply_score_style(score, spec.score_style)

    if spec.comparison_mode == "set_overlap":
        score = _set_overlap_score(elector_value, candidate_value)
        return _apply_score_style(score, spec.score_style)

    if spec.comparison_mode == "custom":
        score = _custom_score(elector_value, candidate_value, spec)
        if score is None:
            return None
        return _apply_score_style(score, spec.score_style)

    return None


def _numeric_similarity_score(elector_value: Any, candidate_value: Any, spec: AttributeSpec) -> float:
    x = _to_float(elector_value)
    y = _to_float(candidate_value)
    if x is None or y is None:
        return 0.0

    value_min = spec.value_min
    value_max = spec.value_max
    if value_min is None:
        config_min = _to_float(spec.config.get("value_min"))
        value_min = config_min
    if value_max is None:
        config_max = _to_float(spec.config.get("value_max"))
        value_max = config_max

    if value_min is None or value_max is None or value_max <= value_min:
        return 1.0 if x == y else -1.0

    distance = abs(x - y) / (value_max - value_min)
    distance = min(max(distance, 0.0), 1.0)
    return 1.0 - (2.0 * distance)


def _set_overlap_score(elector_value: Any, candidate_value: Any) -> float:
    elector_set = _to_set(elector_value)
    candidate_set = _to_set(candidate_value)
    if elector_set is None or candidate_set is None:
        return 0.0

    union = elector_set | candidate_set
    if not union:
        return 0.0

    jaccard = len(elector_set & candidate_set) / len(union)
    return (2.0 * jaccard) - 1.0


def _candidate_effect_score(candidate_value: Any, spec: AttributeSpec) -> float:
    value = _to_float(candidate_value)
    if value is None:
        return 0.0

    value_min = spec.value_min
    value_max = spec.value_max
    if value_min is None:
        value_min = _to_float(spec.config.get("value_min"))
    if value_max is None:
        value_max = _to_float(spec.config.get("value_max"))

    if value_min is not None and value_max is not None and value_max > value_min:
        normalized = 2.0 * ((value - value_min) / (value_max - value_min)) - 1.0
        return _clamp(normalized)

    # Sensible defaults when explicit normalization bounds are unavailable.
    if 0.0 <= value <= 1.0:
        return (2.0 * value) - 1.0
    return _clamp(value)


def _custom_score(elector_value: Any, candidate_value: Any, spec: AttributeSpec) -> float | None:
    custom_scores = spec.config.get("custom_scores")
    if not isinstance(custom_scores, dict):
        return None

    pair_key = f"{elector_value}|{candidate_value}"
    raw = custom_scores.get(pair_key)
    if raw is None:
        return None
    return _to_float(raw)


def _resolve_missing_score(score: float | None, missing_value_policy: str) -> float | None:
    if score is not None:
        return score
    if missing_value_policy == "ignore":
        return None
    if missing_value_policy == "zero":
        return 0.0
    if missing_value_policy == "error":
        raise ValueError("Missing attribute value encountered during scoring.")
    return None


def _apply_score_style(score: float, score_style: str) -> float:
    if score_style == "bonus_only":
        return max(score, 0.0)
    if score_style == "penalty_only":
        return min(score, 0.0)
    return score


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _to_set(value: Any) -> set[Any] | None:
    if isinstance(value, set):
        return value
    if isinstance(value, frozenset):
        return set(value)
    if isinstance(value, list):
        return set(value)
    if isinstance(value, tuple):
        return set(value)
    return None


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return min(max(value, low), high)

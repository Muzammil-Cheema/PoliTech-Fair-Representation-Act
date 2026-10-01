"""Native GerryChain 1.0.0 multi-member district (MMD) generation helpers."""

from __future__ import annotations

import random
from collections.abc import Hashable, Mapping, Sequence
from functools import partial

from gerrychain import Graph, Partition
from gerrychain.constraints.contiguity import number_of_contiguous_parts
from gerrychain.proposals.multi_member_tree_proposals import epsilon_tree_bipartition_multi_member
from gerrychain.tree import (
    BalanceError,
    PopulationBalanceError,
    ReselectException,
    bipartition_tree,
)
from gerrychain.updaters import Tally

from Global_Utilities import success, warn

# Spanning trees drawn for one split before a seed attempt gives up and the caller retries.
# GerryChain's default (100000) would stall for minutes on a statewide graph before retrying.
SEED_SPLIT_MAX_ATTEMPTS = 1000

_REMAINDER_LABEL = "remaining"
_SEED_ATTEMPT_FAILURES = (PopulationBalanceError, BalanceError, ReselectException, RuntimeError)


def _per_seat_population(graph: Graph, seat_vector: Sequence[int]) -> float:
    """Return the statewide population represented by one seat."""
    total_population = sum(graph.node_data(node)["population"] for node in graph.nodes)
    return total_population / sum(seat_vector)


def build_mmd_seed_assignment(
    graph: Graph,
    seat_vector: Sequence[int],
    population_tolerance: float,
    rng: random.Random,
) -> dict[Hashable, int]:
    """Build one seat-proportional MMD plan by peeling off one district at a time.

    District ``i`` receives ``seat_vector[i]`` seats and targets ``seats * per_seat_population``.
    Each step splits the remaining region into district ``i`` and all remaining districts using
    GerryChain's unequal-target tree split (the same split ``MultiMemberReCom`` uses), so a 5/5/4
    plan is built as ``5 | 9`` and then ``5 | 4``. Every split cuts one spanning-tree edge, so both
    sides are contiguous.

    Args:
        graph: Precinct graph with a ``population`` attribute on every node.
        seat_vector: Seat count per district label; must contain at least 2 districts.
        population_tolerance: Allowed per-seat deviation from the statewide ideal.
        rng: Random source shared with the rest of the run for reproducibility.

    Returns:
        Mapping of original precinct ID to district label ``0..len(seat_vector)-1``.

    Raises:
        ValueError: If ``seat_vector`` has fewer than 2 districts.
        PopulationBalanceError, BalanceError, ReselectException, RuntimeError: If a split cannot
            be found within ``SEED_SPLIT_MAX_ATTEMPTS`` spanning trees.
    """
    seat_vector = [int(seat_count) for seat_count in seat_vector]
    if len(seat_vector) < 2:
        raise ValueError("seat_vector must contain at least 2 districts for MMD seed generation")

    per_seat_population = _per_seat_population(graph, seat_vector)
    split_tree = partial(
        bipartition_tree,
        max_attempts=SEED_SPLIT_MAX_ATTEMPTS,
        warn_attempts=SEED_SPLIT_MAX_ATTEMPTS + 1,
    )

    assignment: dict[Hashable, int] = {}
    remaining_nodes = set(graph.nodes)
    last_district = len(seat_vector) - 1

    for district_id in range(last_district):
        remaining_seats = sum(seat_vector[district_id + 1 :])
        flips = epsilon_tree_bipartition_multi_member(
            graph.subgraph(remaining_nodes),
            (district_id, _REMAINDER_LABEL),
            {
                district_id: seat_vector[district_id] * per_seat_population,
                _REMAINDER_LABEL: remaining_seats * per_seat_population,
            },
            pop_col="population",
            epsilon=population_tolerance,
            bipartition_tree_fn=split_tree,
            rng=rng,
        )
        remaining_nodes = set()
        for node, label in flips.items():
            if label == district_id:
                assignment[node] = district_id
            else:
                remaining_nodes.add(node)

    for node in remaining_nodes:
        assignment[node] = last_district

    return assignment


def validate_mmd_partition(
    partition: Partition,
    members_per_district: Mapping[Hashable, int],
    population_tolerance: float,
) -> tuple[bool, str]:
    """Validate coverage, labels, contiguity, and per-seat population for an MMD partition.

    The partition must carry a ``population`` tally. Every district is checked for contiguity,
    not only districts changed by the last chain step.

    Returns:
        ``(True, "ok")`` when valid, otherwise ``(False, reason)``.
    """
    graph = partition.graph
    if len(partition.assignment) != len(graph.nodes):
        return False, "Not every precinct is assigned to a district"

    observed_labels = set(partition.parts)
    expected_labels = set(members_per_district)
    if observed_labels != expected_labels:
        return (
            False,
            f"District labels {sorted(observed_labels)} do not match seat-count labels "
            f"{sorted(expected_labels)}",
        )

    if number_of_contiguous_parts(partition) != len(observed_labels):
        return False, "At least one district is not contiguous"

    populations = partition["population"]
    per_seat_population = sum(populations.values()) / sum(members_per_district.values())
    for district_id in sorted(observed_labels):
        target_population = members_per_district[district_id] * per_seat_population
        observed_population = populations[district_id]
        deviation = abs(observed_population - target_population) / target_population
        if deviation > population_tolerance:
            return (
                False,
                f"District {district_id} failed population bound: "
                f"target={target_population:,.0f}, observed={observed_population:,.0f}, "
                f"deviation={deviation:.4f}",
            )

    return True, "ok"


def create_mmd_seed_partition(
    graph: Graph,
    seat_vector: Sequence[int],
    population_tolerance: float,
    rng: random.Random,
    max_seed_attempts: int = 10,
) -> Partition:
    """Build and validate the base MMD seed partition, retrying with fresh randomness.

    Each retry continues the same ``rng`` stream, so runs stay reproducible for a fixed seed.

    Returns:
        A validated partition with ``population``, ``votes_dem``, and ``votes_rep`` tallies.

    Raises:
        ValueError: If ``seat_vector`` has fewer than 2 districts.
        RuntimeError: If no valid seed is found within ``max_seed_attempts`` attempts.
    """
    seat_vector = [int(seat_count) for seat_count in seat_vector]
    members_per_district = dict(enumerate(seat_vector))

    for attempt in range(1, max_seed_attempts + 1):
        try:
            assignment = build_mmd_seed_assignment(graph, seat_vector, population_tolerance, rng)
        except _SEED_ATTEMPT_FAILURES as exc:
            warn(f"Seed attempt {attempt}/{max_seed_attempts} failed: {type(exc).__name__}: {exc}")
            continue

        partition = Partition(
            graph,
            assignment=assignment,
            updaters={
                "population": Tally("population"),
                "votes_dem": Tally("votes_dem"),
                "votes_rep": Tally("votes_rep"),
            },
        )
        is_valid, reason = validate_mmd_partition(partition, members_per_district, population_tolerance)
        if is_valid:
            success(f"Built MMD seed plan for seat vector {seat_vector} on attempt {attempt}.")
            return partition

        warn(f"Seed attempt {attempt}/{max_seed_attempts} failed validation: {reason}")

    raise RuntimeError(
        f"Could not build a valid MMD seed for seat_vector={seat_vector} at "
        f"population_tolerance={population_tolerance} after {max_seed_attempts} attempts; "
        "try a higher population_tolerance or max_seed_attempts."
    )

import random

import pytest

pytest.importorskip("gerrychain")

import networkx

from gerrychain import Graph, Partition
from gerrychain.updaters import Tally

from MMD_Generation_Layer.Processor.mmd_generation import (
    build_mmd_seed_assignment,
    create_mmd_seed_partition,
    validate_mmd_partition,
)


def build_grid_graph(rows: int = 16, cols: int = 16, uniform_population: int | None = None) -> Graph:
    """Build a grid graph keyed by string precinct IDs ``P{row}_{col}``.

    Populations vary deterministically between 50 and 150 like real precincts; perfectly uniform
    grids make exact seat-proportional cuts artificially rare at tight tolerances.
    """
    nx_graph = networkx.grid_2d_graph(rows, cols)
    for row, col in nx_graph.nodes:
        population = uniform_population or 50 + (row * 31 + col * 17) % 101
        nx_graph.nodes[(row, col)]["population"] = population
        nx_graph.nodes[(row, col)]["votes_dem"] = 60 if (row + col) % 2 else 40
        nx_graph.nodes[(row, col)]["votes_rep"] = 40 if (row + col) % 2 else 60
    nx_graph = networkx.relabel_nodes(nx_graph, {node: f"P{node[0]}_{node[1]}" for node in nx_graph.nodes})
    return Graph.from_networkx(nx_graph)


def column_partition(graph: Graph, district_for_column: dict[int, int]) -> Partition:
    """Assign every precinct to the district mapped from its column."""
    assignment = {node: district_for_column[int(node.split("_")[1])] for node in graph.nodes}
    return Partition(graph, assignment=assignment, updaters={"population": Tally("population")})


def seat_populations(graph: Graph, assignment: dict, seat_vector: tuple[int, ...]) -> dict[int, float]:
    """Return each district's population per seat."""
    totals: dict[int, int] = {}
    for node, district in assignment.items():
        totals[district] = totals.get(district, 0) + graph.node_data(node)["population"]
    return {district: total / seat_vector[district] for district, total in totals.items()}


@pytest.mark.parametrize("seat_vector", [(3, 2, 2), (5, 5, 4), (2, 2, 2, 2, 1)])
@pytest.mark.parametrize("population_tolerance", [0.1, 0.01])
def test_build_mmd_seed_assignment_is_seat_proportional(seat_vector, population_tolerance) -> None:
    """Every district's population per seat is within tolerance of the statewide per-seat ideal."""
    graph = build_grid_graph()
    per_seat = sum(graph.node_data(node)["population"] for node in graph.nodes) / sum(seat_vector)

    assignment = build_mmd_seed_assignment(graph, seat_vector, population_tolerance, random.Random(3))

    assert set(assignment) == set(graph.nodes)
    assert set(assignment.values()) == set(range(len(seat_vector)))
    for per_seat_population in seat_populations(graph, assignment, seat_vector).values():
        assert abs(per_seat_population / per_seat - 1) <= population_tolerance


def test_build_mmd_seed_assignment_is_reproducible_for_same_rng_seed() -> None:
    """The same RNG seed rebuilds the same plan; a different RNG seed builds a different one."""
    graph = build_grid_graph()

    first = build_mmd_seed_assignment(graph, (3, 2, 2), 0.05, random.Random(7))
    again = build_mmd_seed_assignment(graph, (3, 2, 2), 0.05, random.Random(7))
    other = build_mmd_seed_assignment(graph, (3, 2, 2), 0.05, random.Random(8))

    assert first == again
    assert first != other


def test_build_mmd_seed_assignment_rejects_single_district_seat_vector() -> None:
    """A one-district plan has nothing to split, so it is rejected."""
    with pytest.raises(ValueError, match="at least 2 districts"):
        build_mmd_seed_assignment(build_grid_graph(), (4,), 0.05, random.Random(1))


def test_create_mmd_seed_partition_returns_validated_partition_with_tallies() -> None:
    """The returned seed partition passes validation and carries population and vote tallies."""
    graph = build_grid_graph()
    seat_vector = (5, 5, 4)

    partition = create_mmd_seed_partition(graph, seat_vector, 0.02, random.Random(5), max_seed_attempts=3)

    members = dict(enumerate(seat_vector))
    assert validate_mmd_partition(partition, members, 0.02) == (True, "ok")
    assert sum(partition["population"].values()) == sum(graph.node_data(node)["population"] for node in graph.nodes)
    assert set(partition["votes_dem"]) == set(partition["votes_rep"]) == set(members)


def test_create_mmd_seed_partition_raises_clear_error_after_attempt_budget() -> None:
    """An impossible plan exhausts the retry budget and names the seat vector and tolerance."""
    graph = build_grid_graph(rows=8, cols=8)
    graph.node_data("P0_0")["population"] = 1_000_000

    with pytest.raises(RuntimeError, match=r"seat_vector=\[3, 2, 2\].*population_tolerance=0.01.*2 attempts"):
        create_mmd_seed_partition(graph, (3, 2, 2), 0.01, random.Random(1), max_seed_attempts=2)


def test_validate_mmd_partition_accepts_balanced_contiguous_plan() -> None:
    """Two contiguous halves with one seat each are valid."""
    graph = build_grid_graph(rows=4, cols=4, uniform_population=100)
    partition = column_partition(graph, {0: 0, 1: 0, 2: 1, 3: 1})

    assert validate_mmd_partition(partition, {0: 1, 1: 1}, 0.05) == (True, "ok")


def test_validate_mmd_partition_rejects_non_contiguous_district() -> None:
    """Districts made of alternating columns are not contiguous."""
    graph = build_grid_graph(rows=4, cols=4, uniform_population=100)
    partition = column_partition(graph, {0: 0, 1: 1, 2: 0, 3: 1})

    is_valid, reason = validate_mmd_partition(partition, {0: 1, 1: 1}, 0.05)

    assert not is_valid
    assert "contiguous" in reason


def test_validate_mmd_partition_rejects_labels_that_do_not_match_seat_counts() -> None:
    """District labels must match the labels that carry seat counts."""
    graph = build_grid_graph(rows=4, cols=4, uniform_population=100)
    partition = column_partition(graph, {0: 0, 1: 0, 2: 2, 3: 2})

    is_valid, reason = validate_mmd_partition(partition, {0: 1, 1: 1}, 0.05)

    assert not is_valid
    assert "labels" in reason


def test_validate_mmd_partition_rejects_population_outside_tolerance() -> None:
    """A three-column district against a one-column district breaks the per-seat bound."""
    graph = build_grid_graph(rows=4, cols=4, uniform_population=100)
    partition = column_partition(graph, {0: 0, 1: 0, 2: 0, 3: 1})

    is_valid, reason = validate_mmd_partition(partition, {0: 1, 1: 1}, 0.05)

    assert not is_valid
    assert "District 0 failed population bound" in reason

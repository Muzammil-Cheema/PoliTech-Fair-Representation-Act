import pytest

pytest.importorskip("gerrychain")

import networkx

from gerrychain import Graph

from MMD_Generation_Layer.Processor.generation_logic import generate_baseline_ensemble


def build_grid_graph(width: int = 8, height: int = 8) -> Graph:
    """Build a small grid graph keyed by string precinct IDs, like real shapefile data."""
    nx_graph = networkx.convert_node_labels_to_integers(networkx.grid_graph(dim=[width, height]))
    for node in nx_graph.nodes:
        nx_graph.nodes[node]["population"] = 100
        nx_graph.nodes[node]["votes_dem"] = 60 if node % 2 else 40
        nx_graph.nodes[node]["votes_rep"] = 40 if node % 2 else 60
    nx_graph = networkx.relabel_nodes(nx_graph, {node: f"P{node}" for node in nx_graph.nodes})
    return Graph.from_networkx(nx_graph)


def test_generate_baseline_ensemble_returns_requested_smd_plans() -> None:
    """The SMD ReCom path yields one result per step, keyed by the original precinct IDs."""
    graph = build_grid_graph()

    ensemble = generate_baseline_ensemble(
        graph, num_plans=5, num_districts=4, seed=11, population_tolerance=0.1
    )

    assert [plan["results"]["plan_id"] for plan in ensemble] == [1, 2, 3, 4, 5]
    for plan in ensemble:
        assert set(plan["assignment"]) == set(graph.nodes)
        assert set(plan["assignment"].values()) == {0, 1, 2, 3}
        assert plan["results"]["dem_seats"] + plan["results"]["rep_seats"] == 4


def test_generate_baseline_ensemble_is_reproducible_for_same_seed() -> None:
    """The same seed produces the same SMD ensemble; a different seed produces a different one."""
    graph = build_grid_graph()

    first = generate_baseline_ensemble(graph, num_plans=4, num_districts=4, seed=11, population_tolerance=0.1)
    again = generate_baseline_ensemble(graph, num_plans=4, num_districts=4, seed=11, population_tolerance=0.1)
    other = generate_baseline_ensemble(graph, num_plans=4, num_districts=4, seed=12, population_tolerance=0.1)

    assert [plan["assignment"] for plan in first] == [plan["assignment"] for plan in again]
    assert [plan["assignment"] for plan in first] != [plan["assignment"] for plan in other]

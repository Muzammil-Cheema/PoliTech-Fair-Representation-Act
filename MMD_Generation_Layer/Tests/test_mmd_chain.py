import json
from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("gerrychain")

import networkx

from gerrychain import Graph, Partition
from gerrychain.updaters import Tally

from MMD_Generation_Layer.Processor.generation_logic import generate_ensemble_for_run
from MMD_Generation_Layer.Processor.mmd_generation import generate_mmd_ensemble, validate_mmd_partition
from MMD_Generation_Layer.Processor.runtime_setup import VALID_RECOM_VARIANTS, RunConfig, default_run_config


def build_grid_graph(rows: int = 16, cols: int = 16) -> Graph:
    """Build a grid graph keyed by string precinct IDs with varied populations and votes."""
    nx_graph = networkx.grid_2d_graph(rows, cols)
    for row, col in nx_graph.nodes:
        nx_graph.nodes[(row, col)]["population"] = 50 + (row * 31 + col * 17) % 101
        nx_graph.nodes[(row, col)]["votes_dem"] = 40 + (row * 7 + col * 3) % 41
        nx_graph.nodes[(row, col)]["votes_rep"] = 40 + (row * 5 + col * 11) % 41
    nx_graph = networkx.relabel_nodes(nx_graph, {node: f"P{node[0]}_{node[1]}" for node in nx_graph.nodes})
    return Graph.from_networkx(nx_graph)


def mmd_run_config(**overrides) -> RunConfig:
    """Return an MMD RunConfig for the grid graph with optional overrides."""
    values = {
        "generation_mode": "MMD",
        "num_plans": 6,
        "num_districts": 7,
        "seed": 4242,
        "seat_vector": (3, 2, 2),
        "population_tolerance": 0.05,
    }
    return replace(default_run_config(), **{**values, **overrides})


def plan_partition(graph: Graph, plan: dict) -> Partition:
    """Rebuild a partition from a saved plan assignment."""
    return Partition(graph, assignment=plan["assignment"], updaters={"population": Tally("population")})


@pytest.fixture(scope="module")
def graph() -> Graph:
    return build_grid_graph()


def test_generate_mmd_ensemble_saves_requested_valid_plans(graph: Graph) -> None:
    """Exactly num_plans plans are saved, each valid and keyed by original precinct IDs."""
    run_config = mmd_run_config()
    members = dict(enumerate(run_config.seat_vector))

    ensemble, _ = generate_mmd_ensemble(graph, run_config)

    assert [plan["results"]["plan_id"] for plan in ensemble] == [1, 2, 3, 4, 5, 6]
    for plan in ensemble:
        assert set(plan["assignment"]) == set(graph.nodes)
        assert validate_mmd_partition(plan_partition(graph, plan), members, 0.05) == (True, "ok")


def test_generate_mmd_ensemble_applies_burn_in_and_step_interval(graph: Graph) -> None:
    """Saved plans come from chain steps burn_in + k * step_interval; the seed (step 0) is never saved."""
    run_config = mmd_run_config(num_plans=4, burn_in_steps=5, step_interval=3)

    ensemble, _ = generate_mmd_ensemble(graph, run_config)

    assert [plan["results"]["chain_step"] for plan in ensemble] == [8, 11, 14, 17]


def test_generate_mmd_ensemble_defaults_save_every_step_after_seed(graph: Graph) -> None:
    """With burn_in_steps=0 and step_interval=1, saved plans are chain steps 1..num_plans."""
    ensemble, _ = generate_mmd_ensemble(graph, mmd_run_config(num_plans=3))

    assert [plan["results"]["chain_step"] for plan in ensemble] == [1, 2, 3]


def test_generate_mmd_ensemble_keeps_seat_counts_on_labels(graph: Graph) -> None:
    """Each district label keeps its seat count and summaries add up to the plan totals."""
    run_config = mmd_run_config()
    members = dict(enumerate(run_config.seat_vector))
    total_population = sum(graph.node_data(node)["population"] for node in graph.nodes)

    ensemble, _ = generate_mmd_ensemble(graph, run_config)

    for plan in ensemble:
        summaries = plan["district_summaries"]
        assert {summary["district_id"]: summary["seat_count"] for summary in summaries} == members
        assert sum(summary["population"] for summary in summaries) == total_population
        results = plan["results"]
        assert results["dem_seats"] + results["rep_seats"] == results["total_seats"] == 7
        assert results["dem_seat_share"] == results["dem_seats"] / 7
        expected_dem_seats = sum(
            summary["seat_count"] for summary in summaries if summary["votes_dem"] > summary["votes_rep"]
        )
        assert results["dem_seats"] == expected_dem_seats


def test_generate_mmd_ensemble_plan_record_shape(graph: Graph) -> None:
    """Plan records keep the shape the CSV, plots, and dashboard expect."""
    ensemble, _ = generate_mmd_ensemble(graph, mmd_run_config(num_plans=1))

    plan = ensemble[0]
    assert set(plan) == {"results", "assignment", "district_summaries"}
    assert set(plan["results"]) == {
        "plan_id",
        "dem_seats",
        "rep_seats",
        "dem_seat_share",
        "total_seats",
        "chain_step",
    }
    assert set(plan["district_summaries"][0]) == {
        "district_id",
        "seat_count",
        "population",
        "votes_dem",
        "votes_rep",
    }


def test_generate_mmd_ensemble_returns_seed_record(graph: Graph) -> None:
    """The seed record holds the seat vector, seats per label, and the seed's precinct assignment."""
    _, seed_record = generate_mmd_ensemble(graph, mmd_run_config(num_plans=1))

    assert seed_record["seat_vector"] == [3, 2, 2]
    assert seed_record["members_per_district"] == {0: 3, 1: 2, 2: 2}
    assert set(seed_record["assignment"]) == set(graph.nodes)
    assert set(seed_record["assignment"].values()) == {0, 1, 2}


def test_generate_mmd_ensemble_is_reproducible_for_same_seed(graph: Graph) -> None:
    """The same config reproduces the ensemble; a different seed changes it."""
    first, _ = generate_mmd_ensemble(graph, mmd_run_config(num_plans=3))
    again, _ = generate_mmd_ensemble(graph, mmd_run_config(num_plans=3))
    other, _ = generate_mmd_ensemble(graph, mmd_run_config(num_plans=3, seed=4243))

    assert [plan["assignment"] for plan in first] == [plan["assignment"] for plan in again]
    assert [plan["assignment"] for plan in first] != [plan["assignment"] for plan in other]


@pytest.mark.parametrize("variant", VALID_RECOM_VARIANTS)
def test_generate_mmd_ensemble_runs_every_recom_variant(graph: Graph, variant: str) -> None:
    """All four MultiMemberReCom variants produce valid plans."""
    run_config = mmd_run_config(num_plans=3, recom_variant=variant)
    members = dict(enumerate(run_config.seat_vector))

    ensemble, _ = generate_mmd_ensemble(graph, run_config)

    assert len(ensemble) == 3
    for plan in ensemble:
        assert validate_mmd_partition(plan_partition(graph, plan), members, 0.05) == (True, "ok")


def test_generate_ensemble_for_run_uses_native_mmd_and_saves_seed_plan(graph: Graph, tmp_path: Path) -> None:
    """MMD runs use the native chain and write the seed plan only when save_seed_plan is set."""
    seed_plan_path = tmp_path / "seed_plan.json"

    ensemble = generate_ensemble_for_run(
        graph, mmd_run_config(num_plans=2, save_seed_plan=True, seed_plan_path=seed_plan_path)
    )

    assert [plan["results"]["chain_step"] for plan in ensemble] == [1, 2]
    saved = json.loads(seed_plan_path.read_text())
    assert saved["seat_vector"] == [3, 2, 2]
    assert saved["members_per_district"] == {"0": 3, "1": 2, "2": 2}
    assert set(saved["assignment"]) == set(graph.nodes)


def test_generate_ensemble_for_run_skips_seed_plan_by_default(graph: Graph, tmp_path: Path) -> None:
    """No seed plan file is written when save_seed_plan is false."""
    seed_plan_path = tmp_path / "seed_plan.json"

    generate_ensemble_for_run(graph, mmd_run_config(num_plans=1, seed_plan_path=seed_plan_path))

    assert not seed_plan_path.exists()

"""Graph loading, SMD generation, and SMD/MMD run dispatch."""

from __future__ import annotations

import random
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial

import geopandas as gpd
import pandas as pd
from gerrychain import Graph, MarkovChain, Partition
from gerrychain.accept import always_accept
from gerrychain.constraints import contiguous, within_percent_of_ideal_population
from gerrychain.partition import recursive_tree_part
from gerrychain.proposals import recom
from gerrychain.updaters import Tally

from Global_Utilities import info, success, warn
from MMD_Generation_Layer import config as project_config
from MMD_Generation_Layer.Processor.output_artifacts import save_seed_plan
from MMD_Generation_Layer.Processor.runtime_setup import RunConfig

# MMD-only settings and their defaults; SMD runs log when any of these were changed.
MMD_ONLY_SETTING_DEFAULTS = {
    "recom_variant": project_config.RECOM_VARIANT,
    "burn_in_steps": project_config.BURN_IN_STEPS,
    "step_interval": project_config.STEP_INTERVAL,
    "max_seed_attempts": project_config.MAX_SEED_ATTEMPTS,
    "save_seed_plan": project_config.SAVE_SEED_PLAN,
}


@contextmanager
def log_captured_warnings(max_message_length: int = 300) -> Iterator[None]:
    """Route Python warnings raised in the block (e.g. GerryChain's) through ``warn(...)``.

    Each distinct warning is logged once, truncated to ``max_message_length`` characters.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        yield

    logged = set()
    for warning in caught:
        message = f"{warning.category.__name__}: {warning.message}"
        if message in logged:
            continue
        logged.add(message)
        if len(message) > max_message_length:
            message = message[:max_message_length] + "..."
        warn(message)


def load_and_build_graph(
    shape_path=project_config.shape_path,
    id_col=project_config.ID_COLUMN,
    geom_col=project_config.GEOM_COLUMN,
    pop_col=project_config.POP_COLUMN,
    dem_col=project_config.DEM_COLUMN,
    rep_col=project_config.REP_COLUMN,
) -> tuple[Graph, gpd.GeoDataFrame]:
    """Load precinct geodata, validate columns, and build a GerryChain graph."""
    info("Loading shapefile for MMD generation.")
    gdf = gpd.read_file(shape_path)
    success(f"Loaded {len(gdf)} rows.")

    if geom_col in gdf.columns:
        gdf = gdf.set_geometry(geom_col)

    required_cols = {
        id_col,
        pop_col,
        dem_col,
        rep_col,
        gdf.geometry.name,
    }
    missing = required_cols - set(gdf.columns)
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    gdf = gdf[list(required_cols)].copy()
    gdf[id_col] = gdf[id_col].astype(str).str.strip()

    if not gdf[id_col].is_unique:
        raise ValueError(f"{id_col} is not unique. Cannot use as node ID.")

    gdf[pop_col] = pd.to_numeric(gdf[pop_col], errors="coerce").fillna(0).astype(int)
    gdf[dem_col] = pd.to_numeric(gdf[dem_col], errors="coerce").fillna(0).astype(int)
    gdf[rep_col] = pd.to_numeric(gdf[rep_col], errors="coerce").fillna(0).astype(int)

    invalid = ~gdf.geometry.is_valid
    if invalid.any():
        warn(f"Repairing {invalid.sum()} invalid geometries.")
        gdf.loc[invalid, "geometry"] = gdf.loc[invalid, "geometry"].buffer(0)

    gdf = gdf.set_index(id_col, drop=False)

    info("Building GerryChain dual graph.")
    with log_captured_warnings():
        graph = Graph.from_geodataframe(gdf)

    for node in graph.nodes:
        row = gdf.loc[node]
        node_data = graph.node_data(node)
        node_data["population"] = int(row[pop_col])
        node_data["votes_dem"] = int(row[dem_col])
        node_data["votes_rep"] = int(row[rep_col])

    degrees = [graph.degree(node) for node in graph.nodes]
    isolated_count = sum(1 for degree in degrees if degree == 0)
    median_degree = sorted(degrees)[len(degrees) // 2]

    success(f"Graph built ({len(graph.nodes)} nodes, {len(graph.edges)} edges).")
    info(f"Isolated nodes: {isolated_count}")
    info(f"Degree min/median/max: {min(degrees)}/{median_degree}/{max(degrees)}")
    return graph, gdf


def assignment_by_original_node_id(partition: Partition) -> dict:
    """Map a partition's assignment back to the graph's original node IDs.

    GerryChain 1.0.0 keys ``partition.assignment`` by internal integer node IDs, so plan outputs
    must be translated back to precinct IDs before they are saved or compared with the source graph.
    """
    graph = partition.graph
    return {
        graph.original_nx_node_id_for_internal_node_id(node_id): district_id
        for node_id, district_id in partition.assignment.items()
    }


def create_initial_partition(
    graph: Graph,
    num_districts: int = project_config.NUM_DISTRICTS,
    seed: int = project_config.SEED,
    population_tolerance: float = 0.05,
    rng: random.Random | None = None,
) -> Partition:
    """Create an initial contiguous equal-population partition."""
    rng = rng or random.Random(seed)

    total_population = sum(graph.node_data(node)["population"] for node in graph.nodes)
    ideal_population = total_population / num_districts

    info(f"Creating initial partition ({num_districts} districts).")
    info(f"Ideal population per district: {ideal_population:,.0f}")
    info(f"Population tolerance: {population_tolerance * 100:.1f}%")

    assignment = recursive_tree_part(
        graph,
        range(num_districts),
        ideal_population,
        "population",
        population_tolerance,
        1,
        rng=rng,
    )

    partition = Partition(
        graph,
        assignment=assignment,
        updaters={
            "population": Tally("population"),
            "votes_dem": Tally("votes_dem"),
            "votes_rep": Tally("votes_rep"),
        },
    )
    success(f"Initial partition created with {len(partition.parts)} districts.")
    return partition


def generate_baseline_ensemble(
    graph: Graph,
    num_plans: int = project_config.NUM_PLANS,
    num_districts: int = project_config.NUM_DISTRICTS,
    seed: int = project_config.SEED,
    population_tolerance: float = 0.05,
) -> list[dict]:
    """Generate an equal-population SMD ensemble using GerryChain ReCom."""
    info(f"Setting up ReCom chain to generate {num_plans} plans.")
    rng = random.Random(seed)

    initial_partition = create_initial_partition(
        graph,
        num_districts=num_districts,
        seed=seed,
        population_tolerance=population_tolerance,
        rng=rng,
    )
    population_constraint = within_percent_of_ideal_population(
        initial_partition,
        population_tolerance,
    )

    total_population = sum(graph.node_data(node)["population"] for node in graph.nodes)
    ideal_population = total_population / num_districts
    # GerryChain 0.3.2 recom chose a random cut edge; 1.0.0 defaults to district pairs.
    proposal = partial(
        recom,
        pop_col="population",
        pop_target=ideal_population,
        epsilon=population_tolerance,
        node_repeats=2,
        pair_selection="cut_edges",
    )

    chain = MarkovChain(
        proposal_fn=proposal,
        constraints=[contiguous, population_constraint],
        acceptance_fn=always_accept,
        initial_partition=initial_partition,
        total_steps=num_plans,
        rng=rng,
    )

    ensemble = []
    for plan_counter, partition in enumerate(chain, start=1):
        dem_seats = 0
        rep_seats = 0

        for district in partition.parts:
            district_dem = partition["votes_dem"][district]
            district_rep = partition["votes_rep"][district]
            if district_dem > district_rep:
                dem_seats += 1
            else:
                rep_seats += 1

        ensemble.append(
            {
                "results": {
                    "plan_id": plan_counter,
                    "dem_seats": dem_seats,
                    "rep_seats": rep_seats,
                    "dem_seat_share": dem_seats / num_districts,
                },
                "assignment": assignment_by_original_node_id(partition),
            }
        )

        if plan_counter % 5 == 0 or plan_counter == num_plans:
            info(f"Generated {plan_counter}/{num_plans} plans.")

    success(f"Generated {num_plans} random district plans.")
    return ensemble


def runtime_mode_settings(run_config: RunConfig) -> dict[str, int | str]:
    """Validate the generation mode and return the plan and district counts for the run."""
    mode = run_config.generation_mode.strip().upper()
    if mode not in {"SMD", "MMD"}:
        raise ValueError("generation_mode must be either 'SMD' or 'MMD'")

    if mode == "MMD" and not run_config.seat_vector:
        raise ValueError("seat_vector must be non-empty when generation_mode='MMD'")

    return {
        "mode": mode,
        "num_districts": run_config.num_districts,
        "num_plans": run_config.num_plans,
    }


def generate_ensemble_for_run(graph: Graph, run_config: RunConfig) -> list[dict]:
    """Generate the final ensemble for the configured SMD or MMD mode.

    MMD runs use the native GerryChain multi-member chain from an auto-built seed plan; SMD runs
    use the equal-population ReCom baseline.
    """
    mode_settings = runtime_mode_settings(run_config)
    info(f"Mode: {mode_settings['mode']}")
    info(f"Shape path: {run_config.shape_path}")

    if mode_settings["mode"] == "MMD":
        from MMD_Generation_Layer.Processor.mmd_generation import generate_mmd_ensemble

        ensemble, seed_record = generate_mmd_ensemble(graph, run_config)
        if run_config.save_seed_plan:
            save_seed_plan(seed_record, run_config.seed_plan_path)
        return ensemble

    info(f"Districts: {mode_settings['num_districts']}")
    info(f"Plans: {mode_settings['num_plans']}")

    changed_mmd_settings = [
        key for key, default in MMD_ONLY_SETTING_DEFAULTS.items() if getattr(run_config, key) != default
    ]
    if changed_mmd_settings:
        info(
            f"{', '.join(changed_mmd_settings)} only apply when generation_mode='MMD' "
            "and are ignored for this SMD run."
        )

    return generate_baseline_ensemble(
        graph,
        num_plans=int(mode_settings["num_plans"]),
        num_districts=int(mode_settings["num_districts"]),
        seed=run_config.seed,
        population_tolerance=run_config.population_tolerance,
    )

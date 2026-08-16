"""District generation logic for SMD and experimental MMD workflows."""

from __future__ import annotations

import random
from collections import defaultdict, deque
from functools import partial

import geopandas as gpd
import pandas as pd
from gerrychain import Graph, MarkovChain, Partition
from gerrychain.accept import always_accept
from gerrychain.constraints import contiguous, within_percent_of_ideal_population
from gerrychain.proposals import recom
from gerrychain.tree import recursive_tree_part
from gerrychain.updaters import Tally

from Global_Utilities import info, success, warn
from MMD_Generation_Layer import config as project_config
from MMD_Generation_Layer.Processor.output_artifacts import save_intermediate_smd_plans
from MMD_Generation_Layer.Processor.runtime_setup import RunConfig


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
    graph = Graph.from_geodataframe(gdf)

    for node in graph.nodes():
        row = gdf.loc[node]
        graph.nodes[node]["population"] = row[pop_col]
        graph.nodes[node]["votes_dem"] = row[dem_col]
        graph.nodes[node]["votes_rep"] = row[rep_col]

    degrees = [graph.degree(node) for node in graph.nodes()]
    isolated_count = sum(1 for degree in degrees if degree == 0)
    median_degree = sorted(degrees)[len(degrees) // 2]

    success(f"Graph built ({len(graph.nodes())} nodes, {len(graph.edges())} edges).")
    info(f"Isolated nodes: {isolated_count}")
    info(f"Degree min/median/max: {min(degrees)}/{median_degree}/{max(degrees)}")
    return graph, gdf


def create_initial_partition(
    graph: Graph,
    num_districts: int = project_config.NUM_DISTRICTS,
    seed: int = project_config.SEED,
    population_tolerance: float = 0.05,
) -> Partition:
    """Create an initial contiguous equal-population partition."""
    random.seed(seed)

    total_population = sum(graph.nodes[node]["population"] for node in graph.nodes())
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

    initial_partition = create_initial_partition(
        graph,
        num_districts=num_districts,
        seed=seed,
        population_tolerance=population_tolerance,
    )
    population_constraint = within_percent_of_ideal_population(
        initial_partition,
        population_tolerance,
    )

    total_population = sum(graph.nodes[node]["population"] for node in graph.nodes())
    ideal_population = total_population / num_districts
    proposal = partial(
        recom,
        pop_col="population",
        pop_target=ideal_population,
        epsilon=population_tolerance,
        node_repeats=2,
    )

    chain = MarkovChain(
        proposal=proposal,
        constraints=[contiguous, population_constraint],
        accept=always_accept,
        initial_state=initial_partition,
        total_steps=num_plans,
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
                "assignment": dict(partition.assignment),
            }
        )

        if plan_counter % 5 == 0 or plan_counter == num_plans:
            info(f"Generated {plan_counter}/{num_plans} plans.")

    success(f"Generated {num_plans} random district plans.")
    return ensemble


def _build_smd_unit_stats(smd_assignment: dict, graph: Graph) -> dict[int, dict]:
    """Aggregate node-level graph attributes into per-SMD units."""
    units: dict[int, dict] = {}

    for node_id, district_id in smd_assignment.items():
        smd_id = int(district_id)
        if smd_id not in units:
            units[smd_id] = {
                "nodes": set(),
                "population": 0,
                "votes_dem": 0,
                "votes_rep": 0,
            }

        units[smd_id]["nodes"].add(node_id)
        units[smd_id]["population"] += int(graph.nodes[node_id]["population"])
        units[smd_id]["votes_dem"] += int(graph.nodes[node_id]["votes_dem"])
        units[smd_id]["votes_rep"] += int(graph.nodes[node_id]["votes_rep"])

    return units


def _build_smd_adjacency(smd_assignment: dict, graph: Graph) -> dict[int, set[int]]:
    """Build an adjacency graph where each node is an SMD ID."""
    smd_adjacency: dict[int, set[int]] = defaultdict(set)

    for district_id in smd_assignment.values():
        smd_adjacency[int(district_id)]

    for node_u, node_v in graph.edges():
        smd_u = int(smd_assignment[node_u])
        smd_v = int(smd_assignment[node_v])
        if smd_u == smd_v:
            continue

        smd_adjacency[smd_u].add(smd_v)
        smd_adjacency[smd_v].add(smd_u)

    return dict(smd_adjacency)


def _find_bfs_merge_candidate(
    start_smd: int,
    seat_count: int,
    available_smd_ids: set[int],
    smd_adjacency: dict[int, set[int]],
    smd_population: dict[int, int],
    per_seat_population: float,
    population_tolerance: float,
    max_states: int = 20000,
) -> tuple[set[int], int] | None:
    """Find a contiguous SMD merge matching a seat-weighted population target."""
    target_population = seat_count * per_seat_population
    lower_bound = target_population * (1 - population_tolerance)
    upper_bound = target_population * (1 + population_tolerance)

    start_state = frozenset([start_smd])
    state_population = {start_state: smd_population[start_smd]}
    queue = deque([start_state])
    visited = {start_state}

    best_state = start_state
    best_deviation = abs(state_population[start_state] - target_population) / target_population

    explored = 0
    while queue and explored < max_states:
        current_state = queue.popleft()
        current_population = state_population[current_state]
        explored += 1

        current_deviation = abs(current_population - target_population) / target_population
        if current_deviation < best_deviation:
            best_state = current_state
            best_deviation = current_deviation

        if lower_bound <= current_population <= upper_bound:
            return set(current_state), current_population

        if current_population >= upper_bound:
            continue

        frontier = set()
        for smd_id in current_state:
            frontier.update(smd_adjacency.get(smd_id, set()))

        for neighbor_smd in sorted(frontier):
            if neighbor_smd not in available_smd_ids or neighbor_smd in current_state:
                continue

            new_state = frozenset(set(current_state) | {neighbor_smd})
            if new_state in visited:
                continue

            new_population = current_population + smd_population[neighbor_smd]
            visited.add(new_state)
            state_population[new_state] = new_population
            queue.append(new_state)

    best_population = state_population[best_state]
    best_deviation = abs(best_population - target_population) / target_population
    if best_deviation <= population_tolerance:
        return set(best_state), best_population

    return None


def _validate_mmd_plan(
    mmd_plan: dict,
    graph: Graph,
    seat_vector: tuple[int, ...] | list[int],
    population_tolerance: float,
) -> tuple[bool, str]:
    """Validate full-node coverage, seat accounting, and population bounds."""
    expected_nodes = set(graph.nodes())
    assigned_nodes = set(mmd_plan["assignment"].keys())
    if assigned_nodes != expected_nodes:
        return False, "Not all nodes are mapped in final MMD assignment"

    expected_sorted = sorted(int(seat_count) for seat_count in seat_vector)
    observed_sorted = sorted(int(d["seat_count"]) for d in mmd_plan["district_summaries"])
    if observed_sorted != expected_sorted:
        return False, "MMD seat vector does not match requested seat vector"

    total_population = sum(int(graph.nodes[node]["population"]) for node in graph.nodes())
    total_seats = sum(expected_sorted)
    per_seat_population = total_population / total_seats

    for district_summary in mmd_plan["district_summaries"]:
        target_population = district_summary["seat_count"] * per_seat_population
        observed_population = district_summary["population"]
        deviation = abs(observed_population - target_population) / target_population
        if deviation > population_tolerance:
            return (
                False,
                (
                    f"District {district_summary['district_id']} failed population bound: "
                    f"target={target_population:,.0f}, observed={observed_population:,.0f}, "
                    f"deviation={deviation:.4f}"
                ),
            )

    return True, "ok"


def _build_single_mmd_plan(
    smd_assignment: dict,
    graph: Graph,
    seat_vector: tuple[int, ...] | list[int],
    population_tolerance: float,
    seed: int,
) -> dict | None:
    """Build a single MMD plan from one temporary-SMD assignment."""
    seat_vector = [int(seat_count) for seat_count in seat_vector]
    smd_units = _build_smd_unit_stats(smd_assignment, graph)
    smd_adjacency = _build_smd_adjacency(smd_assignment, graph)

    total_population = sum(unit["population"] for unit in smd_units.values())
    total_seats = sum(seat_vector)
    per_seat_population = total_population / total_seats
    smd_population = {smd_id: unit["population"] for smd_id, unit in smd_units.items()}

    available_smd_ids = set(smd_units.keys())
    remaining_seat_targets = list(seat_vector)
    rng = random.Random(seed)

    smd_to_mmd = {}
    district_summaries = []
    next_mmd_id = 0

    while remaining_seat_targets:
        if not available_smd_ids:
            return None

        random_draw = rng.randint(0, 2**31 - 1)
        seat_index = random_draw % len(remaining_seat_targets)
        seat_count = remaining_seat_targets.pop(seat_index)

        candidate_start_pool = sorted(available_smd_ids)
        if not candidate_start_pool:
            return None

        start_smd = candidate_start_pool[random_draw % len(candidate_start_pool)]
        candidate_merge = _find_bfs_merge_candidate(
            start_smd=start_smd,
            seat_count=seat_count,
            available_smd_ids=available_smd_ids,
            smd_adjacency=smd_adjacency,
            smd_population=smd_population,
            per_seat_population=per_seat_population,
            population_tolerance=population_tolerance,
        )

        if candidate_merge is None:
            shuffled_starts = candidate_start_pool[:]
            rng.shuffle(shuffled_starts)

            for alternate_start in shuffled_starts:
                candidate_merge = _find_bfs_merge_candidate(
                    start_smd=alternate_start,
                    seat_count=seat_count,
                    available_smd_ids=available_smd_ids,
                    smd_adjacency=smd_adjacency,
                    smd_population=smd_population,
                    per_seat_population=per_seat_population,
                    population_tolerance=population_tolerance,
                )
                if candidate_merge is not None:
                    break

        if candidate_merge is None:
            return None

        merged_smd_ids, merged_population = candidate_merge
        merged_smd_ids = set(merged_smd_ids)

        dem_votes = sum(smd_units[smd_id]["votes_dem"] for smd_id in merged_smd_ids)
        rep_votes = sum(smd_units[smd_id]["votes_rep"] for smd_id in merged_smd_ids)

        for smd_id in merged_smd_ids:
            smd_to_mmd[smd_id] = next_mmd_id

        district_summaries.append(
            {
                "district_id": next_mmd_id,
                "seat_count": seat_count,
                "smd_ids": sorted(merged_smd_ids),
                "population": int(merged_population),
                "votes_dem": int(dem_votes),
                "votes_rep": int(rep_votes),
            }
        )

        available_smd_ids -= merged_smd_ids
        next_mmd_id += 1

    if available_smd_ids:
        return None

    precinct_assignment = {}
    for node_id, smd_id_raw in smd_assignment.items():
        smd_id = int(smd_id_raw)
        if smd_id not in smd_to_mmd:
            return None
        precinct_assignment[node_id] = smd_to_mmd[smd_id]

    dem_seats = 0
    for district_summary in district_summaries:
        if district_summary["votes_dem"] > district_summary["votes_rep"]:
            dem_seats += district_summary["seat_count"]

    rep_seats = total_seats - dem_seats
    return {
        "results": {
            "plan_id": -1,
            "dem_seats": int(dem_seats),
            "rep_seats": int(rep_seats),
            "dem_seat_share": float(dem_seats / total_seats),
            "total_seats": int(total_seats),
        },
        "assignment": precinct_assignment,
        "district_summaries": district_summaries,
    }


def _mmd_plan_signature(mmd_plan: dict) -> tuple:
    """Build a deterministic signature for deduplicating MMD plans."""
    tuples = []
    for district_summary in mmd_plan["district_summaries"]:
        tuples.append(
            (
                int(district_summary["seat_count"]),
                tuple(int(smd_id) for smd_id in district_summary["smd_ids"]),
            )
        )
    return tuple(sorted(tuples))


def generate_mmd_ensemble_from_smd_ensemble(
    smd_ensemble: list[dict],
    graph: Graph,
    seat_vector: tuple[int, ...] | list[int],
    plans_per_smd_plan: int = 5,
    population_tolerance: float = 0.05,
    seed: int = project_config.SEED,
    max_attempts_per_smd_plan: int = 250,
) -> list[dict]:
    """Expand temporary SMD plans into MMD plans by contiguous BFS merging."""
    if not seat_vector:
        raise ValueError("seat_vector must be non-empty for MMD generation")

    if any(int(seat_count) <= 0 for seat_count in seat_vector):
        raise ValueError("seat_vector must contain only positive integers")

    seat_vector = [int(seat_count) for seat_count in seat_vector]
    mmd_ensemble = []
    global_plan_id = 1
    master_rng = random.Random(seed)

    info("Converting temporary SMD plans into MMD plans.")
    info(f"Requested seat vector: {seat_vector}")
    info(f"MMD plans per SMD plan: {plans_per_smd_plan}")

    for smd_plan_index, smd_plan in enumerate(smd_ensemble, start=1):
        smd_assignment = smd_plan["assignment"]
        generated_for_this_smd_plan = 0
        attempts = 0
        seen_signatures = set()

        while (
            generated_for_this_smd_plan < plans_per_smd_plan
            and attempts < max_attempts_per_smd_plan
        ):
            attempts += 1
            plan_seed = master_rng.randint(0, 2**31 - 1)
            candidate_plan = _build_single_mmd_plan(
                smd_assignment=smd_assignment,
                graph=graph,
                seat_vector=seat_vector,
                population_tolerance=population_tolerance,
                seed=plan_seed,
            )

            if candidate_plan is None:
                continue

            is_valid, reason = _validate_mmd_plan(
                candidate_plan,
                graph=graph,
                seat_vector=seat_vector,
                population_tolerance=population_tolerance,
            )
            if not is_valid:
                continue

            signature = _mmd_plan_signature(candidate_plan)
            if signature in seen_signatures:
                continue

            seen_signatures.add(signature)
            candidate_plan["results"]["plan_id"] = global_plan_id
            candidate_plan["results"]["source_smd_plan_id"] = smd_plan["results"]["plan_id"]
            mmd_ensemble.append(candidate_plan)
            generated_for_this_smd_plan += 1
            global_plan_id += 1

        if generated_for_this_smd_plan < plans_per_smd_plan:
            warn(
                f"SMD plan {smd_plan_index}: generated "
                f"{generated_for_this_smd_plan}/{plans_per_smd_plan} MMD plans "
                f"after {attempts} attempts."
            )
        else:
            info(
                f"SMD plan {smd_plan_index}: generated "
                f"{generated_for_this_smd_plan}/{plans_per_smd_plan} MMD plans."
            )

    success(f"Generated {len(mmd_ensemble)} total MMD plans.")
    return mmd_ensemble


def runtime_mode_settings(run_config: RunConfig) -> dict[str, int | str]:
    """Compute mode-specific temporary SMD generation settings."""
    mode = run_config.generation_mode.strip().upper()
    if mode not in {"SMD", "MMD"}:
        raise ValueError("generation_mode must be either 'SMD' or 'MMD'")

    if mode == "SMD":
        smd_num_districts = run_config.num_districts
        smd_num_plans = run_config.num_plans
    else:
        if not run_config.seat_vector:
            raise ValueError("seat_vector must be non-empty when generation_mode='MMD'")

        smd_num_districts = run_config.mmd_smd_multiplier * len(run_config.seat_vector)
        smd_num_plans = max(1, run_config.num_plans // run_config.mmd_plans_per_smd_plan)

    return {
        "mode": mode,
        "smd_num_districts": smd_num_districts,
        "smd_num_plans": smd_num_plans,
    }


def generate_ensemble_for_run(graph: Graph, run_config: RunConfig) -> list[dict]:
    """Generate the final ensemble for the configured SMD or MMD mode."""
    mode_settings = runtime_mode_settings(run_config)
    info(f"Mode: {mode_settings['mode']}")
    info(f"Shape path: {run_config.shape_path}")
    info(f"Temporary SMD count: {mode_settings['smd_num_districts']}")
    info(f"Temporary SMD plans: {mode_settings['smd_num_plans']}")

    smd_ensemble = generate_baseline_ensemble(
        graph,
        num_plans=int(mode_settings["smd_num_plans"]),
        num_districts=int(mode_settings["smd_num_districts"]),
        seed=run_config.seed,
        population_tolerance=run_config.population_tolerance,
    )

    if run_config.save_intermediate_smd_plans and mode_settings["mode"] == "SMD":
        info(
            "save_intermediate_smd_plans is ignored when generation_mode='SMD' "
            "(it only applies to the temporary SMD plans built while generating MMD output)."
        )

    if mode_settings["mode"] == "MMD":
        if run_config.save_intermediate_smd_plans:
            save_intermediate_smd_plans(smd_ensemble, run_config.intermediate_smd_plans_dir)

        ensemble = generate_mmd_ensemble_from_smd_ensemble(
            smd_ensemble=smd_ensemble,
            graph=graph,
            seat_vector=run_config.seat_vector,
            plans_per_smd_plan=run_config.mmd_plans_per_smd_plan,
            population_tolerance=run_config.population_tolerance,
            seed=run_config.seed,
            max_attempts_per_smd_plan=run_config.max_mmd_attempts_per_smd_plan,
        )
        if not ensemble:
            raise RuntimeError(
                "MMD generation produced 0 valid plans. "
                "Try raising max_mmd_attempts_per_smd_plan or population_tolerance."
            )
        return ensemble

    return smd_ensemble

"""Output artifact helpers for MMD generation runs."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from Global_Utilities import info, success
from MMD_Generation_Layer import config as project_config
from MMD_Generation_Layer.Processor.runtime_setup import RunConfig


def save_ensemble_summary(ensemble: list[dict], csv_path: Path) -> pd.DataFrame:
    """Save ensemble result rows to CSV."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    results_df = pd.DataFrame([plan["results"] for plan in ensemble])
    results_df.to_csv(csv_path, index=False)
    success(f"Saved summary CSV: {csv_path}")
    return results_df


def save_plan_assignments(
    ensemble: list[dict],
    plans_dir: Path,
    clear_existing: bool = True,
) -> None:
    """Save precinct-to-district assignment JSON files for generated plans."""
    plans_dir.mkdir(parents=True, exist_ok=True)

    if clear_existing:
        for stale_plan in plans_dir.glob("plan_*.json"):
            stale_plan.unlink()

    for plan in ensemble:
        plan_id = plan["results"]["plan_id"]
        assignment_path = plans_dir / f"plan_{plan_id}.json"
        json_assignment = {str(key): int(value) for key, value in plan["assignment"].items()}
        with assignment_path.open("w") as file:
            json.dump(json_assignment, file)

    success(f"Saved {len(ensemble)} plan assignments to {plans_dir}")


def save_intermediate_smd_plans(
    smd_ensemble: list[dict],
    intermediate_smd_plans_dir: Path,
    clear_existing: bool = True,
) -> None:
    """Save temporary SMD assignment JSON files used to build MMD plans."""
    intermediate_smd_plans_dir.mkdir(parents=True, exist_ok=True)

    if clear_existing:
        for stale_plan in intermediate_smd_plans_dir.glob("smd_plan_*.json"):
            stale_plan.unlink()

    for smd_plan in smd_ensemble:
        plan_id = smd_plan["results"]["plan_id"]
        assignment_path = intermediate_smd_plans_dir / f"smd_plan_{plan_id}.json"
        json_assignment = {str(key): int(value) for key, value in smd_plan["assignment"].items()}
        with assignment_path.open("w") as file:
            json.dump(json_assignment, file)

    success(f"Saved {len(smd_ensemble)} intermediate SMD plans to {intermediate_smd_plans_dir}")


def plot_seat_share_histogram(results_df: pd.DataFrame, output_path: Path) -> None:
    """Create and save a Democratic seat-share histogram."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 6))
    plt.hist(
        results_df["dem_seat_share"],
        bins=10,
        edgecolor="black",
        alpha=0.7,
        color="steelblue",
    )
    plt.xlabel("Democratic Seat Share", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)

    plan_count = len(results_df)
    total_seats = (
        int((results_df["dem_seats"] + results_df["rep_seats"]).iloc[0])
        if plan_count
        else 0
    )
    plt.title(
        (
            "Ensemble: Democratic Seat Share Distribution\n"
            f"({plan_count} Random District Plans, {total_seats} Total Seats)"
        ),
        fontsize=14,
        fontweight="bold",
    )
    plt.axvline(
        results_df["dem_seat_share"].mean(),
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {results_df['dem_seat_share'].mean():.3f}",
    )
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    success(f"Saved histogram: {output_path}")


def generate_district_csvs(
    gdf: gpd.GeoDataFrame,
    plans_dir: Path,
    output_dir: Path,
    pop_col: str = project_config.POP_COLUMN,
    dem_col: str = project_config.DEM_COLUMN,
    rep_col: str = project_config.REP_COLUMN,
) -> bool:
    """Generate district-level CSV files for all saved plan assignments."""
    plan_files = sorted(plans_dir.glob("plan_*.json"))
    info(f"Found {len(plan_files)} plan assignment files.")

    for plan_file in plan_files:
        plan_id = int(plan_file.stem.split("_")[1])

        with plan_file.open("r") as file:
            assignment = json.load(file)

        assignment = {str(key): value for key, value in assignment.items()}
        district_results = []

        for district_id in sorted(set(assignment.values())):
            precinct_ids = [key for key, value in assignment.items() if value == district_id]
            district_precincts = gdf[gdf.index.isin(precinct_ids)]

            dem_votes = district_precincts[dem_col].sum()
            rep_votes = district_precincts[rep_col].sum()
            population = district_precincts[pop_col].sum()
            winner = "Democrat" if dem_votes > rep_votes else "Republican"

            district_results.append(
                {
                    "plan_id": plan_id,
                    "district_id": district_id,
                    "dem_votes": int(dem_votes),
                    "rep_votes": int(rep_votes),
                    "population": int(population),
                    "winner": winner,
                }
            )

        output_path = output_dir / f"baseline_districts_plan_{plan_id}.csv"
        pd.DataFrame(district_results).to_csv(output_path, index=False)
        info(f"Saved {len(district_results)} districts to {output_path.name}")

    success("Generated district-level CSV files.")
    return True


def save_output_artifacts(
    ensemble: list[dict],
    run_config: RunConfig,
    gdf: gpd.GeoDataFrame | None = None,
    include_plots: bool = True,
    include_district_csvs: bool = False,
) -> pd.DataFrame:
    """Save generated run artifacts and optional diagnostics."""
    run_config.output_dir.mkdir(parents=True, exist_ok=True)
    save_plan_assignments(ensemble, run_config.plans_dir)
    results_df = save_ensemble_summary(ensemble, run_config.ensemble_csv_path)

    if include_plots:
        plot_seat_share_histogram(results_df, run_config.seat_share_png_path)

    if include_district_csvs:
        if gdf is None:
            raise ValueError("gdf is required when include_district_csvs=True")
        generate_district_csvs(
            gdf,
            run_config.plans_dir,
            run_config.output_dir,
            pop_col=run_config.pop_column,
            dem_col=run_config.dem_column,
            rep_col=run_config.rep_column,
        )

    return results_df


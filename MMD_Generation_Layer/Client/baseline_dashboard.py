#!/usr/bin/env python3
"""Baseline ensemble Streamlit dashboard."""

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from MMD_Generation_Layer import config as project_config
from MMD_Generation_Layer.Processor.output_artifacts import district_color_map
from MMD_Generation_Layer.Processor.runtime_setup import load_dashboard_run_metadata
from MMD_Generation_Layer.Processor.seat_allocation import (
    SEAT_ALLOCATION_LABEL,
    SEAT_ALLOCATION_METHOD,
    democratic_vote_share,
)

PROXY_CAPTION = (
    f"Seat counts use the **{SEAT_ALLOCATION_LABEL.lower()}**: each district's seats are split "
    "by its Democratic share of major-party votes, `round(seats × dem_votes / (dem_votes + rep_votes))`, "
    "and Republicans get the rest. Exact half seats round to the even Democratic count; districts with "
    "no major-party votes count as an even split. This approximates representation from single-choice "
    "vote totals and is not FRA ranked-choice tabulation."
)


def discover_available_states(outputs_root: Path) -> list[str]:
    """List state folders under outputs_root, most recently modified first."""
    if not outputs_root.exists():
        return []

    state_dirs = [entry for entry in outputs_root.iterdir() if entry.is_dir()]
    state_dirs.sort(key=lambda entry: entry.stat().st_mtime, reverse=True)
    return [entry.name for entry in state_dirs]


# Page config
st.set_page_config(
    page_title="FRA Pipeline - Baseline Dashboard",
    page_icon="🗺️",
    layout="wide",
)


def load_ensemble_results(csv_path: str) -> pd.DataFrame:
    """Read current ensemble results CSV on every dashboard rerun."""
    return pd.read_csv(csv_path)


@st.cache_data
def load_shapefile(
    shape_path: str, id_col: str, geom_col: str, dem_col: str, rep_col: str
) -> gpd.GeoDataFrame:
    """Load geodata for map rendering, plus precinct Democratic and Republican votes."""
    gdf = gpd.read_file(shape_path)

    missing = {id_col, dem_col, rep_col} - set(gdf.columns)
    if missing:
        raise ValueError(f"Missing required columns {sorted(missing)} in shapefile")

    if geom_col in gdf.columns and gdf.geometry.name != geom_col:
        gdf = gdf.set_geometry(geom_col)

    keep_cols = [id_col, dem_col, rep_col, gdf.geometry.name]
    gdf = gdf[keep_cols].copy()
    gdf[id_col] = gdf[id_col].astype(str)
    for vote_col in (dem_col, rep_col):
        gdf[vote_col] = pd.to_numeric(gdf[vote_col], errors="coerce").fillna(0).astype(int)
    return gdf


def load_plan_assignment(plan_id: int, plans_dir: Path) -> dict[str, int] | None:
    """Load district assignment for a specific plan."""
    assignment_path = plans_dir / f"plan_{plan_id}.json"

    if not assignment_path.exists():
        return None

    with assignment_path.open("r") as f:
        assignment = json.load(f)

    return {str(k): int(v) for k, v in assignment.items()}


def create_district_map(
    gdf: gpd.GeoDataFrame,
    assignment: dict[str, int],
    plan_id: int,
    id_col: str,
    dissolve_districts: bool = True,
    show_precinct_lines: bool = True,
    district_edgecolor: str = "black",
    district_linewidth: float = 0.8,
    precinct_edgecolor: str = "white",
    precinct_linewidth: float = 0.4,
    precinct_alpha: float = 0.25,
):
    """Create a district map labelled with the assignment IDs used in district CSVs."""
    gdf_plot = gdf.copy()
    gdf_plot["district"] = gdf_plot[id_col].astype(str).map(assignment)

    missing = gdf_plot["district"].isna().sum()
    if missing > 0:
        st.warning(f"⚠️ {missing} precincts missing district assignment (ID mismatch).")

    gdf_plot = gdf_plot.dropna(subset=["district"])
    district_shapes = gdf_plot.dissolve(by="district")
    colors_by_district = district_color_map(assignment.values())
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    if dissolve_districts:
        district_shapes.plot(
            ax=ax,
            color=[colors_by_district[district_id] for district_id in district_shapes.index],
            edgecolor=district_edgecolor,
            linewidth=district_linewidth,
        )

        if show_precinct_lines:
            gdf_plot.plot(
                ax=ax,
                facecolor="none",
                edgecolor=precinct_edgecolor,
                linewidth=precinct_linewidth,
                alpha=precinct_alpha,
            )
    else:
        gdf_plot.plot(
            ax=ax,
            color=gdf_plot["district"].map(colors_by_district),
            edgecolor=(precinct_edgecolor if show_precinct_lines else "none"),
            linewidth=(precinct_linewidth if show_precinct_lines else 0),
            alpha=1.0,
        )

        if show_precinct_lines and district_linewidth > 0:
            district_shapes.boundary.plot(
                ax=ax,
                color=district_edgecolor,
                linewidth=district_linewidth,
                alpha=1.0,
            )

    for district_id, geometry in district_shapes.geometry.items():
        label_point = geometry.representative_point()
        ax.text(
            label_point.x,
            label_point.y,
            f"District {int(district_id)}",
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="black",
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "gray", "alpha": 0.9},
            zorder=10,
        )

    ax.set_title(
        f"Plan {plan_id}: District Map ({len(district_shapes)} Districts)",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.axis("off")
    plt.tight_layout()
    return fig


def plot_baseline_histogram(
    results_df: pd.DataFrame, output_dir: Path, total_seats: int, num_plans: int
):
    """Create and save histogram of Democratic vote-share proxy seat counts."""
    fig, ax = plt.subplots(figsize=(10, 6))

    bins = range(results_df["dem_seats"].min(), results_df["dem_seats"].max() + 2)
    ax.hist(
        results_df["dem_seats"],
        bins=bins,
        edgecolor="black",
        alpha=0.7,
        color="steelblue",
        align="left",
    )

    mean_seats = results_df["dem_seats"].mean()
    ax.axvline(
        mean_seats,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {mean_seats:.2f}",
    )

    ax.set_xlabel(
        f"Democratic Seats (out of {total_seats}, vote-share proxy)", fontsize=12, fontweight="bold"
    )
    ax.set_ylabel("Frequency (Number of Plans)", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Baseline Ensemble: Democratic Seat Distribution\n({num_plans} Random District Plans, "
        f"{SEAT_ALLOCATION_LABEL})",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    ax.set_xticks(range(0, total_seats + 1))
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend(fontsize=11, loc="upper right")
    plt.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "democratic_seats.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig, output_path


def main():
    """Main dashboard application."""
    outputs_root = project_config.base_dir / "Outputs"
    available_states = discover_available_states(outputs_root)

    if not available_states:
        st.error("❌ No pipeline runs found under Outputs/. Run the MMD pipeline for a state first.")
        st.stop()

    selected_state = st.sidebar.selectbox("State", options=available_states)
    dashboard_metadata = load_dashboard_run_metadata(outputs_root / selected_state)

    st.title("🗺️ Baseline Ensemble Dashboard")
    st.markdown("### Step 1: Traditional Single-Member Districts")
    st.markdown("---")

    if not dashboard_metadata.ensemble_csv_path.exists():
        st.error(f"❌ Results not found at: {dashboard_metadata.ensemble_csv_path}")
        st.info("Please run the baseline generation pipeline first.")
        st.stop()

    if not dashboard_metadata.shape_path.exists():
        st.error(f"❌ Shapefile not found at: {dashboard_metadata.shape_path}")
        st.stop()

    if not dashboard_metadata.plans_dir.exists():
        st.error(f"❌ Plan assignments directory not found at: {dashboard_metadata.plans_dir}")
        st.stop()

    with st.spinner("Loading data..."):
        results_df = load_ensemble_results(str(dashboard_metadata.ensemble_csv_path))
        gdf = load_shapefile(
            str(dashboard_metadata.shape_path),
            dashboard_metadata.id_column,
            dashboard_metadata.geom_column,
            dashboard_metadata.dem_column,
            dashboard_metadata.rep_column,
        )
    statewide_dem_vote_share = democratic_vote_share(
        int(gdf[dashboard_metadata.dem_column].sum()),
        int(gdf[dashboard_metadata.rep_column].sum()),
    )

    st.success(f"✅ Loaded {len(results_df)} plans with {len(gdf)} precincts")

    uses_proxy = (
        "seat_allocation_method" in results_df.columns
        and (results_df["seat_allocation_method"] == SEAT_ALLOCATION_METHOD).all()
    )
    if uses_proxy:
        st.info(PROXY_CAPTION)
    else:
        st.warning(
            "⚠️ These outputs predate the vote-share proxy, so their seat counts are winner-take-all "
            "per district. Re-run the MMD pipeline for this state to get proxy seat counts."
        )

    total_seats = (
        int(results_df["total_seats"].iloc[0])
        if "total_seats" in results_df.columns
        else dashboard_metadata.num_districts
    )

    st.sidebar.header("📊 Plan Selection")
    plan_id = st.sidebar.selectbox(
        "Choose a plan to visualize:",
        options=results_df["plan_id"].tolist(),
        format_func=lambda x: f"Plan {x}",
    )

    assignment = load_plan_assignment(int(plan_id), dashboard_metadata.plans_dir)
    if assignment is None:
        st.error(f"❌ Could not load assignment for Plan {plan_id}")
        st.stop()

    selected_plan = results_df[results_df["plan_id"] == plan_id].iloc[0]

    st.sidebar.markdown("---")
    st.sidebar.subheader(f"Plan {plan_id} Results")
    st.sidebar.caption(SEAT_ALLOCATION_LABEL)
    st.sidebar.metric("Democratic Seats", f"{int(selected_plan['dem_seats'])}/{total_seats}")
    st.sidebar.metric("Republican Seats", f"{int(selected_plan['rep_seats'])}/{total_seats}")
    st.sidebar.metric("Dem Seat Share", f"{selected_plan['dem_seat_share']:.1%}")
    st.sidebar.metric(
        "Dem Vote Share (statewide)",
        f"{float(statewide_dem_vote_share):.1%}",
        help="Democratic share of statewide major-party votes; the same for every plan.",
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"🗺️ District Map - Plan {plan_id}")
        with st.spinner("Rendering map..."):
            fig_map = create_district_map(
                gdf,
                assignment,
                int(plan_id),
                dashboard_metadata.id_column,
            )
            st.pyplot(fig_map)
            plt.close(fig_map)

    with col2:
        st.subheader("📈 Seat Distribution (Vote-Share Proxy)")

        fig_pie, ax_pie = plt.subplots(figsize=(6, 6))
        colors_pie = ["#4A90E2", "#E24A4A"]
        ax_pie.pie(
            [selected_plan["dem_seats"], selected_plan["rep_seats"]],
            labels=["Democrat", "Republican"],
            colors=colors_pie,
            autopct="%1.1f%%",
            startangle=90,
            textprops={"fontsize": 12, "weight": "bold"},
        )
        ax_pie.set_title(f"Plan {plan_id} Seat Distribution", fontsize=14, fontweight="bold")
        st.pyplot(fig_pie)
        plt.close(fig_pie)

        st.markdown("#### Summary Stats")
        summary_data = {
            "Metric": ["Dem Seats", "Rep Seats", "Total Seats", "Dem Seat Share"],
            "Value": [
                selected_plan["dem_seats"],
                selected_plan["rep_seats"],
                total_seats,
                f"{selected_plan['dem_seat_share']:.3f}",
            ],
        }
        st.table(pd.DataFrame(summary_data))

    st.markdown("---")
    st.subheader(f"📊 Comparative Analysis: All {len(results_df)} Plans")

    fig_hist, hist_output_path = plot_baseline_histogram(
        results_df,
        dashboard_metadata.output_dir,
        total_seats,
        dashboard_metadata.num_plans,
    )
    st.pyplot(fig_hist)
    plt.close(fig_hist)
    st.caption(f"Histogram saved to {hist_output_path}")

    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Mean Dem Share", f"{results_df['dem_seat_share'].mean():.3f}")
    with col_stat2:
        st.metric("Std Deviation", f"{results_df['dem_seat_share'].std():.3f}")
    with col_stat3:
        st.metric("Min Dem Share", f"{results_df['dem_seat_share'].min():.3f}")
    with col_stat4:
        st.metric("Max Dem Share", f"{results_df['dem_seat_share'].max():.3f}")

    st.markdown("---")
    st.subheader("📋 All Plans - Detailed Results")

    display_df = results_df.copy()
    display_df["dem_share_pct"] = (display_df["dem_seat_share"] * 100).round(1)
    display_df = display_df.rename(
        columns={
            "plan_id": "Plan ID",
            "dem_seats": "Dem Seats",
            "rep_seats": "Rep Seats",
            "dem_share_pct": "Dem Share %",
        }
    )

    st.dataframe(
        display_df[["Plan ID", "Dem Seats", "Rep Seats", "Dem Share %"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.markdown(
        """
        **About This Analysis:**
        - Generated {0} random district plans using GerryChain's ReCom algorithm
        - Seats use an **interim vote-share proxy**: each district's seats are split by its
          Democratic share of major-party votes (not FRA ranked-choice tabulation)
        - Population deviation constrained to ±5%
        - All districts are contiguous

        **Key Insight:** Notice how Democratic seat share varies across plans (range: {1:.1%} - {2:.1%}),
        demonstrating how district boundaries affect electoral outcomes even with the same voters!
        """.format(
            len(results_df),
            results_df["dem_seat_share"].min(),
            results_df["dem_seat_share"].max(),
        )
    )


if __name__ == "__main__":
    main()

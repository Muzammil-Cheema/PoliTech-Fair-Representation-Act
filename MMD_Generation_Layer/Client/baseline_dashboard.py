#!/usr/bin/env python3
"""Baseline ensemble Streamlit dashboard."""

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from MMD_Generation_Layer.config import (
    output_dir,
    plans_dir,
    ensemble_csv_path,
)
from MMD_Generation_Layer.Processor.runtime_setup import load_dashboard_config


# Page config
st.set_page_config(
    page_title="FRA Pipeline - Baseline Dashboard",
    page_icon="🗺️",
    layout="wide",
)


@st.cache_data
def load_ensemble_results(csv_path: str) -> pd.DataFrame:
    """Load baseline ensemble results CSV."""
    return pd.read_csv(csv_path)


@st.cache_data
def load_shapefile(shape_path: str, id_col: str, geom_col: str) -> gpd.GeoDataFrame:
    """Load geodata for map rendering."""
    gdf = gpd.read_file(shape_path)

    if id_col not in gdf.columns:
        raise ValueError(f"Missing required ID column '{id_col}' in shapefile")

    if geom_col in gdf.columns and gdf.geometry.name != geom_col:
        gdf = gdf.set_geometry(geom_col)

    keep_cols = [id_col, gdf.geometry.name]
    gdf = gdf[keep_cols].copy()
    gdf[id_col] = gdf[id_col].astype(str)
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
    num_districts: int,
    dissolve_districts: bool = True,
    show_precinct_lines: bool = True,
    district_edgecolor: str = "black",
    district_linewidth: float = 0.8,
    precinct_edgecolor: str = "white",
    precinct_linewidth: float = 0.4,
    precinct_alpha: float = 0.25,
):
    """Create district map figure for a selected plan."""
    gdf_plot = gdf.copy()
    gdf_plot["district"] = gdf_plot[id_col].astype(str).map(assignment)

    missing = gdf_plot["district"].isna().sum()
    if missing > 0:
        st.warning(f"⚠️ {missing} precincts missing district assignment (ID mismatch).")

    gdf_plot = gdf_plot.dropna(subset=["district"])
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    colors = ['Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap', 'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Grays', 'Grays_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy', 'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r', 'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'berlin', 'berlin_r', 'binary', 'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r', 'cividis', 'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix', 'cubehelix_r', 'flag', 'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_grey', 'gist_grey_r', 'gist_heat', 'gist_heat_r', 'gist_ncar', 'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gist_yerg', 'gist_yerg_r', 'gnuplot', 'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'grey', 'grey_r', 'hot', 'hot_r', 'hsv', 'hsv_r', 'inferno', 'inferno_r', 'jet', 'jet_r', 'magma', 'magma_r', 'managua', 'managua_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r', 'rainbow', 'rainbow_r', 'seismic', 'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r', 'tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r', 'turbo', 'turbo_r', 'twilight', 'twilight_r', 'twilight_shifted', 'twilight_shifted_r', 'vanimo', 'vanimo_r', 'viridis', 'viridis_r', 'winter', 'winter_r']
    cmap = plt.cm.get_cmap("tab20", num_districts)

    if dissolve_districts:
        district_shapes = gdf_plot.dissolve(by="district")
        district_shapes.plot(
            ax=ax,
            cmap=cmap,
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
            column="district",
            cmap=cmap,
            edgecolor=(precinct_edgecolor if show_precinct_lines else "none"),
            linewidth=(precinct_linewidth if show_precinct_lines else 0),
            alpha=1.0,
        )

        if show_precinct_lines and district_linewidth > 0:
            district_shapes = gdf_plot.dissolve(by="district")
            district_shapes.boundary.plot(
                ax=ax,
                color=district_edgecolor,
                linewidth=district_linewidth,
                alpha=1.0,
            )

    ax.set_title(
        f"Plan {plan_id}: District Map ({num_districts} Districts)",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.axis("off")
    plt.tight_layout()
    return fig


def plot_baseline_histogram(
    results_df: pd.DataFrame, output_dir: Path, num_districts: int, num_plans: int
):
    """Create and save histogram of Democratic seat distribution."""
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

    ax.set_xlabel(f"Democratic Seats (out of {num_districts})", fontsize=12, fontweight="bold")
    ax.set_ylabel("Frequency (Number of Plans)", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Baseline Ensemble: Democratic Seat Distribution\n({num_plans} Random Single-Member District Plans)",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    ax.set_xticks(range(0, num_districts + 1))
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend(fontsize=11, loc="upper right")
    plt.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "democratic_seats.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig, output_path


def main():
    """Main dashboard application."""
    dashboard_config = load_dashboard_config()

    st.title("🗺️ Baseline Ensemble Dashboard")
    st.markdown("### Step 1: Traditional Single-Member Districts")
    st.markdown("---")

    if not ensemble_csv_path.exists():
        st.error(f"❌ Results not found at: {ensemble_csv_path}")
        st.info("Please run the baseline generation pipeline first.")
        st.stop()

    if not dashboard_config.shape_path.exists():
        st.error(f"❌ Shapefile not found at: {dashboard_config.shape_path}")
        st.stop()

    if not plans_dir.exists():
        st.error(f"❌ Plan assignments directory not found at: {plans_dir}")
        st.stop()

    with st.spinner("Loading data..."):
        results_df = load_ensemble_results(str(ensemble_csv_path))
        gdf = load_shapefile(
            str(dashboard_config.shape_path),
            dashboard_config.id_column,
            dashboard_config.geom_column,
        )

    st.success(f"✅ Loaded {len(results_df)} plans with {len(gdf)} precincts")

    st.sidebar.header("📊 Plan Selection")
    plan_id = st.sidebar.selectbox(
        "Choose a plan to visualize:",
        options=results_df["plan_id"].tolist(),
        format_func=lambda x: f"Plan {x}",
    )

    assignment = load_plan_assignment(int(plan_id), plans_dir)
    if assignment is None:
        st.error(f"❌ Could not load assignment for Plan {plan_id}")
        st.stop()

    selected_plan = results_df[results_df["plan_id"] == plan_id].iloc[0]

    st.sidebar.markdown("---")
    st.sidebar.subheader(f"Plan {plan_id} Results")
    st.sidebar.metric(
        "Democratic Seats", f"{selected_plan['dem_seats']}/{dashboard_config.num_districts}"
    )
    st.sidebar.metric(
        "Republican Seats", f"{selected_plan['rep_seats']}/{dashboard_config.num_districts}"
    )
    st.sidebar.metric("Dem Seat Share", f"{selected_plan['dem_seat_share']:.1%}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"🗺️ District Map - Plan {plan_id}")
        with st.spinner("Rendering map..."):
            fig_map = create_district_map(
                gdf,
                assignment,
                int(plan_id),
                dashboard_config.id_column,
                dashboard_config.num_districts,
            )
            st.pyplot(fig_map)
            plt.close(fig_map)

    with col2:
        st.subheader("📈 Seat Distribution")

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
            "Metric": ["Dem Seats", "Rep Seats", "Total Districts", "Dem Share"],
            "Value": [
                selected_plan["dem_seats"],
                selected_plan["rep_seats"],
                dashboard_config.num_districts,
                f"{selected_plan['dem_seat_share']:.3f}",
            ],
        }
        st.table(pd.DataFrame(summary_data))

    st.markdown("---")
    st.subheader(f"📊 Comparative Analysis: All {len(results_df)} Plans")

    fig_hist, hist_output_path = plot_baseline_histogram(
        results_df, output_dir, dashboard_config.num_districts, dashboard_config.num_plans
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
        - Each district uses **winner-take-all** (plurality voting)
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

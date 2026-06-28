"""Command-line runner for MMD generation workflows."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Global_Utilities import info, success
from MMD_Generation_Layer import config as project_config
from MMD_Generation_Layer.Processor.runtime_setup import (
    bootstrap_run_config,
    describe_run_config,
)


def run_generation_pipeline(
    config_path: str | Path | None = None,
    include_plots: bool = True,
    include_district_csvs: bool = False,
) -> list[dict]:
    """Run graph building, generation, and artifact writing."""
    from MMD_Generation_Layer.Processor.generation_logic import (
        generate_ensemble_for_run,
        load_and_build_graph,
    )
    from MMD_Generation_Layer.Processor.output_artifacts import save_output_artifacts

    run_config = bootstrap_run_config(config_path)
    describe_run_config(run_config)

    graph, gdf = load_and_build_graph(
        run_config.shape_path,
        run_config.id_column,
        run_config.geom_column,
    )
    ensemble = generate_ensemble_for_run(graph, run_config)
    save_output_artifacts(
        ensemble,
        run_config,
        gdf=gdf,
        include_plots=include_plots,
        include_district_csvs=include_district_csvs,
    )
    success("MMD generation pipeline complete.")
    return ensemble


def run_streamlit_dashboard(extra_args: Sequence[str] | None = None) -> int:
    """Run the Streamlit dashboard from the Client layer."""
    dashboard_path = project_config.base_dir / "Client" / "baseline_dashboard.py"
    command = ["streamlit", "run", str(dashboard_path), *(extra_args or [])]
    info(f"Starting Streamlit dashboard: {' '.join(command)}")
    return subprocess.run(command, check=False).returncode


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line options for the MMD generation runner."""
    parser = argparse.ArgumentParser(description="Run MMD generation from Python scripts.")
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="Optional JSON run config path.",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Skip optional histogram output.",
    )
    parser.add_argument(
        "--district-csvs",
        action="store_true",
        help="Generate district-level CSV diagnostics after assignments are saved.",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Run the Streamlit dashboard after generation completes.",
    )
    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="Run Streamlit without generating new plans.",
    )
    parser.add_argument(
        "streamlit_args",
        nargs=argparse.REMAINDER,
        help="Extra args passed to Streamlit after --.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MMD generation command-line workflow."""
    args = parse_args(argv)

    if args.dashboard_only:
        return run_streamlit_dashboard(args.streamlit_args)

    run_generation_pipeline(
        config_path=args.config,
        include_plots=not args.skip_plots,
        include_district_csvs=args.district_csvs,
    )

    if args.dashboard:
        return run_streamlit_dashboard(args.streamlit_args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

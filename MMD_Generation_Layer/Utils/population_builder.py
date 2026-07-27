"""Reconstruct precinct-level population from 2020 Census TIGER/Line blocks.

State-agnostic: pass any two-digit state FIPS code and a precinct GeoDataFrame.
Census TIGER/Line tabblock20 shapefiles ship with a `POP20` field already
joined from the 2020 Decennial Census, so no separate PL 94-171 / Census API
call (and no API key) is required.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import geopandas as gpd
import pandas as pd
import requests

from Global_Utilities import info, success, warn

TIGER_BLOCK_URL_TEMPLATE = (
    "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_{state_fips}_tabblock20.zip"
)
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[1] / "Data" / "Census_Blocks"

# NAD83 / Conus Albers Equal Area — used only for area calculations so that
# area-weighted apportionment isn't distorted by a geographic (lat/lon) CRS.
AREA_CRS = "EPSG:5070"


def download_census_blocks(state_fips: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    """Download (or reuse cached) TIGER/Line 2020 block shapefile for a state."""
    state_dir = cache_dir / state_fips
    shp_path = state_dir / f"tl_2020_{state_fips}_tabblock20.shp"
    if shp_path.exists():
        info(f"Using cached census blocks: {shp_path}")
        return shp_path

    state_dir.mkdir(parents=True, exist_ok=True)
    zip_path = state_dir / f"tl_2020_{state_fips}_tabblock20.zip"
    url = TIGER_BLOCK_URL_TEMPLATE.format(state_fips=state_fips)

    info(f"Downloading census blocks for state FIPS {state_fips}: {url}")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    zip_path.write_bytes(response.content)

    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(state_dir)
    zip_path.unlink()

    if not shp_path.exists():
        raise FileNotFoundError(f"Expected shapefile not found after extraction: {shp_path}")

    success(f"Downloaded and cached census blocks: {shp_path}")
    return shp_path


def build_block_population_points(state_fips: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> gpd.GeoDataFrame:
    """Return a point GeoDataFrame of block internal points and POP20."""
    shp_path = download_census_blocks(state_fips, cache_dir)
    blocks = gpd.read_file(shp_path)

    points = gpd.GeoDataFrame(
        {
            "GEOID20": blocks["GEOID20"],
            "POP20": pd.to_numeric(blocks["POP20"], errors="coerce").fillna(0).astype(int),
        },
        geometry=gpd.points_from_xy(
            blocks["INTPTLON20"].astype(float),
            blocks["INTPTLAT20"].astype(float),
        ),
        crs=blocks.crs,
    )
    return points


def assign_population_to_precincts(
    precinct_gdf: gpd.GeoDataFrame,
    block_points_gdf: gpd.GeoDataFrame,
    precinct_id_col: str,
) -> pd.DataFrame:
    """Sum block population into precincts via point-in-polygon spatial join."""
    if block_points_gdf.crs != precinct_gdf.crs:
        block_points_gdf = block_points_gdf.to_crs(precinct_gdf.crs)

    joined = gpd.sjoin(
        block_points_gdf,
        precinct_gdf[[precinct_id_col, precinct_gdf.geometry.name]],
        how="left",
        predicate="within",
    )

    unmatched = joined[precinct_id_col].isna().sum()
    if unmatched:
        warn(f"{unmatched} census blocks did not fall within any precinct.")

    totals = joined.groupby(precinct_id_col)["POP20"].sum().reset_index()
    totals = totals.rename(columns={"POP20": "TOTPOP"})
    return totals


def reconstruct_totpop(
    precinct_gdf: gpd.GeoDataFrame,
    state_fips: str,
    id_col: str,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> gpd.GeoDataFrame:
    """Return a copy of precinct_gdf with a reconstructed TOTPOP column."""
    info(f"Reconstructing TOTPOP for state FIPS {state_fips} using {id_col} as precinct key.")
    block_points = build_block_population_points(state_fips, cache_dir)
    totals = assign_population_to_precincts(precinct_gdf, block_points, id_col)

    result = precinct_gdf.merge(totals, on=id_col, how="left")
    missing = result["TOTPOP"].isna().sum()
    if missing:
        warn(f"{missing} precincts received no population (set to 0).")
    result["TOTPOP"] = result["TOTPOP"].fillna(0).astype(int)

    success(f"Reconstructed TOTPOP for {len(result)} precincts (total pop: {result['TOTPOP'].sum():,}).")
    return result


def build_block_population_polygons(state_fips: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> gpd.GeoDataFrame:
    """Return the full block polygons (not just internal points) with POP20."""
    shp_path = download_census_blocks(state_fips, cache_dir)
    blocks = gpd.read_file(shp_path)

    polygons = blocks[["GEOID20", "geometry"]].copy()
    polygons["POP20"] = pd.to_numeric(blocks["POP20"], errors="coerce").fillna(0).astype(int)
    return polygons


def assign_population_to_precincts_area_weighted(
    precinct_gdf: gpd.GeoDataFrame,
    block_polygons_gdf: gpd.GeoDataFrame,
    precinct_id_col: str,
) -> pd.DataFrame:
    """Split each block's population across precincts proportional to overlap area.

    More expensive than the point-in-polygon method (computes real polygon
    intersections for every block), but a block that straddles two precincts
    contributes population to both, proportional to how much of its area
    falls in each — instead of being assigned wholesale to one.
    """
    blocks = block_polygons_gdf.to_crs(AREA_CRS)
    precincts = precinct_gdf[[precinct_id_col, precinct_gdf.geometry.name]].to_crs(AREA_CRS)

    blocks["block_area"] = blocks.geometry.area
    blocks = blocks[blocks["block_area"] > 0]

    pieces = gpd.overlay(blocks, precincts, how="intersection")
    pieces["piece_area"] = pieces.geometry.area
    pieces["area_fraction"] = pieces["piece_area"] / pieces["block_area"]
    pieces["apportioned_pop"] = pieces["POP20"] * pieces["area_fraction"]

    covered_fraction = pieces.groupby("GEOID20")["area_fraction"].sum()
    uncovered = covered_fraction[covered_fraction < 0.999]
    if len(uncovered):
        warn(f"{len(uncovered)} census blocks are only partially covered by precincts (gaps in precinct coverage).")

    totals = pieces.groupby(precinct_id_col)["apportioned_pop"].sum().reset_index()
    totals["TOTPOP"] = totals["apportioned_pop"].round().astype(int)
    return totals[[precinct_id_col, "TOTPOP"]]


def reconstruct_totpop_area_weighted(
    precinct_gdf: gpd.GeoDataFrame,
    state_fips: str,
    id_col: str,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> gpd.GeoDataFrame:
    """Return a copy of precinct_gdf with TOTPOP reconstructed via area-weighted apportionment."""
    info(f"Reconstructing TOTPOP (area-weighted) for state FIPS {state_fips} using {id_col} as precinct key.")
    block_polygons = build_block_population_polygons(state_fips, cache_dir)
    totals = assign_population_to_precincts_area_weighted(precinct_gdf, block_polygons, id_col)

    result = precinct_gdf.merge(totals, on=id_col, how="left")
    missing = result["TOTPOP"].isna().sum()
    if missing:
        warn(f"{missing} precincts received no population (set to 0).")
    result["TOTPOP"] = result["TOTPOP"].fillna(0).astype(int)

    success(
        f"Reconstructed TOTPOP (area-weighted) for {len(result)} precincts "
        f"(total pop: {result['TOTPOP'].sum():,})."
    )
    return result


def compare_point_vs_area_weighted(
    precinct_gdf: gpd.GeoDataFrame,
    state_fips: str,
    id_col: str,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> pd.DataFrame:
    """Run both reconstruction methods and report where they disagree."""
    point_result = reconstruct_totpop(precinct_gdf, state_fips, id_col, cache_dir)
    area_result = reconstruct_totpop_area_weighted(precinct_gdf, state_fips, id_col, cache_dir)

    merged = point_result[[id_col, "TOTPOP"]].merge(
        area_result[[id_col, "TOTPOP"]],
        on=id_col,
        suffixes=("_point", "_area_weighted"),
    )
    merged["diff"] = merged["TOTPOP_point"] - merged["TOTPOP_area_weighted"]

    mismatched = (merged["diff"] != 0).sum()
    info(f"Precincts compared: {len(merged)}")
    info(
        f"Statewide total — point: {merged['TOTPOP_point'].sum():,}, "
        f"area-weighted: {merged['TOTPOP_area_weighted'].sum():,}"
    )
    if mismatched:
        warn(f"{mismatched} precincts differ between the two methods.")
    else:
        success("Both methods agree exactly on every precinct.")

    return merged


def compare_totpop(
    reconstructed_gdf: gpd.GeoDataFrame,
    original_shape_path: Path,
    id_col: str,
) -> pd.DataFrame:
    """Compare reconstructed TOTPOP against a known-good original shapefile."""
    original = gpd.read_file(original_shape_path)
    original["TOTPOP"] = pd.to_numeric(original["TOTPOP"], errors="coerce").fillna(0).astype(int)

    merged = reconstructed_gdf[[id_col, "TOTPOP"]].merge(
        original[[id_col, "TOTPOP"]],
        on=id_col,
        suffixes=("_reconstructed", "_original"),
    )
    merged["diff"] = merged["TOTPOP_reconstructed"] - merged["TOTPOP_original"]

    total_reconstructed = merged["TOTPOP_reconstructed"].sum()
    total_original = merged["TOTPOP_original"].sum()
    mismatched = (merged["diff"] != 0).sum()

    info(f"Precincts compared: {len(merged)}")
    info(f"Statewide total — reconstructed: {total_reconstructed:,}, original: {total_original:,}")
    if mismatched:
        warn(f"{mismatched} precincts differ from the original TOTPOP.")
    else:
        success("All precincts match the original TOTPOP exactly.")

    return merged


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line options for the population reconstruction CLI."""
    parser = argparse.ArgumentParser(
        description="Reconstruct precinct-level TOTPOP from 2020 Census TIGER/Line blocks."
    )
    parser.add_argument("--input", "-i", required=True, help="Path to the precinct shapefile.")
    parser.add_argument("--state-fips", "-s", required=True, help="Two-digit state FIPS code (e.g. 37 for NC, 51 for VA).")
    parser.add_argument("--id-col", default="UNIQUE_ID", help="Precinct ID column name (default: UNIQUE_ID).")
    parser.add_argument("--output", "-o", required=True, help="Output shapefile path for the result.")
    parser.add_argument(
        "--method",
        choices=["point", "area", "both"],
        default="point",
        help=(
            "point: assign each block wholesale to the precinct containing its internal point (fast, default). "
            "area: split each block's population proportional to overlap area with each precinct (slower, more precise). "
            "both: compute both and save TOTPOP_point/TOTPOP_area_weighted columns for comparison."
        ),
    )
    parser.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        help=f"Directory to cache downloaded Census blocks (default: {DEFAULT_CACHE_DIR}).",
    )
    parser.add_argument(
        "--compare-to",
        default=None,
        help="Optional path to a shapefile with an existing TOTPOP column to validate against.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the population reconstruction command-line workflow."""
    args = parse_args(argv)

    precincts = gpd.read_file(args.input)
    cache_dir = Path(args.cache_dir)

    if args.method == "both":
        comparison = compare_point_vs_area_weighted(precincts, args.state_fips, args.id_col, cache_dir)
        result = precincts.merge(
            comparison.rename(columns={"TOTPOP_point": "TOTPOP_point", "TOTPOP_area_weighted": "TOTPOP_area_weighted"}),
            on=args.id_col,
            how="left",
        )
    elif args.method == "area":
        result = reconstruct_totpop_area_weighted(precincts, args.state_fips, args.id_col, cache_dir)
    else:
        result = reconstruct_totpop(precincts, args.state_fips, args.id_col, cache_dir)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    result.to_file(args.output)
    success(f"Saved: {args.output}")

    if args.compare_to:
        compare_col = "TOTPOP_point" if args.method == "both" else "TOTPOP"
        compare_totpop(result.rename(columns={compare_col: "TOTPOP"}), Path(args.compare_to), id_col=args.id_col)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from pathlib import Path

import pytest

pytest.importorskip("gerrychain")

import geopandas as gpd
from shapely.geometry import box

from MMD_Generation_Layer.Processor.generation_logic import load_and_build_graph


def write_two_by_two_precincts(path: Path) -> Path:
    """Write a 2x2 grid of square precincts with population and vote columns."""
    rows = []
    for index, (x, y) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
        rows.append(
            {
                "UNIQUE_ID": f"P{index}",
                "TOTPOP": 100 * (index + 1),
                "G24PREDHAR": 10 * (index + 1),
                "G24PRERTRU": 5 * (index + 1),
                "geometry": box(x, y, x + 1, y + 1),
            }
        )
    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:3857")
    gdf.to_file(path)
    return path


def test_load_and_build_graph_sets_node_attributes_with_gerrychain_1_api(tmp_path: Path) -> None:
    """The loader builds a precinct graph and stores population/vote attributes per node."""
    shape_path = write_two_by_two_precincts(tmp_path / "precincts.shp")

    graph, gdf = load_and_build_graph(
        shape_path=shape_path,
        id_col="UNIQUE_ID",
        geom_col="geometry",
        pop_col="TOTPOP",
        dem_col="G24PREDHAR",
        rep_col="G24PRERTRU",
    )

    assert sorted(graph.nodes) == ["P0", "P1", "P2", "P3"]
    assert len(graph.edges) == 4
    node_data = graph.node_data("P2")
    assert (node_data["population"], node_data["votes_dem"], node_data["votes_rep"]) == (300, 30, 15)
    assert sum(graph.node_data(node)["population"] for node in graph.nodes) == 1000
    assert len(gdf) == 4

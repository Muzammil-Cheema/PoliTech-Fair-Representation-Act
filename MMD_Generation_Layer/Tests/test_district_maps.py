import json
from pathlib import Path

import pytest

gpd = pytest.importorskip("geopandas")
matplotlib = pytest.importorskip("matplotlib")
pytest.importorskip("streamlit")
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import to_hex
from shapely.geometry import MultiPolygon, Point, Polygon, box

from MMD_Generation_Layer.Client.baseline_dashboard import create_district_map
from MMD_Generation_Layer.Processor.output_artifacts import generate_district_csvs


@pytest.mark.parametrize("dissolve_districts", [True, False])
@pytest.mark.parametrize("show_precinct_lines", [True, False])
def test_map_labels_and_colors_match_district_csvs(
    tmp_path: Path, dissolve_districts: bool, show_precinct_lines: bool
) -> None:
    """Labels identify the CSV districts inside their shapes, and map fills match CSV hex codes."""
    precincts = gpd.GeoDataFrame(
        {
            "precinct_id": ["A", "B", "C", "D"],
            "population": [100, 100, 100, 100],
            "dem": [60, 40, 10, 0],
            "rep": [40, 60, 30, 0],
        },
        index=["A", "B", "C", "D"],
        geometry=[
            Polygon([(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)]),
            box(4, 0, 5, 3),
            box(5, 0, 6, 3),
            MultiPolygon([box(7, 0, 8, 2), box(10, 0, 11, 1)]),
        ],
        crs="EPSG:3857",
    ).iloc[[3, 1, 0, 2]]
    assignment = {"D": 9, "B": 4, "A": 0, "C": 4}
    plans_dir = tmp_path / "Plan_Assignments"
    plans_dir.mkdir()
    (plans_dir / "plan_1.json").write_text(json.dumps(assignment))
    generate_district_csvs(
        precincts, plans_dir, tmp_path,
        pop_col="population", dem_col="dem", rep_col="rep",
        seats_per_district={0: 3, 4: 2, 9: 3},
    )
    csv_rows = pd.read_csv(tmp_path / "districts" / "baseline_districts_plan_1.csv")
    csv_colors = csv_rows.set_index("district_id")["color"].to_dict()
    assert len(set(csv_colors.values())) == 3

    figure = create_district_map(
        precincts, assignment, plan_id=1, id_col="precinct_id",
        dissolve_districts=dissolve_districts,
        show_precinct_lines=show_precinct_lines,
    )
    try:
        axes = figure.axes[0]
        labels = {label.get_text(): label for label in axes.texts}
        assert set(labels) == {f"District {district_id}" for district_id in csv_colors}
        assert axes.get_title() == "Plan 1: District Map (3 Districts)"
        for district_id in csv_colors:
            geometry = precincts.loc[
                precincts["precinct_id"].map(assignment) == district_id, "geometry"
            ].union_all()
            assert geometry.contains(Point(labels[f"District {district_id}"].get_position()))

        fills = axes.collections[0]
        for precinct_id, precinct in precincts.iterrows():
            point = precinct.geometry.representative_point()
            rendered_colors = [
                to_hex(color)
                for path, color in zip(fills.get_paths(), fills.get_facecolors(), strict=True)
                if path.contains_point((point.x, point.y))
            ]
            assert rendered_colors == [csv_colors[assignment[precinct_id]]]
    finally:
        plt.close(figure)

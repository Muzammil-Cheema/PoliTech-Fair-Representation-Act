"""Shared project configuration for paths and immutable constants."""

from pathlib import Path

# Directories
base_dir = Path(__file__).resolve().parent
processor_dir = base_dir / "Processor"
shape_path = base_dir / "Data" / "Shapefiles" / "NC" / "nc_2024_with_population.shp"
output_dir = base_dir / "Outputs"
plans_dir = output_dir / "Plan_Assignments"

# Paths
ensemble_csv_path = output_dir / "baseline_ensemble.csv"
seat_share_png_path = output_dir / "seat_share.png"

# Global constants
NUM_PLANS = 100
NUM_DISTRICTS = 14
ID_COLUMN = "UNIQUE_ID"
GEOM_COLUMN = "the_geom"
SEED = 67676767

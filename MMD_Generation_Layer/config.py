"""Shared project configuration for paths and immutable constants."""

from pathlib import Path

# Directories
base_dir = Path(__file__).resolve().parent
processor_dir = base_dir / "Processor"
shape_path = base_dir / "Data" / "Shapefiles" / "NC" / "nc_2024_with_population.shp"
output_dir = base_dir / "Outputs"
plans_dir = output_dir / "Plan_Assignments"
intermediate_smd_plans_dir = output_dir / "Intermediate_SMD_Plans"

# Paths
ensemble_csv_path = output_dir / "baseline_ensemble.csv"
seat_share_png_path = output_dir / "seat_share.png"

# Global constants
GENERATION_MODE = "MMD"
NUM_PLANS = 50
NUM_DISTRICTS = 14
ID_COLUMN = "UNIQUE_ID"
GEOM_COLUMN = "the_geom"
SEED = 67676767
SEAT_VECTOR = (5, 5, 4)
MMD_SMD_MULTIPLIER = 10
MMD_PLANS_PER_SMD_PLAN = 5
POPULATION_TOLERANCE = 0.05
MAX_MMD_ATTEMPTS_PER_SMD_PLAN = 10
SAVE_INTERMEDIATE_SMD_PLANS = False

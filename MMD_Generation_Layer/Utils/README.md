# Utils

## population_builder.py

Reconstructs precinct-level total population (`TOTPOP`) from 2020 Census
TIGER/Line blocks. State-agnostic — works for any state given its two-digit
FIPS code and a precinct shapefile. No Census API key required; the TIGER/Line
block shapefile ships with population (`POP20`) already attached.

Two reconstruction methods are available:

- **`point`** (default, fast) — assigns each census block's population
  wholesale to whichever precinct contains the block's internal point.
- **`area`** (slower, more precise) — splits each block's population across
  every precinct it overlaps, proportional to the overlap area. Recommended
  when generating data you intend to keep, since it's meaningfully more
  accurate at precinct boundaries.

### Usage

```bash
python3 MMD_Generation_Layer/Utils/population_builder.py \
  --input <path to precinct shapefile> \
  --state-fips <two-digit state FIPS code> \
  --id-col <precinct ID column, default UNIQUE_ID> \
  --output <path to save the result> \
  --method {point,area,both} \
  [--compare-to <path to a file with known TOTPOP, to validate against>] \
  [--cache-dir <where to cache downloaded Census blocks, default Data/Census_Blocks>]
```

### Example: generate VA population data (area method)

```bash
python3 MMD_Generation_Layer/Utils/population_builder.py \
  --input "MMD_Generation_Layer/Data/Shapefiles/VA/va_2024_gen_all_prec/va_2024_gen_all_prec.shp" \
  --state-fips 51 \
  --id-col UNIQUE_ID \
  --method area \
  --output "MMD_Generation_Layer/Data/Shapefiles/VA/va_2024_with_population.shp"
```

This is the exact command used to produce
`Data/Shapefiles/VA/va_2024_with_population.shp`, matching the naming
convention of `Data/Shapefiles/NC/nc_2024_with_population.shp`.

### Comparing both methods

```bash
python3 MMD_Generation_Layer/Utils/population_builder.py \
  --input <precinct shapefile> --state-fips <fips> --method both \
  --output /tmp/comparison.shp
```

Saves `TOTPOP_point` and `TOTPOP_area_weighted` as separate columns and
prints a statewide + per-precinct diff summary.

### Validating against a known TOTPOP

```bash
python3 MMD_Generation_Layer/Utils/population_builder.py \
  --input <precinct shapefile> --state-fips <fips> \
  --output /tmp/check.shp \
  --compare-to <shapefile with an existing TOTPOP column>
```

### State FIPS codes

Two-digit FIPS codes for states currently in use: NC = `37`, VA = `51`.
Full list: https://www.census.gov/library/reference/code-lists/ansi.html

### Notes

- First run for a given state downloads and caches that state's TIGER/Line
  block shapefile under `Data/Census_Blocks/<state_fips>/` (NC ≈ 350MB,
  size varies by state). Subsequent runs reuse the cache.
- Both methods can produce warnings about census blocks that don't cleanly
  match precinct boundaries (unmatched or partially-covered blocks) — this
  reflects real gaps/overlaps in the precinct shapefile, not a bug in the
  script. Statewide totals are typically accurate to within ~0.01–0.02%
  even so; the `area` method is the more accurate of the two at precinct
  boundaries specifically.
- Population source is the 2020 Decennial Census. It will not reflect
  population growth/decline since 2020 — this can occasionally show up as a
  precinct having more 2024 votes than its 2020 population in fast-growing
  areas.

import json
from fractions import Fraction
from pathlib import Path

import pytest

from MMD_Generation_Layer.Processor.seat_allocation import (
    SEAT_ALLOCATION_METHOD,
    aggregate_district_votes,
    allocate_proxy_seats,
    democratic_vote_share,
)


@pytest.mark.parametrize(
    ("available_seats", "votes_dem", "votes_rep", "expected_dem_seats"),
    [
        pytest.param(5, 720, 280, 4, id="dem-majority"),
        pytest.param(5, 280, 720, 1, id="rep-majority"),
        pytest.param(5, 5001, 4999, 3, id="near-even-dem-lean"),
        pytest.param(5, 4999, 5001, 2, id="near-even-rep-lean"),
        pytest.param(4, 5001, 4999, 2, id="near-even-even-seats"),
        pytest.param(1, 600, 400, 1, id="single-seat-dem"),
        pytest.param(1, 400, 600, 0, id="single-seat-rep"),
        pytest.param(3, 1000, 0, 3, id="dem-sweep"),
        pytest.param(3, 0, 1000, 0, id="rep-sweep"),
    ],
)
def test_allocate_proxy_seats_rounds_seats_by_vote_share(
    available_seats: int, votes_dem: int, votes_rep: int, expected_dem_seats: int
) -> None:
    """Democrats get round(seats * share) and Republicans get the remaining seats."""
    allocation = allocate_proxy_seats(available_seats, votes_dem, votes_rep)

    assert allocation.dem_seats == expected_dem_seats
    assert allocation.rep_seats == available_seats - expected_dem_seats
    assert allocation.dem_vote_share == pytest.approx(votes_dem / (votes_dem + votes_rep))


@pytest.mark.parametrize(
    ("available_seats", "votes_dem", "votes_rep", "expected_dem_seats"),
    [
        pytest.param(1, 500, 500, 0, id="0.5-rounds-to-0"),
        pytest.param(3, 500, 500, 2, id="1.5-rounds-to-2"),
        pytest.param(5, 500, 500, 2, id="2.5-rounds-to-2"),
        pytest.param(3, 1, 5, 0, id="exact-sixth-of-3-is-0.5"),
        pytest.param(3, 5, 1, 2, id="exact-five-sixths-of-3-is-2.5"),
        pytest.param(5, 3, 7, 2, id="dem-share-0.3-of-5-is-1.5"),
    ],
)
def test_allocate_proxy_seats_rounds_exact_half_seats_to_even(
    available_seats: int, votes_dem: int, votes_rep: int, expected_dem_seats: int
) -> None:
    """Exact half seats are computed without float error and round to the even Democratic count."""
    assert available_seats * Fraction(votes_dem, votes_dem + votes_rep) % 1 == Fraction(1, 2)

    allocation = allocate_proxy_seats(available_seats, votes_dem, votes_rep)

    assert allocation.dem_seats == expected_dem_seats
    assert allocation.dem_seats + allocation.rep_seats == available_seats


@pytest.mark.parametrize(("available_seats", "expected_dem_seats"), [(1, 0), (2, 1), (3, 2), (4, 2), (5, 2)])
def test_allocate_proxy_seats_splits_zero_vote_districts_evenly(
    available_seats: int, expected_dem_seats: int
) -> None:
    """A district with no major-party votes is an even split that follows the half-seat rule."""
    allocation = allocate_proxy_seats(available_seats, 0, 0)

    assert allocation.dem_seats == expected_dem_seats
    assert allocation.rep_seats == available_seats - expected_dem_seats
    assert allocation.dem_vote_share == 0.5


def test_allocate_proxy_seats_always_totals_available_seats() -> None:
    """Every allocation across seat counts and vote splits uses exactly the available seats."""
    for available_seats in range(1, 8):
        for votes_dem in range(0, 31):
            for votes_rep in range(0, 31):
                allocation = allocate_proxy_seats(available_seats, votes_dem, votes_rep)
                assert 0 <= allocation.dem_seats <= available_seats
                assert allocation.dem_seats + allocation.rep_seats == available_seats


@pytest.mark.parametrize(
    ("available_seats", "votes_dem", "votes_rep", "message"),
    [
        (0, 10, 10, "available_seats must be at least 1"),
        (3, -1, 10, "Vote totals must be non-negative"),
        (3, 10, -1, "Vote totals must be non-negative"),
    ],
)
def test_allocate_proxy_seats_rejects_invalid_inputs(
    available_seats: int, votes_dem: int, votes_rep: int, message: str
) -> None:
    """Non-positive seat counts and negative vote totals raise a clear error."""
    with pytest.raises(ValueError, match=message):
        allocate_proxy_seats(available_seats, votes_dem, votes_rep)


def test_democratic_vote_share_is_exact() -> None:
    """The share is an exact fraction, and 1/2 when there are no major-party votes."""
    assert democratic_vote_share(1, 2) == Fraction(1, 3)
    assert democratic_vote_share(0, 0) == Fraction(1, 2)


def test_aggregate_district_votes_sums_precincts_per_district() -> None:
    """Precinct vote totals are summed per assigned district."""
    assignment = {"A": 0, "B": 0, "C": 1, "D": 2}
    votes_dem = {"A": 10, "B": 5, "C": 0, "D": 7}
    votes_rep = {"A": 1, "B": 2, "C": 0, "D": 9}

    assert aggregate_district_votes(assignment, votes_dem, votes_rep) == {
        0: (15, 3),
        1: (0, 0),
        2: (7, 9),
    }


def test_generate_district_csvs_writes_proxy_seats(tmp_path: Path) -> None:
    """District CSVs are written under districts/ with the run's proxy seat counts."""
    pd = pytest.importorskip("pandas")
    pytest.importorskip("geopandas")
    from MMD_Generation_Layer.Processor.output_artifacts import generate_district_csvs

    precincts = pd.DataFrame(
        {
            "TOTPOP": [100, 100, 100, 100],
            "DEM": [60, 40, 10, 0],
            "REP": [40, 60, 30, 0],
        },
        index=["A", "B", "C", "D"],
    )
    plans_dir = tmp_path / "Plan_Assignments"
    plans_dir.mkdir()
    (plans_dir / "plan_1.json").write_text(json.dumps({"A": 0, "B": 0, "C": 1, "D": 2}))

    generate_district_csvs(
        precincts,
        plans_dir,
        tmp_path,
        pop_col="TOTPOP",
        dem_col="DEM",
        rep_col="REP",
        seats_per_district={0: 3, 1: 2, 2: 3},
    )

    assert not (tmp_path / "baseline_districts_plan_1.csv").exists()
    rows = pd.read_csv(tmp_path / "districts" / "baseline_districts_plan_1.csv").to_dict("records")
    assert [(row["district_id"], row["seat_count"], row["dem_seats"], row["rep_seats"]) for row in rows] == [
        (0, 3, 2, 1),  # 100/200 = 0.5 share -> 1.5 seats -> 2 (half to even)
        (1, 2, 0, 2),  # 10/40 = 0.25 share -> 0.5 seats -> 0 (half to even)
        (2, 3, 2, 1),  # zero votes -> even split -> 1.5 seats -> 2
    ]
    assert {row["seat_allocation_method"] for row in rows} == {SEAT_ALLOCATION_METHOD}
    assert "winner" not in rows[0]

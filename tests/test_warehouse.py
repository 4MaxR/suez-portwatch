"""Data-quality checks on the built warehouse. Run after scripts/build_warehouse.py."""

import json

import pytest

from suez_portwatch.config import (
    DAILY_LAYERS,
    RAW_DIR,
    REF_DIR,
    ROUTE_CHOKEPOINTS,
    WAREHOUSE,
    YEARS,
)
from suez_portwatch.warehouse import connect

pytestmark = pytest.mark.skipif(not WAREHOUSE.exists(), reason="warehouse not built")


@pytest.fixture(scope="module")
def con():
    with connect(read_only=True) as c:
        yield c


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def test_every_layer_has_every_year():
    for layer in DAILY_LAYERS:
        assert sorted(int(p.stem) for p in (RAW_DIR / layer.name).glob("*.json")) == YEARS


def test_closed_years_end_on_31_december():
    for layer in DAILY_LAYERS:
        for year in YEARS[:-1]:
            rows = json.loads((RAW_DIR / layer.name / f"{year}.json").read_text(encoding="utf-8"))
            assert max(r["date"] for r in rows) == f"{year}-12-31", (layer.name, year)


def test_every_chokepoint_has_every_day(con):
    """28 chokepoints x every calendar day from 1 Jan 2019 to the last date, no gaps."""
    missing = scalar(
        con,
        """
        SELECT count(*) FROM gold.dim_date AS d
        CROSS JOIN gold.dim_chokepoint AS c
        ANTI JOIN silver.chokepoint_daily AS s USING ("date", chokepoint_id)
        """,
    )
    assert missing == 0
    assert scalar(con, "SELECT count(*) FROM gold.dim_chokepoint") == 28


def test_every_egyptian_port_has_every_day(con):
    expected_ports = len(json.loads((REF_DIR / "egypt_ports.json").read_text(encoding="utf-8")))
    missing = scalar(
        con,
        """
        SELECT count(*) FROM gold.dim_date AS d
        CROSS JOIN gold.dim_port AS p
        ANTI JOIN silver.port_daily AS s USING ("date", port_id)
        WHERE d."date" <= (SELECT max("date") FROM silver.port_daily)
        """,
    )
    assert missing == 0
    assert scalar(con, "SELECT count(DISTINCT port_id) FROM silver.port_daily") == expected_ports


@pytest.mark.parametrize(
    ("table", "key"),
    [
        ("silver.chokepoint_daily", 'chokepoint_id, "date"'),
        ("silver.port_daily", 'port_id, "date"'),
        ("gold.fact_chokepoint_transits", 'chokepoint_id, "date", vessel_type'),
        ("gold.fact_port_calls", 'port_id, "date", vessel_type'),
    ],
)
def test_keys_are_unique(con, table, key):
    dupes = scalar(
        con, f"SELECT count(*) FROM (SELECT 1 FROM {table} GROUP BY {key} HAVING count(*) > 1)"
    )
    assert dupes == 0


def test_vessel_types_reconcile_to_published_totals(con):
    """The long fact table must add back up to PortWatch's own n_total and capacity columns.

    PortWatch rounds each vessel-type tonnage to whole tonnes, so five rounded parts can differ
    from the rounded total by a few tonnes on a day that carries millions.
    """
    worst = con.execute(
        """
        SELECT max(abs(f.transits - s.transits_total)),
               max(abs(f.volume_t - s.volume_total_t))
        FROM (SELECT "date", chokepoint_id, sum(transits) AS transits, sum(volume_t) AS volume_t
              FROM gold.fact_chokepoint_transits GROUP BY ALL) AS f
        JOIN silver.chokepoint_daily AS s USING ("date", chokepoint_id)
        """
    ).fetchone()
    assert worst[0] == 0
    assert worst[1] <= 5


def test_port_calls_reconcile_to_published_totals(con):
    worst = scalar(
        con,
        """
        SELECT max(abs(f.calls - s.calls_total))
        FROM (SELECT "date", port_id, sum(port_calls) AS calls
              FROM gold.fact_port_calls GROUP BY ALL) AS f
        JOIN silver.port_daily AS s USING ("date", port_id)
        """,
    )
    assert worst == 0


def test_counts_and_volumes_are_non_negative(con):
    assert (
        scalar(
            con,
            "SELECT count(*) FROM gold.fact_chokepoint_transits WHERE transits < 0 OR volume_t < 0",
        )
        == 0
    )
    assert (
        scalar(
            con,
            "SELECT count(*) FROM gold.fact_port_calls "
            "WHERE port_calls < 0 OR import_t < 0 OR export_t < 0",
        )
        == 0
    )


def test_suez_never_reports_a_zero_day(con):
    """A day with zero Suez transits would mean an AIS outage, not a closed canal."""
    zero = scalar(
        con,
        f"""
        SELECT count(*) FROM silver.chokepoint_daily
        WHERE chokepoint_id IN ({", ".join(f"'{c}'" for c in ROUTE_CHOKEPOINTS)})
          AND transits_total = 0
        """,
    )
    assert zero == 0


def test_periods_are_fully_covered(con):
    """Each analysis period has data on every one of its days at Suez."""
    gaps = con.execute(
        """
        SELECT p.period
        FROM gold.dim_period AS p
        JOIN silver.chokepoint_daily AS s
          ON s.chokepoint_id = 'chokepoint1' AND s."date" BETWEEN p.start_date AND p.end_date
        GROUP BY p.period, p.start_date, p.end_date
        HAVING count(*) <> date_diff('day', p.start_date, p.end_date) + 1
        """
    ).fetchall()
    assert gaps == []

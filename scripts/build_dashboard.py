"""Step 4: export dashboard data from the warehouse and render docs/dashboard.html.

The template (scripts/dashboard_template.html) holds page content only. Two files are written:
  docs/dashboard.html           standalone page with its own <!doctype> (GitHub Pages)
  outputs/dashboard_body.html   the same page without the document wrapper (artifact publish)
"""

import json
import math
from datetime import date

from suez_portwatch.config import (
    DAILY_LAYERS,
    EVENTS,
    LATEST_WINDOW_DAYS,
    RAW_DIR,
    ROOT,
    ROUTE_CHOKEPOINTS,
    SCA_REVENUE_2023_USD,
    SCA_REVENUE_2024_USD,
    SCA_TRANSITS_2023,
    SCA_TRANSITS_2024,
    YEARS,
)
from suez_portwatch.warehouse import analysis_queries, connect, query

TEMPLATE = ROOT / "scripts" / "dashboard_template.html"
PAGE = ROOT / "docs" / "dashboard.html"
BODY = ROOT / "outputs" / "dashboard_body.html"

SHORT = {
    "Suez Canal": "Suez",
    "Bab el-Mandeb Strait": "Bab el-Mandeb",
    "Cape of Good Hope": "Cape of Good Hope",
    "Gibraltar Strait": "Gibraltar",
    "Malacca Strait": "Malacca",
}
KEY = {
    "chokepoint1": "suez",
    "chokepoint4": "bab",
    "chokepoint7": "cape",
    "chokepoint8": "gib",
    "chokepoint5": "mal",
}


def clean(v):
    """JSON-safe scalar: NaN -> None, numpy -> python, dates -> ISO strings."""
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()[:10]
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def records(df):
    return [{k: clean(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


def main() -> None:
    q = {f.stem: query(f) for f in analysis_queries()}

    with connect(read_only=True) as con:
        counts = dict(
            con.execute(
                "SELECT 'chokepoint', count(*) FROM silver.chokepoint_daily "
                "UNION ALL SELECT 'port', count(*) FROM silver.port_daily"
            ).fetchall()
        )
        gold_tables = con.execute(
            "SELECT count(*) FROM duckdb_tables() WHERE schema_name = 'gold'"
        ).fetchone()[0]
        fact_rows = con.execute(
            "SELECT (SELECT count(*) FROM gold.fact_chokepoint_transits)"
            " + (SELECT count(*) FROM gold.fact_port_calls)"
        ).fetchone()[0]
        last_choke, last_port, extracted = con.execute(
            'SELECT (SELECT max("date") FROM silver.chokepoint_daily),'
            ' (SELECT max("date") FROM silver.port_daily),'
            " (SELECT max(extracted_at)::DATE FROM silver.chokepoint_daily)"
        ).fetchone()
        dupes = con.execute(
            """
            SELECT (SELECT count(*) FROM (SELECT 1 FROM silver.chokepoint_daily
                    GROUP BY chokepoint_id, "date" HAVING count(*) > 1))
                 + (SELECT count(*) FROM (SELECT 1 FROM silver.port_daily
                    GROUP BY port_id, "date" HAVING count(*) > 1))
            """
        ).fetchone()[0]
        missing_days = con.execute(
            """
            SELECT count(*) FROM gold.dim_date CROSS JOIN gold.dim_chokepoint
            ANTI JOIN silver.chokepoint_daily USING ("date", chokepoint_id)
            """
        ).fetchone()[0]
        periods = records(con.execute("SELECT * FROM gold.dim_period ORDER BY sort_order").df())
        port_coast_monthly = con.execute(
            """
            SELECT p.coast, d.month_start,
                   sum(f.port_calls) / count(DISTINCT f."date") AS calls,
                   sum(f.port_calls) FILTER (WHERE f.vessel_type = 'container')
                       / count(DISTINCT f."date") AS box_calls,
                   count(DISTINCT f."date") < 20 AS is_partial
            FROM gold.fact_port_calls f
            JOIN gold.dim_port p USING (port_id)
            JOIN gold.dim_date d USING ("date")
            GROUP BY ALL ORDER BY p.coast, d.month_start
            """
        ).df()

    # Monthly series on one shared month axis (full months only).
    monthly = q["03_monthly_routes"]
    monthly = monthly[~monthly.is_partial]
    months = sorted({m.isoformat()[:7] for m in monthly.month_start})
    routes = {}
    for cid in ROUTE_CHOKEPOINTS:
        g = monthly[monthly.chokepoint_id == cid].copy()
        g["m"] = [m.isoformat()[:7] for m in g.month_start]
        g = g.set_index("m").reindex(months)
        routes[KEY[cid]] = {
            "name": SHORT[g.chokepoint_name.dropna().iloc[0]],
            "transits": [clean(v) for v in g.transits_per_day],
            "volume": [clean(v) for v in g.volume_t_per_day],
        }

    coast = {}
    pcm = port_coast_monthly[~port_coast_monthly.is_partial].copy()
    pcm["m"] = [m.isoformat()[:7] for m in pcm.month_start]
    for name, g in pcm.groupby("coast"):
        g = g.set_index("m").reindex(months)
        coast[name] = {
            "calls": [clean(v) for v in g.calls],
            "box": [clean(v) for v in g.box_calls],
        }

    route_periods = q["02_route_shift"].copy()
    route_periods["chokepoint_name"] = route_periods.chokepoint_name.map(SHORT)

    dq = q["09_data_quality"]
    raw_files = len(list(RAW_DIR.glob("*/*.json")))
    data = {
        "months": months,
        "events": [{"date": d.isoformat(), "label": label} for d, label in EVENTS],
        "periods": periods,
        "meta": {
            "built": date.today().isoformat(),
            "extracted": clean(extracted),
            "last_chokepoint_date": clean(last_choke),
            "last_port_date": clean(last_port),
            "first_year": YEARS[0],
            "raw_files": raw_files,
            "silver_rows": int(sum(counts.values())),
            "chokepoint_rows": int(counts["chokepoint"]),
            "port_rows": int(counts["port"]),
            "fact_rows": int(fact_rows),
            "gold_tables": int(gold_tables),
            "latest_window_days": LATEST_WINDOW_DAYS,
            "layers": [
                {"name": lay.name, "service": lay.service, "description": lay.description}
                for lay in DAILY_LAYERS
            ],
            "sca": {
                "revenue_2023": SCA_REVENUE_2023_USD,
                "revenue_2024": SCA_REVENUE_2024_USD,
                "transits_2023": SCA_TRANSITS_2023,
                "transits_2024": SCA_TRANSITS_2024,
            },
            "checks": {
                "duplicates": int(dupes),
                "missing_chokepoint_days": int(missing_days),
                "route_zero_days": int(dq[dq.layer == "chokepoint"].zero_days.sum()),
                "count_mismatch_days": int(dq.count_mismatch_days.sum()),
                "max_volume_gap_t": float(dq.max_volume_gap_t.max()),
                "port_coverage": float(dq[dq.layer == "port"].coverage.min()),
            },
        },
        "decline": records(q["01_suez_decline"]),
        "route_periods": records(route_periods),
        "routes": routes,
        "vessel": records(q["04_vessel_mix"]),
        "annual": records(q["05_suez_annual_proxy"]),
        "lost": records(q["06_lost_transits"]),
        "ports": records(q["07_egypt_ports"]),
        "coast": coast,
        "quality": records(dq),
        "outliers": records(
            q["10_outlier_days"]
            .query("chokepoint_name == 'Suez Canal'")
            .sort_values("date")
            .assign(chokepoint_name=lambda d: d.chokepoint_name.map(SHORT))
        ),
        "outlier_counts": {
            SHORT[k]: int(v) for k, v in q["10_outlier_days"].chokepoint_name.value_counts().items()
        },
    }

    body = TEMPLATE.read_text(encoding="utf-8").replace(
        "/*__DATA__*/null", json.dumps(data, separators=(",", ":"))
    )
    BODY.parent.mkdir(parents=True, exist_ok=True)
    BODY.write_text(body, encoding="utf-8")
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        "</head>\n<body>\n" + body + "\n</body>\n</html>\n",
        encoding="utf-8",
    )
    print(f"dashboard -> {PAGE.relative_to(ROOT)} ({PAGE.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()

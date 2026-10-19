"""Step 3: run sql/analysis queries; save CSVs to outputs/tables, figures to outputs/charts."""

from suez_portwatch import charts
from suez_portwatch.config import CHART_DIR, TABLE_DIR
from suez_portwatch.warehouse import analysis_queries, connect, query

TABLE_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

results = {}
with connect(read_only=True) as con:
    for sql_file in analysis_queries():
        df = query(sql_file, con)
        df.to_csv(TABLE_DIR / f"{sql_file.stem}.csv", index=False)
        results[sql_file.stem] = df
        print(f"{sql_file.stem:<28} {len(df):>5} rows")

charts.suez_transits(
    results["03_monthly_routes"], results["01_suez_decline"], CHART_DIR / "suez_transits.png"
)
charts.route_shift(results["03_monthly_routes"], CHART_DIR / "route_shift.png")
charts.vessel_mix(results["04_vessel_mix"], CHART_DIR / "vessel_mix.png")
charts.revenue_proxy(results["05_suez_annual_proxy"], CHART_DIR / "revenue_proxy.png")
charts.egypt_ports(results["07_egypt_ports"], CHART_DIR / "egypt_ports.png")
print(f"charts -> {CHART_DIR}")

"""Build the DuckDB warehouse from data/raw and run the analysis queries."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from .config import (
    LATEST_WINDOW_DAYS,
    PERIODS,
    RAW_DIR,
    REF_DIR,
    SCA_REVENUE_2023_USD,
    SCA_TRANSITS_2023,
    SQL_DIR,
    WAREHOUSE,
)

LAYERS = ["bronze", "silver", "gold"]


def _params() -> dict[str, str]:
    params = {
        "raw_dir": RAW_DIR.as_posix(),
        "ref_dir": REF_DIR.as_posix(),
        "latest_window_days": str(LATEST_WINDOW_DAYS),
        "sca_revenue_2023_usd": repr(SCA_REVENUE_2023_USD),
        "sca_transits_2023": str(SCA_TRANSITS_2023),
    }
    for name, (start, end) in PERIODS.items():
        params[f"{name}_start"] = start.isoformat()
        params[f"{name}_end"] = end.isoformat()
    return params


def _render(sql_file: Path) -> str:
    return sql_file.read_text(encoding="utf-8").format(**_params())


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(WAREHOUSE), read_only=read_only)


def build() -> None:
    """Run every bronze, silver and gold script in file-name order."""
    WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        for layer in LAYERS:
            for sql_file in sorted((SQL_DIR / layer).glob("*.sql")):
                con.execute(_render(sql_file))
                print(f"built  {layer}/{sql_file.name}")
        for schema, table, rows in con.execute(
            """
            SELECT schema_name, table_name, estimated_size
            FROM duckdb_tables() WHERE schema_name IN ('silver', 'gold')
            ORDER BY schema_name, table_name
            """
        ).fetchall():
            print(f"  {schema}.{table:<26} {rows:>8,} rows")


def analysis_queries() -> list[Path]:
    return sorted((SQL_DIR / "analysis").glob("*.sql"))


def query(sql_or_file: str | Path, con: duckdb.DuckDBPyConnection | None = None) -> pd.DataFrame:
    sql = _render(Path(sql_or_file)) if isinstance(sql_or_file, Path) else sql_or_file
    if con is not None:
        return con.execute(sql).df()
    with connect(read_only=True) as own:
        return own.execute(sql).df()

"""Project-wide constants: paths, the study window, the PortWatch layers and the periods."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
REF_DIR = ROOT / "data" / "reference"
WAREHOUSE = ROOT / "data" / "suez_portwatch.duckdb"
SQL_DIR = ROOT / "sql"
CHART_DIR = ROOT / "outputs" / "charts"
TABLE_DIR = ROOT / "outputs" / "tables"

FIRST_YEAR = 2019
YEARS = list(range(FIRST_YEAR, date.today().year + 1))

# IMF PortWatch publishes its datasets as public ArcGIS FeatureServer layers (no key, no sign-in).
SERVICES = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services"


@dataclass(frozen=True)
class Layer:
    """One PortWatch daily layer, downloaded one calendar year per file."""

    name: str
    service: str
    where: str
    description: str


DAILY_LAYERS = [
    Layer(
        "chokepoint_transits",
        "Daily_Chokepoints_Data",
        "1=1",
        "Daily transit calls and estimated trade volume (t) for all 28 PortWatch chokepoints",
    ),
    Layer(
        "egypt_port_calls",
        "Daily_Ports_Data",
        "portid IN ({egypt_port_ids})",  # ISO3 is not indexed on this layer; portid is
        "Daily port calls and estimated import/export volume (t) for every Egyptian port",
    ),
]

REFERENCE_LAYERS = {
    "chokepoints": ("PortWatch_chokepoints_database", "1=1"),
    "egypt_ports": ("PortWatch_ports_database", "ISO3 = 'EGY'"),
}

# Chokepoints on the Asia-Europe route. Malacca is the control: it sits upstream of the
# diversion, so it shows whether trade itself fell or only the route changed.
SUEZ = "chokepoint1"
BAB_EL_MANDEB = "chokepoint4"
CAPE = "chokepoint7"
GIBRALTAR = "chokepoint8"
MALACCA = "chokepoint5"
ROUTE_CHOKEPOINTS = [SUEZ, BAB_EL_MANDEB, CAPE, GIBRALTAR, MALACCA]

# Periods used by every analysis query (inclusive dates). The baseline is the ten months of
# 2023 before the first Houthi attack on merchant shipping (Galaxy Leader, 19 Nov 2023).
PERIODS = {
    "baseline": (date(2023, 1, 1), date(2023, 10, 31)),
    "crisis_2024": (date(2024, 1, 1), date(2024, 12, 31)),
    "year_2025": (date(2025, 1, 1), date(2025, 12, 31)),
}
LATEST_WINDOW_DAYS = 90  # the "latest" period is the last 90 days with data

# Context markers for charts. These dates come from news reporting, not from PortWatch.
EVENTS = [
    (date(2023, 11, 19), "Galaxy Leader seized"),
    (date(2023, 12, 15), "Major container lines pause Red Sea"),
    (date(2025, 1, 19), "Gaza ceasefire; attacks pause"),
    (date(2025, 7, 7), "Two bulk carriers sunk"),
    (date(2025, 10, 10), "Gaza ceasefire"),
]

# Suez Canal Authority figures from its public statements (calendar years). 2023 turns the
# PortWatch tonnage index into an illustrative revenue figure; 2024 is held back as a check.
SCA_REVENUE_2023_USD = 10.25e9
SCA_TRANSITS_2023 = 26_434
SCA_REVENUE_2024_USD = 3.991e9
SCA_TRANSITS_2024 = 13_213

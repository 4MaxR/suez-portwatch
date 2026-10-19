"""Static README figures (matplotlib). One chart per analysis question.

Colour roles stay fixed across every chart and the dashboard: Suez = canal teal, Bab el-Mandeb
= coral, Cape of Good Hope = kelp green, so a reader learns the encoding once.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.dates as mdates

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .config import EVENTS, SCA_REVENUE_2023_USD, SCA_REVENUE_2024_USD  # noqa: E402

SURFACE = "#f7f9fa"
INK = "#0b1d2a"
INK_2 = "#4b5d6b"
GRID = "#dfe5e9"
ROUTE = {
    "Suez Canal": "#0b7a8a",
    "Bab el-Mandeb Strait": "#e2603f",
    "Cape of Good Hope": "#3f8f3a",
    "Gibraltar Strait": "#7b62c9",
    "Malacca Strait": "#9aa6b0",
}
VESSEL = {
    "Container": "#0b7a8a",
    "Dry bulk": "#b8873a",
    "Tanker": "#b43f3f",
    "General cargo": "#5f86ad",
    "Ro-ro": "#7b62c9",
}
COAST = {"Mediterranean": "#0b7a8a", "Gulf of Suez": "#e2603f", "Red Sea": "#b8873a"}
MUTED = "#b9c3ca"

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK_2,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "ytick.left": False,
        "font.size": 10,
        "lines.linewidth": 2,
        "legend.frameon": False,
        "text.parse_math": False,
        "axes.titlepad": 24,
    }
)

SOURCE = "Source: IMF PortWatch (AIS-based estimates), daily data aggregated to months."


def _finish(fig: plt.Figure, ax: plt.Axes, path: Path, subtitle: str, source: str = SOURCE):
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=INK_2, fontsize=9.5, va="bottom")
    ax.tick_params(axis="x", length=0)
    fig.text(0.01, 0.01, source, color=INK_2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _monthly(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Full months only: a few days of the current month would read as a trend."""
    out = df[(df.chokepoint_name == name) & ~df.is_partial].copy()
    out["month_start"] = pd.to_datetime(out["month_start"])
    return out


def _time_axis(ax: plt.Axes, right_pad_days: int = 0) -> None:
    ax.set_xlim(
        pd.Timestamp("2018-12-01"), pd.Timestamp("2026-12-31") + pd.Timedelta(days=right_pad_days)
    )
    ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2019, 2027)])
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def suez_transits(monthly: pd.DataFrame, decline: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.8))
    suez = _monthly(monthly, "Suez Canal")
    base = decline.set_index("period").loc["baseline", "transits_per_day"]
    ax.axvspan(pd.Timestamp("2023-11-19"), suez.month_start.max(), color="#e2603f", alpha=0.06)
    ax.axhline(base, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(
        pd.Timestamp("2019-01-15"),
        base + 1.5,
        f"Jan–Oct 2023 baseline: {base:.0f}/day",
        color=INK_2,
        fontsize=9,
    )
    ax.plot(suez.month_start, suez.transits_per_day, color=ROUTE["Suez Canal"], linewidth=2.4)
    first_attack = EVENTS[0]
    ax.axvline(pd.Timestamp(first_attack[0]), color=INK_2, linewidth=1, linestyle=":")
    ax.text(
        pd.Timestamp(first_attack[0]) + pd.Timedelta(days=20),
        82,
        "First attack\n19 Nov 2023",
        color=INK,
        fontsize=9,
        va="top",
    )
    last = suez.iloc[-1]
    ax.annotate(
        f"{last.transits_per_day:.0f}/day",
        (last.month_start, last.transits_per_day),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        color=INK,
        fontsize=9.5,
    )
    ax.set_ylim(0, 85)
    _time_axis(ax)
    ax.set_title("Suez Canal transits fell by almost half and have not come back")
    ax.set_ylabel("Ships per day (monthly average)")
    _finish(
        fig,
        ax,
        path,
        "Daily transits through the Suez Canal, all cargo ship types. "
        "The shaded area is the period since the first Houthi attack on merchant shipping.",
    )


def route_shift(monthly: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for name in ["Suez Canal", "Bab el-Mandeb Strait", "Cape of Good Hope"]:
        d = _monthly(monthly, name)
        ax.plot(d.month_start, d.transits_per_day, color=ROUTE[name], linewidth=2.2)
        last = d.iloc[-1]
        ax.annotate(
            f"{name.replace(' Strait', '')} {last.transits_per_day:.0f}",
            (last.month_start, last.transits_per_day),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            color=ROUTE[name],
            fontsize=9.5,
            fontweight="bold",
        )
    ax.axvline(pd.Timestamp(EVENTS[0][0]), color=INK_2, linewidth=1, linestyle=":")
    ax.set_ylim(0, 110)
    _time_axis(ax, right_pad_days=330)
    ax.set_title("Traffic swapped the Red Sea for the Cape of Good Hope")
    ax.set_ylabel("Ships per day (monthly average)")
    _finish(
        fig,
        ax,
        path,
        "Daily transits at the two ends of the Red Sea route and at the Cape. "
        "The dotted line marks 19 Nov 2023.",
    )


def vessel_mix(mix: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.4))
    d = mix.iloc[::-1].reset_index(drop=True)
    yy = range(len(d))
    ax.barh(
        [y + 0.18 for y in yy],
        d.transits_change_2024 * 100,
        height=0.34,
        color=[VESSEL[v] for v in d.vessel_label],
        label="Ships per day",
    )
    ax.barh(
        [y - 0.18 for y in yy],
        d.volume_change_2024 * 100,
        height=0.34,
        color=[VESSEL[v] for v in d.vessel_label],
        alpha=0.45,
        label="Estimated tonnes per day",
    )
    for y, (t, v) in enumerate(zip(d.transits_change_2024, d.volume_change_2024, strict=True)):
        ax.text(
            t * 100 - 1.5,
            y + 0.18,
            f"{t * 100:.0f}%",
            va="center",
            ha="right",
            fontsize=9,
            color=INK,
        )
        ax.text(
            v * 100 - 1.5,
            y - 0.18,
            f"{v * 100:.0f}%",
            va="center",
            ha="right",
            fontsize=9,
            color=INK_2,
        )
    ax.set_yticks(list(yy), d.vessel_label)
    ax.set_xlim(-105, 0)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_title("Container ships and car carriers left first; tankers and bulkers held on more")
    _finish(
        fig,
        ax,
        path,
        "Change in Suez Canal daily transits (solid) and estimated cargo tonnes "
        "(light) in 2024, against Jan–Oct 2023.",
    )


def revenue_proxy(annual: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.6))
    years = annual.year.astype(int)
    vals = annual.revenue_proxy_usd_annualised / 1e9
    colors = [ROUTE["Suez Canal"] if y < 2024 else "#e2603f" for y in years]
    bars = ax.bar(years, vals, color=colors, width=0.62)
    for bar, partial in zip(bars, annual.is_partial_year, strict=True):
        if partial:
            bar.set_hatch("///")
            bar.set_alpha(0.7)
    for y, v, partial in zip(years, vals, annual.is_partial_year, strict=True):
        ax.text(
            y,
            v + 0.35,
            f"${v:.1f}bn" + ("*" if partial else ""),
            ha="center",
            fontsize=9.5,
            color=INK,
        )
    ax.scatter(
        [2023, 2024],
        [SCA_REVENUE_2023_USD / 1e9, SCA_REVENUE_2024_USD / 1e9],
        marker="D",
        s=44,
        color=INK,
        zorder=3,
        label="SCA-reported revenue",
    )
    ax.legend(loc="upper left", fontsize=9)
    ax.set_xticks(list(years))
    ax.set_ylim(0, 12)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:.0f}bn")
    ax.set_title("A tonnage-based proxy puts canal revenue near $4bn a year since 2024")
    _finish(
        fig,
        ax,
        path,
        "SCA's 2023 revenue scaled by PortWatch's Suez tonnage index. "
        "Diamonds: SCA-reported revenue. *2026 annualised.",
        "Source: IMF PortWatch; Suez Canal Authority statements (2023, 2024 revenue).",
    )


def egypt_ports(ports: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.8))
    d = ports.sort_values("calls_change_latest").reset_index(drop=True)
    vals = d.calls_change_latest * 100
    ax.barh(d.port_name, vals, color=[COAST[c] for c in d.coast], height=0.6)
    for y, (v, base, now) in enumerate(zip(vals, d.baseline_calls, d.latest_calls, strict=True)):
        ax.text(
            v + (2 if v >= 0 else -2),
            y,
            f"{v:+.0f}%  ({base:.1f} → {now:.1f}/day)",
            va="center",
            ha="left" if v >= 0 else "right",
            fontsize=9,
            color=INK,
        )
    ax.axvline(0, color=INK_2, linewidth=1)
    ax.set_xlim(-100, 230)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:+.0f}%")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in COAST.values()]
    ax.legend(handles, list(COAST), loc="lower right", fontsize=9)
    ax.set_title("El Sokhna's port calls nearly tripled; the Mediterranean ports held or slipped")
    _finish(
        fig,
        ax,
        path,
        "Change in port calls per day at Egypt's main ports, latest 90 days "
        "against Jan–Oct 2023. Colour shows the coast.",
        "Source: IMF PortWatch (AIS-based port calls). Ports under one call a week omitted.",
    )

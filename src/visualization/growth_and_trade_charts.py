"""Static charts proving the core thesis:
Turkey has closed the production gap with Spain, but not the trade gap.

Produces three PNGs in outputs/figures/combined/:
  1. indexed_growth.png       - FAOSTAT production, rebased to 100 at first shared year
  2. self_sufficiency.png     - IOC export share of production, Spain vs Turkey
  3. volatility_heartbeat.png - year-over-year % change, Spain vs Turkey (alternate bearing)
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SPAIN_COLOR = "#c0392b"
TURKEY_COLOR = "#e67e22"


def find_project_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    raise FileNotFoundError("Project root could not be found.")


def load_data(root):
    faostat = pd.read_csv(root / "data" / "processed" / "faostat_clean.csv")
    ioc = pd.read_csv(root / "data" / "processed" / "ioc_clean.csv")
    faostat = faostat[faostat["country"].isin(["Spain", "Türkiye"])].copy()
    ioc = ioc[ioc["country"].isin(["Spain", "Türkiye"])].copy()
    return faostat, ioc


def chart_absolute_scale(faostat, ioc, out_dir):
    """Absolute tonnage, log scale: production (FAOSTAT) vs exports (IOC).

    Deliberately NOT indexed to a base year -- Turkey's 1990 export base is
    so small (10,000t) that ordinary volatility reads as 1000%+ swings and
    drowns out the real comparison. Log-scale absolute tonnage keeps both
    countries' true scale visible and comparable.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=False)

    for country, color in [("Spain", SPAIN_COLOR), ("Türkiye", TURKEY_COLOR)]:
        f = faostat[faostat.country == country].sort_values("year")
        axes[0].plot(f["year"], f["production_tonnes"], color=color, linewidth=2.5, label=country)

        o = ioc[ioc.country == country].sort_values("crop_year_start")
        axes[1].plot(o["crop_year_start"], o["exports_tonnes"], color=color, linewidth=2.5, label=country)

    axes[0].set_yscale("log")
    axes[0].set_title("Olive Fruit Production\n(FAOSTAT, 1961-2024)", fontsize=13, fontweight="bold")
    axes[0].set_ylabel("Tonnes (log scale)")
    axes[0].legend(fontsize=10)
    axes[0].grid(alpha=0.25, which="both")

    axes[1].set_yscale("log")
    axes[1].set_title("Olive Oil Exports\n(IOC, 1990-2024)", fontsize=13, fontweight="bold")
    axes[1].set_ylabel("Tonnes (log scale)")
    axes[1].legend(fontsize=10)
    axes[1].grid(alpha=0.25, which="both")

    fig.suptitle("Scale Isn't the Whole Story — But It's Most of It", fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(out_dir / "absolute_scale.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_self_sufficiency(ioc, out_dir):
    """Export share of production: exports / production, by year."""
    fig, ax = plt.subplots(figsize=(9.5, 6))
    for country, color in [("Spain", SPAIN_COLOR), ("Türkiye", TURKEY_COLOR)]:
        o = ioc[ioc.country == country].sort_values("crop_year_start").copy()
        o = o[o["production_tonnes"] > 0]
        o["export_share"] = o["exports_tonnes"] / o["production_tonnes"] * 100
        ax.plot(o["crop_year_start"], o["export_share"], color=color, linewidth=2.5, label=country)

    ax.set_title("Export Share of Production\nWhat fraction of the olive oil each country makes, it sells abroad",
                  fontsize=14, fontweight="bold")
    ax.set_xlabel("Crop year (starting)")
    ax.set_ylabel("Exports as % of production")
    ax.legend(fontsize=10)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "self_sufficiency.png", dpi=200)
    plt.close(fig)


def chart_volatility(faostat, out_dir):
    """Year-over-year % change in production -- the alternate-bearing heartbeat."""
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 7), sharex=True)
    for ax, (country, color) in zip(axes, [("Spain", SPAIN_COLOR), ("Türkiye", TURKEY_COLOR)]):
        f = faostat[faostat.country == country].sort_values("year").copy()
        f["pct_change"] = f["production_tonnes"].pct_change() * 100
        colors = [SPAIN_COLOR if v >= 0 else "#7f8c8d" for v in f["pct_change"]] if country == "Spain" \
            else [TURKEY_COLOR if v >= 0 else "#7f8c8d" for v in f["pct_change"]]
        ax.bar(f["year"], f["pct_change"], color=colors, width=0.8)
        ax.axhline(0, color="black", linewidth=0.6)
        ax.set_ylabel(f"{country}\nYoY % change")
        ax.grid(alpha=0.2, axis="y")
        std = f["pct_change"].std()
        ax.text(0.02, 0.92, f"volatility (σ) = {std:.1f} pts", transform=ax.transAxes,
                fontsize=10, fontweight="bold", va="top")

    axes[0].set_title("The Alternate-Bearing Heartbeat\nYear-over-year swing in olive production",
                       fontsize=14, fontweight="bold")
    axes[1].set_xlabel("Year")
    fig.tight_layout()
    fig.savefig(out_dir / "volatility_heartbeat.png", dpi=200)
    plt.close(fig)


def build():
    root = find_project_root()
    faostat, ioc = load_data(root)
    out_dir = root / "outputs" / "figures" / "combined"
    out_dir.mkdir(parents=True, exist_ok=True)

    chart_absolute_scale(faostat, ioc, out_dir)
    chart_self_sufficiency(ioc, out_dir)
    chart_volatility(faostat, out_dir)
    print(f"Wrote 3 charts to {out_dir}")


if __name__ == "__main__":
    build()

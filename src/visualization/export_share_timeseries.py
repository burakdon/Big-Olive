"""Is the Italy/Tunisia/Greece export-share gap persistent or recent?
Line chart, export share of production over time, 1990-2024.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

COLORS = {
    "Italy": "#2d6a4f",
    "Tunisia": "#9c6644",
    "Greece": "#1d3557",
    "Spain": "#c0392b",
}


def find_project_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    raise FileNotFoundError("Project root could not be found.")


def build():
    root = find_project_root()
    ioc = pd.read_csv(root / "data" / "processed" / "ioc_all_countries.csv")
    ioc = ioc[ioc.country.isin(COLORS.keys())].copy()
    ioc = ioc[ioc.production_tonnes > 0]
    ioc["export_share"] = ioc.exports_tonnes / ioc.production_tonnes * 100
    ioc = ioc.sort_values("crop_year_start")

    fig, ax = plt.subplots(figsize=(10, 6.5))
    for country, color in COLORS.items():
        sub = ioc[ioc.country == country]
        # 3-yr rolling mean to smooth alternate-bearing noise, raw as faint background
        ax.plot(sub.crop_year_start, sub.export_share, color=color, alpha=0.2, linewidth=1)
        roll = sub.set_index("crop_year_start")["export_share"].rolling(3, center=True, min_periods=1).mean()
        ax.plot(roll.index, roll.values, color=color, linewidth=2.5, label=country)

    ax.set_title("Is This New? Export Share of Production, 1990-2024\n(3-year rolling average; faint lines show raw annual values)",
                  fontsize=13.5, fontweight="bold")
    ax.set_xlabel("Crop year")
    ax.set_ylabel("Exports as % of production")
    ax.legend(fontsize=10)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out_dir = root / "outputs" / "figures" / "combined"
    fig.savefig(out_dir / "export_share_timeseries.png", dpi=200)
    plt.close(fig)
    print("Wrote export_share_timeseries.png")


if __name__ == "__main__":
    build()

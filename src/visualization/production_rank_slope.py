"""Slope chart: production rank in 1990 vs 2024, all FAOSTAT-reporting countries.
Static backup visual -- who moved up/down in the growing leaderboard over 34 years.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HIGHLIGHT = {
    "Italy": "#2d6a4f",
    "Tunisia": "#9c6644",
    "Greece": "#1d3557",
    "Spain": "#c0392b",
    "Türkiye": "#e67e22",
}
NEUTRAL = "#b0b0b0"


def find_project_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    raise FileNotFoundError("Project root could not be found.")


def build():
    root = find_project_root()
    fao = pd.read_csv(root / "data" / "processed" / "faostat_all_countries.csv")

    y1990 = fao[fao.year == 1990].set_index("country")["production_tonnes"]
    y2023 = fao[fao.year == 2023].set_index("country")["production_tonnes"]
    df = pd.DataFrame({"p1990": y1990, "p2023": y2023}).dropna()
    df["rank1990"] = df.p1990.rank(ascending=False, method="min")
    df["rank2023"] = df.p2023.rank(ascending=False, method="min")

    keep = df[(df.rank1990 <= 15) | (df.rank2023 <= 15)]

    fig, ax = plt.subplots(figsize=(9, 10))
    for country, row in keep.iterrows():
        color = HIGHLIGHT.get(country, NEUTRAL)
        lw = 3 if country in HIGHLIGHT else 1
        alpha = 1.0 if country in HIGHLIGHT else 0.4
        z = 5 if country in HIGHLIGHT else 2
        ax.plot([0, 1], [row.rank1990, row.rank2023], color=color, linewidth=lw, alpha=alpha,
                marker="o", markersize=5, zorder=z)
        weight = "bold" if country in HIGHLIGHT else "normal"
        ax.text(-0.03, row.rank1990, country, ha="right", va="center", fontsize=9.5, color=color if country in HIGHLIGHT else "#555", fontweight=weight)
        ax.text(1.03, row.rank2023, country, ha="left", va="center", fontsize=9.5, color=color if country in HIGHLIGHT else "#555", fontweight=weight)

    ax.invert_yaxis()
    ax.set_xlim(-0.6, 1.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["1990", "2023"], fontsize=12, fontweight="bold")
    ax.set_yticks([])
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.set_title("The Growing Leaderboard, 34 Years Later\nRank by olive fruit production (FAOSTAT)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    out_dir = root / "outputs" / "figures" / "faostat"
    fig.savefig(out_dir / "production_rank_slope.png", dpi=200)
    plt.close(fig)
    print("Wrote production_rank_slope.png")


if __name__ == "__main__":
    build()

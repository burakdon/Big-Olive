"""Charts proving the core thesis: Italy gets outsized credit/market presence
in olive oil relative to how much it actually produces, while countries like
Greece and Tunisia produce comparably or more and stay invisible.

Uses IOC all-countries data (production, exports, imports, consumption),
2015-2024 average, all reporting countries.

Produces three PNGs in outputs/figures/combined/:
  1. production_vs_exports_scatter.png - log-log scatter + trend line, outliers labeled
  2. rank_bump_chart.png                - production rank vs export rank, country lines
  3. supply_gap_bar.png                 - unexplained supply gap by country
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ITALY_COLOR = "#2d6a4f"
GREECE_COLOR = "#1d3557"
TUNISIA_COLOR = "#9c6644"
SPAIN_COLOR = "#c0392b"
TURKEY_COLOR = "#e67e22"
NEUTRAL = "#95a5a6"

HIGHLIGHT_COLORS = {
    "Italy": ITALY_COLOR,
    "Greece": GREECE_COLOR,
    "Tunisia": TUNISIA_COLOR,
    "Spain": SPAIN_COLOR,
    "Türkiye": TURKEY_COLOR,
}


def find_project_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    raise FileNotFoundError("Project root could not be found.")


def load_agg(root):
    ioc = pd.read_csv(root / "data" / "processed" / "ioc_all_countries.csv")
    recent = ioc[ioc.crop_year_start >= 2015].copy()
    agg = recent.groupby("country").agg(
        production=("production_tonnes", "mean"),
        exports=("exports_tonnes", "mean"),
        imports=("imports_tonnes", "mean"),
        consumption=("consumption_tonnes", "mean"),
    )
    agg = agg.dropna(subset=["production", "exports"])
    agg = agg[agg.production > 0]
    # drop non-country aggregates
    agg = agg[~agg.index.isin(["World", "EU", "Other non-producing countries", "Other producing countries"])]
    return agg


def load_export_share_ratio(root):
    """Export share computed as the mean of each YEAR's own ratio, not the
    ratio of averaged totals. This matches the methodology used in
    export_share_timeseries.py and is more robust to which individual years
    happen to carry more volume (relevant given alternate-bearing swings) --
    it's the number that should be quoted everywhere in the deck."""
    ioc = pd.read_csv(root / "data" / "processed" / "ioc_all_countries.csv")
    recent = ioc[ioc.crop_year_start >= 2015].copy()
    recent = recent[~recent.country.isin(["World", "EU", "Other non-producing countries", "Other producing countries"])]
    recent = recent[recent.production_tonnes > 0]
    recent["ratio"] = recent.exports_tonnes / recent.production_tonnes * 100
    return recent.groupby("country")["ratio"].mean()


def chart_scatter(agg, out_dir):
    sub = agg[(agg.production > 1000) & (agg.exports > 0)].copy()
    logp = np.log(sub.production)
    loge = np.log(sub.exports)
    slope, intercept = np.polyfit(logp, loge, 1)
    sub["predicted"] = slope * logp + intercept
    sub["residual"] = loge - sub["predicted"]

    fig, ax = plt.subplots(figsize=(10, 7.5))
    ax.scatter(sub.production, sub.exports, s=60, c=NEUTRAL, alpha=0.55, edgecolors="white", linewidths=0.5, zorder=2)

    label_offsets = {
        "Italy": (8, 14),
        "Tunisia": (-70, -18),
        "Spain": (8, 6),
        "Türkiye": (8, 6),
        "Greece": (8, 6),
    }
    for country, color in HIGHLIGHT_COLORS.items():
        if country in sub.index:
            row = sub.loc[country]
            ax.scatter(row.production, row.exports, s=220, c=color, edgecolors="black", linewidths=1, zorder=4)
            dx, dy = label_offsets.get(country, (8, 6))
            ax.annotate(country, (row.production, row.exports), fontsize=11, fontweight="bold",
                        xytext=(dx, dy), textcoords="offset points", zorder=5)

    # trend line
    xs = np.linspace(sub.production.min(), sub.production.max(), 100)
    ys = np.exp(intercept) * xs ** slope
    ax.plot(xs, ys, color="black", linestyle="--", linewidth=1.2, alpha=0.6, zorder=1,
            label="Expected exports, given production\n(fit across all reporting countries)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Average olive oil production, 2015-2024 (tonnes, log scale)", fontsize=11)
    ax.set_ylabel("Average olive oil exports, 2015-2024 (tonnes, log scale)", fontsize=11)
    ax.set_title("Who Grows It vs. Who Sells It\nItaly exports far more than its harvest predicts. Greece, the opposite.",
                  fontsize=14, fontweight="bold")
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(alpha=0.2, which="both")
    fig.tight_layout()
    fig.savefig(out_dir / "production_vs_exports_scatter.png", dpi=200)
    plt.close(fig)


def chart_export_share(agg, out_dir, ratio_series):
    """Export share of production -- the cleanest single proof of the thesis.
    Uses the mean-of-yearly-ratios (ratio_series), consistent with
    export_share_timeseries.py, not the ratio of averaged totals."""
    sub = agg[["production"]].join(ratio_series.rename("export_share"), how="inner")
    sub = sub[sub.production > 100000]  # keep it to major producers only
    sub = sub.sort_values("export_share", ascending=True)

    colors = [HIGHLIGHT_COLORS.get(c, NEUTRAL) for c in sub.index]

    fig, ax = plt.subplots(figsize=(9.5, 7))
    bars = ax.barh(sub.index, sub.export_share, color=colors, edgecolor="black", linewidth=0.4)
    for bar, country in zip(bars, sub.index):
        if country in HIGHLIGHT_COLORS:
            bar.set_linewidth(1.3)
    ax.set_xlabel("Exports as % of production, 2015-2024 average", fontsize=11)
    ax.set_title("Who Sells Almost Everything They Grow\nTunisia and Italy export the majority of their harvest. Greece exports almost none.",
                  fontsize=13.5, fontweight="bold")
    ax.grid(alpha=0.2, axis="x")
    fig.tight_layout()
    fig.savefig(out_dir / "export_share_bar.png", dpi=200)
    plt.close(fig)


def chart_rank_bump(agg, out_dir):
    sub = agg.copy()
    sub["prod_rank"] = sub["production"].rank(ascending=False, method="min")
    sub["exp_rank"] = sub["exports"].rank(ascending=False, method="min")

    keep = sub[(sub.prod_rank <= 12) | (sub.exp_rank <= 12)].copy()

    fig, ax = plt.subplots(figsize=(10, 9))
    for country, row in keep.iterrows():
        color = HIGHLIGHT_COLORS.get(country, NEUTRAL)
        lw = 3 if country in HIGHLIGHT_COLORS else 1.2
        alpha = 1.0 if country in HIGHLIGHT_COLORS else 0.45
        z = 5 if country in HIGHLIGHT_COLORS else 2
        ax.plot([0, 1], [row.prod_rank, row.exp_rank], color=color, linewidth=lw, alpha=alpha, zorder=z, marker="o", markersize=5)
        label_color = color if country in HIGHLIGHT_COLORS else "#555555"
        weight = "bold" if country in HIGHLIGHT_COLORS else "normal"
        ax.text(-0.03, row.prod_rank, country, ha="right", va="center", fontsize=9.5, color=label_color, fontweight=weight)
        ax.text(1.03, row.exp_rank, country, ha="left", va="center", fontsize=9.5, color=label_color, fontweight=weight)

    ax.invert_yaxis()
    ax.set_xlim(-0.6, 1.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Rank by\nproduction", "Rank by\nexports"], fontsize=11, fontweight="bold")
    ax.set_yticks([])
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.set_title("Tunisia's Quiet Rise, Greece's Disappearance\nItaly holds #2 either way — its story is share, not rank (see export-share chart)",
                  fontsize=12.5, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_dir / "rank_bump_chart.png", dpi=200)
    plt.close(fig)


def chart_supply_gap(agg, out_dir):
    sub = agg.copy()
    sub["inflow"] = sub.production.fillna(0) + sub.imports.fillna(0)
    sub["outflow"] = sub.consumption.fillna(0) + sub.exports.fillna(0)
    sub["unexplained_gap"] = sub.outflow - sub.inflow
    sub = sub.sort_values("unexplained_gap", ascending=False).head(10)

    colors = [HIGHLIGHT_COLORS.get(c, NEUTRAL) for c in sub.index]

    fig, ax = plt.subplots(figsize=(9.5, 6))
    bars = ax.barh(sub.index[::-1], sub.unexplained_gap[::-1], color=colors[::-1], edgecolor="black", linewidth=0.4)
    ax.set_xlabel("Unexplained supply gap (tonnes/year)\nconsumption + exports  minus  production + reported imports", fontsize=10)
    ax.set_title("The Missing Tonnage\nWhere declared trade doesn't add up to what's sold and eaten",
                  fontsize=14, fontweight="bold")
    ax.grid(alpha=0.2, axis="x")
    fig.tight_layout()
    fig.savefig(out_dir / "supply_gap_bar.png", dpi=200)
    plt.close(fig)


def build():
    root = find_project_root()
    agg = load_agg(root)
    ratio_series = load_export_share_ratio(root)
    out_dir = root / "outputs" / "figures" / "combined"
    out_dir.mkdir(parents=True, exist_ok=True)

    chart_scatter(agg, out_dir)
    chart_export_share(agg, out_dir, ratio_series)
    chart_rank_bump(agg, out_dir)
    chart_supply_gap(agg, out_dir)
    print(f"Wrote 4 charts to {out_dir}")


if __name__ == "__main__":
    build()

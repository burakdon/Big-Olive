"""Animated bubble chart: olive yield vs production, all countries, 1961-2024.

x = yield (kg/ha, log scale)      -- intensification
y = production (tonnes, log scale) -- scale
size = area harvested (ha)         -- footprint
color = region
frame = year

Spain and Turkey are drawn with a persistent trail so their trajectories
are readable against the swarm.
"""

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent))
from region_map import assign_region


def find_project_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    raise FileNotFoundError("Project root could not be found.")


def build():
    root = find_project_root()
    df = pd.read_csv(root / "data" / "processed" / "faostat_all_countries.csv")

    # Need both yield and production and area to be present
    df = df.dropna(subset=["yield_kg_ha", "production_tonnes", "area_harvested_ha"])
    df = df[(df["yield_kg_ha"] > 0) & (df["production_tonnes"] > 0)]

    df["region"] = df["country"].apply(assign_region)
    df["year"] = df["year"].astype(int)
    df = df.sort_values("year")

    # highlight flag for marker styling
    df["highlight"] = df["country"].isin(["Spain", "Türkiye"])

    region_colors = {
        "Western Mediterranean": "#c0392b",
        "Eastern Mediterranean": "#e67e22",
        "North Africa": "#16a085",
        "Middle East": "#8e44ad",
        "Rest of World": "#95a5a6",
    }

    fig = px.scatter(
        df,
        x="yield_kg_ha",
        y="production_tonnes",
        size="area_harvested_ha",
        color="region",
        color_discrete_map=region_colors,
        hover_name="country",
        animation_frame="year",
        animation_group="country",
        log_x=True,
        log_y=True,
        size_max=55,
        range_x=[max(df["yield_kg_ha"].min() * 0.7, 5), df["yield_kg_ha"].max() * 1.4],
        range_y=[max(df["production_tonnes"].min() * 0.5, 100), df["production_tonnes"].max() * 1.6],
        labels={
            "yield_kg_ha": "Yield (kg per hectare, log scale)",
            "production_tonnes": "Production (tonnes, log scale)",
            "region": "Region",
        },
        title="Olive Production, 1961-2024: Who Grows More, Who Grows Better",
    )

    # Make Spain & Turkey markers have a black outline so they pop against the swarm
    for frame in fig.frames:
        for trace in frame.data:
            pass  # styling handled via a separate overlay trace below

    fig.update_traces(marker=dict(line=dict(width=0.5, color="rgba(0,0,0,0.25)")))

    # Add persistent trace outlines for Spain and Turkey across all years (static, for context)
    for country, dash_color in [("Spain", "#c0392b"), ("Türkiye", "#e67e22")]:
        cdf = df[df["country"] == country].sort_values("year")
        fig.add_trace(
            go.Scatter(
                x=cdf["yield_kg_ha"],
                y=cdf["production_tonnes"],
                mode="lines",
                line=dict(color=dash_color, width=1.5, dash="dot"),
                opacity=0.35,
                name=f"{country} trajectory (all years)",
                hoverinfo="skip",
                showlegend=True,
            )
        )

    fig.update_layout(
        template="plotly_white",
        font=dict(family="Georgia, serif", size=14),
        title=dict(font=dict(size=22)),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        height=700,
        width=950,
    )

    # Slow the animation down a bit so it reads as a story, not a blur
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 400
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 250

    out_dir = root / "outputs" / "figures" / "faostat"
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "bubble_race_yield_production.html"
    fig.write_html(html_path, include_plotlyjs="cdn")

    # Also export a handful of static key-frame PNGs for slides, via matplotlib
    # (kaleido/plotly static export needs a local Chrome install, not available here)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x_lo, x_hi = max(df["yield_kg_ha"].min() * 0.7, 5), df["yield_kg_ha"].max() * 1.4
    y_lo, y_hi = max(df["production_tonnes"].min() * 0.5, 100), df["production_tonnes"].max() * 1.6
    size_ref = df["area_harvested_ha"].max()

    for yr in [1961, 1985, 2000, 2010, 2024]:
        sub = df[df["year"] == yr]
        if sub.empty:
            continue
        fig2, ax = plt.subplots(figsize=(9.5, 7))
        for region, color in region_colors.items():
            rsub = sub[sub["region"] == region]
            if rsub.empty:
                continue
            sizes = 30 + 900 * (rsub["area_harvested_ha"] / size_ref) ** 0.5
            ax.scatter(
                rsub["yield_kg_ha"], rsub["production_tonnes"],
                s=sizes, c=color, alpha=0.75, edgecolors="black", linewidths=0.4,
                label=region,
            )
        # highlight Spain & Turkey with labels
        for country in ["Spain", "Türkiye"]:
            csub = sub[sub["country"] == country]
            if not csub.empty:
                ax.annotate(
                    country,
                    (csub["yield_kg_ha"].values[0], csub["production_tonnes"].values[0]),
                    fontsize=10, fontweight="bold",
                    xytext=(6, 6), textcoords="offset points",
                )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(x_lo, x_hi)
        ax.set_ylim(y_lo, y_hi)
        ax.set_xlabel("Yield (kg/ha, log scale)", fontsize=11)
        ax.set_ylabel("Production (tonnes, log scale)", fontsize=11)
        ax.set_title(f"Olive Production, {yr}", fontsize=16, fontweight="bold")
        ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
        ax.grid(True, which="both", alpha=0.2)
        fig2.tight_layout()
        fig2.savefig(out_dir / f"bubble_snapshot_{yr}.png", dpi=200)
        plt.close(fig2)

    print(f"Wrote {html_path}")
    print(f"Wrote snapshot PNGs to {out_dir}")


if __name__ == "__main__":
    build()

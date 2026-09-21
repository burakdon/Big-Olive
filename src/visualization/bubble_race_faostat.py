"""Animated GIF: olive yield vs production, big-5 countries highlighted.

Built for embedding in the slide deck -- PowerPoint can't play interactive
JS, so this renders real GIF frames with matplotlib rather than relying on
Plotly (which also needed a live browser to export static images, not
available in this environment anyway).

DESIGN DECISIONS (each fixing a specific problem found in review):

1. START YEAR = 1985, not 1961. Spain's FAOSTAT yield/area records only
   start in 1980; Greece's start in 1985. Starting the animation any
   earlier means one of the "big 5" pops into existence mid-animation,
   which reads as a bug in a GIF with no way to explain it. 1985 is the
   first year all five have real data.

2. PERSISTENT ON-SCREEN LABELS for the big 5, not hover tooltips. A GIF
   has no hover state, so identification has to be permanent text next to
   each highlighted bubble every frame.

3. BIG-5 COLOR OVERRIDES REGION COLOR. Previously the highlighted
   countries kept their region's color for the bubble fill (e.g. Italy and
   Spain are both "Western Mediterranean" = same red) while ALSO getting a
   different, unrelated trail color -- so a single country was represented
   by two contradicting colors at once, and same-region countries were
   indistinguishable from each other. Now each of the 5 gets ONE color
   (bubble fill + trail + label, all matching), completely separate from
   the muted region palette used for the ~55 background "swarm" countries.

4. GROWING TRAIL, not a fully-drawn 64-year trail shown from frame one.
   The trail for each highlighted country now only shows years up to the
   current frame -- it grows as the animation plays, which is what you'd
   expect from a "trajectory reveal" rather than spoiling the ending.

5. SMOOTHING (kept from the previous fix): olives are biennial bearers, so
   raw annual yield/production oscillate +/-40% with no real trend behind
   it. A 3-year centered rolling mean drives the animation so bubbles
   drift instead of jittering.
"""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from region_map import assign_region

START_YEAR = 1985  # first year Spain AND Greece both have real data
END_YEAR = 2023     # last year Greece has real data -- 2024 exists for the
                     # other 4 but Greece would simply vanish from that frame

HIGHLIGHT_COLORS = {
    "Tunisia": "#9c6644",
    "Italy": "#2d6a4f",
    "Spain": "#c0392b",
    "Türkiye": "#e67e22",
    "Greece": "#1d3557",
}

# Per-country label placement -- tuned against the 1985 and 2023 frames,
# where Italy/Türkiye/Greece cluster close together in yield-production
# space. A uniform "always above" offset caused label collisions once
# bubbles converged; these stagger direction and distance per country.
LABEL_OFFSETS = {
    "Tunisia": (0, 1.0),
    "Spain": (-18, 1.0),
    "Italy": (18, 1.1),
    "Türkiye": (0, -1.6),   # below its bubble, not above -- avoids Italy
    "Greece": (26, 0.9),
}

SWARM_REGION_COLORS = {
    "Western Mediterranean": "#e8b3ab",   # muted -- big-5 members of this
    "Eastern Mediterranean": "#f3cda3",   # region get their own solid color
    "North Africa": "#a9d4c8",            # instead, so these stay pale
    "Middle East": "#cdb3dd",
    "Rest of World": "#c9c9c9",
}


def find_project_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    raise FileNotFoundError("Project root could not be found.")


def build(fps_duration_ms=180, hold_last_frame_ms=1800):
    root = find_project_root()
    df = pd.read_csv(root / "data" / "processed" / "faostat_all_countries.csv")

    df = df.dropna(subset=["yield_kg_ha", "production_tonnes", "area_harvested_ha"])
    df = df[(df["yield_kg_ha"] > 0) & (df["production_tonnes"] > 0)]
    df["region"] = df["country"].apply(assign_region)
    df["year"] = df["year"].astype(int)
    df = df.sort_values(["country", "year"])

    # 3-year centered rolling mean per country -- smooths alternate bearing
    for col in ["yield_kg_ha", "production_tonnes", "area_harvested_ha"]:
        df[col] = (
            df.groupby("country")[col]
            .transform(lambda s: s.rolling(window=3, center=True, min_periods=1).mean())
        )

    df = df[(df.year >= START_YEAR) & (df.year <= END_YEAR)]

    x_lo, x_hi = df["yield_kg_ha"].min() * 0.7, df["yield_kg_ha"].max() * 1.4
    y_lo, y_hi = df["production_tonnes"].min() * 0.5, df["production_tonnes"].max() * 2.4
    size_ref = df["area_harvested_ha"].max()

    frame_dir = root / "outputs" / "figures" / "faostat" / "_gif_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    frame_paths = []

    years = list(range(START_YEAR, END_YEAR + 1))

    for yr in years:
        sub = df[df.year == yr]
        fig, ax = plt.subplots(figsize=(10, 7.2), dpi=130)

        # --- swarm (non-highlighted) countries, muted region colors ---
        swarm = sub[~sub.country.isin(HIGHLIGHT_COLORS)]
        for region, color in SWARM_REGION_COLORS.items():
            rsub = swarm[swarm.region == region]
            if rsub.empty:
                continue
            sizes = 25 + 700 * (rsub.area_harvested_ha / size_ref) ** 0.5
            ax.scatter(rsub.yield_kg_ha, rsub.production_tonnes, s=sizes, c=color,
                       alpha=0.75, edgecolors="white", linewidths=0.4, zorder=2)

        # --- growing trails for the big 5 (years up to and including yr) ---
        for country, color in HIGHLIGHT_COLORS.items():
            trail = df[(df.country == country) & (df.year <= yr)].sort_values("year")
            if len(trail) > 1:
                ax.plot(trail.yield_kg_ha, trail.production_tonnes, color=color,
                        linewidth=1.6, alpha=0.55, linestyle=(0, (2, 1.5)), zorder=3)

        # --- big-5 bubbles, own solid color, with persistent labels ---
        for country, color in HIGHLIGHT_COLORS.items():
            crow = sub[sub.country == country]
            if crow.empty:
                continue
            size = 25 + 700 * (crow.area_harvested_ha.values[0] / size_ref) ** 0.5
            x, y = crow.yield_kg_ha.values[0], crow.production_tonnes.values[0]
            ax.scatter([x], [y], s=size, c=color, alpha=0.92, edgecolors="black",
                       linewidths=1.0, zorder=5)
            dx, dy_sign = LABEL_OFFSETS[country]
            base_dist = (size ** 0.5) / 2 + 7
            dy = base_dist * dy_sign
            va = "bottom" if dy_sign > 0 else "top"
            ax.annotate(country, (x, y), fontsize=10.5, fontweight="bold", color=color,
                        xytext=(dx, dy), textcoords="offset points",
                        ha="center", va=va, zorder=6,
                        path_effects=[__import__("matplotlib.patheffects", fromlist=["withStroke"]).withStroke(linewidth=3, foreground="white")])

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(x_lo, x_hi)
        ax.set_ylim(y_lo, y_hi)
        ax.set_xlabel("Yield (kg per hectare, log scale)", fontsize=11)
        ax.set_ylabel("Production (tonnes, log scale)", fontsize=11)
        ax.grid(True, which="both", alpha=0.18)
        ax.set_title("Olive Production, 1985-2023: Who Grows More, Who Grows Better",
                      fontsize=15, fontweight="bold", loc="left")

        # Prominent year readout -- replaces the interactive slider a GIF can't have
        ax.text(0.98, 0.05, str(yr), transform=ax.transAxes, fontsize=34, fontweight="bold",
                color="#333333", ha="right", va="bottom", alpha=0.85,
                path_effects=[__import__("matplotlib.patheffects", fromlist=["withStroke"]).withStroke(linewidth=4, foreground="white")])

        fig.tight_layout()
        fp = frame_dir / f"frame_{yr}.png"
        fig.savefig(fp, dpi=130)
        plt.close(fig)
        frame_paths.append(fp)

    # --- Stitch frames into a GIF ---
    images = [Image.open(fp).convert("P", palette=Image.ADAPTIVE) for fp in frame_paths]
    durations = [fps_duration_ms] * len(images)
    durations[-1] = hold_last_frame_ms  # pause on the final year before looping

    out_path = root / "outputs" / "figures" / "faostat" / "bubble_race.gif"
    images[0].save(
        out_path, save_all=True, append_images=images[1:],
        duration=durations, loop=0, optimize=True,
    )

    print(f"Wrote {out_path} ({len(images)} frames, {years[0]}-{years[-1]})")
    print(f"File size: {out_path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    build()
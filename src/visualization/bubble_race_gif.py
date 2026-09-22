"""Animated GIF: olive yield vs production, big-5 countries highlighted.

KEYFRAME + TWEEN approach (not annual frames). The first version of this
GIF played all 39 years, one per frame -- even with 3-year smoothing, that
still samples every year's noise, so the motion read as buzzy rather than
a clean trend. Instead: pick a handful of well-spaced anchor years, hold on
each one long enough to read it, then glide smoothly (eased interpolation)
between anchors. This is closer to how Gapminder's own animation actually
works -- it eases between real anchor points, it doesn't tick through raw
annual data.

Anchors: 1985, 1991, 1998, 2004, 2010, 2017, 2023 -- evenly spaced across
the full range where all 5 highlighted countries have real data (Spain's
FAOSTAT record starts 1980, Greece's starts 1985 and ends 2023, which is
what bounds the whole range).

Each anchor's position uses the 3-year centered rolling mean at that year
(not the raw single-year value), so a single anomalous biennial year can't
skew where an anchor sits -- smoothing happens at the anchor level, and
tweening happens between already-smoothed anchors.

PRODUCTION AXIS IS LINEAR, NOT LOG. Log scale is designed to compress large
differences -- exactly the opposite of what a "look how much bigger this
got" chart wants. Yield (x-axis) stays log, since its spread is only ~2
orders of magnitude and it's a secondary/contextual variable here, not the
one the chart is trying to dramatize.

BUBBLE SIZE = PRODUCTION, not area harvested. Previously size encoded
footprint (hectares planted), a different variable from the y-axis. Tying
size to the same variable as the y-axis is deliberately redundant -- it
reinforces the production story on two visual channels at once (a bubble
that's both high AND big reads as "big producer" faster than reading the
axis), which is what a presentation visual should optimize for over
analytical precision.
"""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patheffects
from PIL import Image
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from region_map import assign_region

KEYFRAME_YEARS = [1985, 1991, 1998, 2004, 2010, 2017, 2023]
HOLD_FRAMES = 6          # frames spent paused ON each anchor year
TWEEN_FRAMES = 13        # frames spent gliding BETWEEN two anchors -- more
                         # anchors means more transitions, so slightly
                         # fewer tween frames per transition keeps total
                         # runtime reasonable
HOLD_DURATION_MS = 150
TWEEN_DURATION_MS = 55
FINAL_HOLD_EXTRA_MS = 1600  # extra pause on the very last frame before loop

HIGHLIGHT_COLORS = {
    "Tunisia": "#9c6644",
    "Italy": "#2d6a4f",
    "Spain": "#c0392b",
    "Türkiye": "#e67e22",
    "Greece": "#1d3557",
}

LABEL_OFFSETS = {
    "Tunisia": (0, 1.0),
    "Spain": (-18, 1.0),
    "Italy": (18, 1.1),
    "Türkiye": (0, -1.6),
    "Greece": (26, 0.9),
}

SWARM_REGION_COLORS = {
    "Western Mediterranean": "#e8b3ab",
    "Eastern Mediterranean": "#f3cda3",
    "North Africa": "#a9d4c8",
    "Middle East": "#cdb3dd",
    "Rest of World": "#c9c9c9",
}


def find_project_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    raise FileNotFoundError("Project root could not be found.")


def ease_in_out(t):
    """Smoothstep easing -- starts slow, speeds up, ends slow. Reads as
    natural glide rather than a linear slide."""
    return t * t * (3 - 2 * t)


def load_smoothed(root):
    df = pd.read_csv(root / "data" / "processed" / "faostat_all_countries.csv")
    df = df.dropna(subset=["yield_kg_ha", "production_tonnes", "area_harvested_ha"])
    df = df[(df["yield_kg_ha"] > 0) & (df["production_tonnes"] > 0)]
    df["region"] = df["country"].apply(assign_region)
    df["year"] = df["year"].astype(int)
    df = df.sort_values(["country", "year"])
    for col in ["yield_kg_ha", "production_tonnes", "area_harvested_ha"]:
        df[col] = (
            df.groupby("country")[col]
            .transform(lambda s: s.rolling(window=3, center=True, min_periods=1).mean())
        )
    return df


def draw_frame(ax, swarm_rows, big5_positions, trail_history, size_ref,
                x_lo, x_hi, y_lo, y_hi, display_year):
    """swarm_rows: DataFrame of non-highlighted countries for THIS instant
    (only drawn at exact anchors -- swarm doesn't tween, only the big 5 do,
    since interpolating ~55 background countries adds no story value and
    costs a lot of complexity).
    big5_positions: dict {country: (x, y, size_value)} for this instant,
    possibly interpolated. size_value is production_tonnes -- same variable
    as the y-axis, deliberately redundant (see module docstring).
    trail_history: dict {country: [(x,y), ...]} of anchor points strictly
    before this instant, PLUS the current point appended -- draws as a
    connect-the-anchors path with a moving head during tweens.
    """
    for region, color in SWARM_REGION_COLORS.items():
        rsub = swarm_rows[swarm_rows.region == region]
        if rsub.empty:
            continue
        sizes = 15 + 2000 * (rsub.production_tonnes / size_ref)
        ax.scatter(rsub.yield_kg_ha, rsub.production_tonnes, s=sizes, c=color,
                   alpha=0.7, edgecolors="white", linewidths=0.4, zorder=2)

    for country, color in HIGHLIGHT_COLORS.items():
        path = trail_history.get(country, [])
        if len(path) > 1:
            xs, ys = zip(*path)
            ax.plot(xs, ys, color=color, linewidth=1.6, alpha=0.5,
                    linestyle=(0, (2, 1.5)), zorder=3)

    for country, color in HIGHLIGHT_COLORS.items():
        if country not in big5_positions:
            continue
        x, y, size_value = big5_positions[country]
        size = 15 + 2000 * (size_value / size_ref)
        ax.scatter([x], [y], s=size, c=color, alpha=0.92, edgecolors="black",
                   linewidths=1.0, zorder=5)
        dx, dy_sign = LABEL_OFFSETS[country]
        base_dist = (size ** 0.5) / 2 + 7
        dy = base_dist * dy_sign
        va = "bottom" if dy_sign > 0 else "top"
        ax.annotate(country, (x, y), fontsize=10.5, fontweight="bold", color=color,
                    xytext=(dx, dy), textcoords="offset points",
                    ha="center", va=va, zorder=6,
                    path_effects=[patheffects.withStroke(linewidth=3, foreground="white")])

    ax.set_xscale("log")
    ax.set_yscale("linear")
    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo, y_hi)
    ax.set_xlabel("Yield (kg per hectare, log scale)", fontsize=11)
    ax.set_ylabel("Production (tonnes)", fontsize=11)
    ax.yaxis.set_major_formatter(
        __import__("matplotlib.ticker", fromlist=["FuncFormatter"]).FuncFormatter(
            lambda val, pos: f"{val/1e6:.1f}M" if val >= 1e6 else (f"{val/1e3:.0f}k" if val >= 1e3 else f"{val:.0f}")
        )
    )
    ax.grid(True, which="both", alpha=0.18)
    ax.set_title("Olive Production, 1985-2023: Who Grows More, Who Grows Better",
                  fontsize=15, fontweight="bold", loc="left")
    ax.text(0.98, 0.05, display_year, transform=ax.transAxes, fontsize=34, fontweight="bold",
            color="#333333", ha="right", va="bottom", alpha=0.85,
            path_effects=[patheffects.withStroke(linewidth=4, foreground="white")])


def build():
    root = find_project_root()
    df = load_smoothed(root)

    span = df[df.year.isin(KEYFRAME_YEARS)]
    x_lo, x_hi = span["yield_kg_ha"].min() * 0.7, span["yield_kg_ha"].max() * 1.4
    prod_max = span["production_tonnes"].max()
    y_lo, y_hi = -prod_max * 0.05, prod_max * 1.3   # linear: small negative
                                                      # floor so bubbles near
                                                      # zero don't get clipped
                                                      # at the bottom edge
    size_ref = prod_max

    # Pre-fetch each keyframe's big-5 positions and full swarm snapshot
    keyframe_data = {}
    for yr in KEYFRAME_YEARS:
        sub = df[df.year == yr]
        positions = {}
        for country in HIGHLIGHT_COLORS:
            row = sub[sub.country == country]
            if not row.empty:
                positions[country] = (
                    row.yield_kg_ha.values[0],
                    row.production_tonnes.values[0],
                    row.production_tonnes.values[0],  # size driven by production too (see docstring)
                )
        keyframe_data[yr] = {
            "positions": positions,
            "swarm": sub[~sub.country.isin(HIGHLIGHT_COLORS)],
        }

    frame_dir = root / "outputs" / "figures" / "faostat" / "_gif_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for old in frame_dir.glob("*.png"):
        old.unlink()

    frame_paths = []
    durations = []
    trail_history = {c: [] for c in HIGHLIGHT_COLORS}

    def save_frame(idx, swarm_rows, positions, trail_hist_snapshot, display_year, duration_ms):
        fig, ax = plt.subplots(figsize=(10, 7.2), dpi=130)
        draw_frame(ax, swarm_rows, positions, trail_hist_snapshot, size_ref,
                   x_lo, x_hi, y_lo, y_hi, display_year)
        fig.tight_layout()
        fp = frame_dir / f"frame_{idx:04d}.png"
        fig.savefig(fp, dpi=130)
        plt.close(fig)
        frame_paths.append(fp)
        durations.append(duration_ms)

    idx = 0
    for i, yr in enumerate(KEYFRAME_YEARS):
        kf = keyframe_data[yr]
        # append this keyframe's own points to each country's trail history
        for country, (x, y, _) in kf["positions"].items():
            trail_history[country].append((x, y))

        # --- hold on this anchor ---
        for h in range(HOLD_FRAMES):
            save_frame(idx, kf["swarm"], kf["positions"], trail_history, str(yr), HOLD_DURATION_MS)
            idx += 1

        # --- tween to the NEXT anchor, if there is one ---
        if i < len(KEYFRAME_YEARS) - 1:
            next_yr = KEYFRAME_YEARS[i + 1]
            next_kf = keyframe_data[next_yr]
            for step in range(1, TWEEN_FRAMES + 1):
                t = ease_in_out(step / (TWEEN_FRAMES + 1))
                tween_positions = {}
                for country in HIGHLIGHT_COLORS:
                    if country in kf["positions"] and country in next_kf["positions"]:
                        x0, y0, a0 = kf["positions"][country]
                        x1, y1, a1 = next_kf["positions"][country]
                        tween_positions[country] = (
                            x0 + (x1 - x0) * t,
                            y0 + (y1 - y0) * t,
                            a0 + (a1 - a0) * t,
                        )
                # trail during tween: history so far + the moving current point
                tween_trail = {c: list(v) for c, v in trail_history.items()}
                for country, (x, y, _) in tween_positions.items():
                    tween_trail[country].append((x, y))

                display_year = str(round(yr + (next_yr - yr) * t))
                # swarm fades: show the DEPARTING keyframe's swarm for the
                # first half of the tween, arriving keyframe's for the
                # second half, rather than interpolating ~55 countries
                swarm_rows = kf["swarm"] if t < 0.5 else next_kf["swarm"]
                save_frame(idx, swarm_rows, tween_positions, tween_trail,
                           display_year, TWEEN_DURATION_MS)
                idx += 1

    # extra pause on the very last frame before the GIF loops
    durations[-1] += FINAL_HOLD_EXTRA_MS

    images = [Image.open(fp).convert("P", palette=Image.ADAPTIVE) for fp in frame_paths]
    out_path = root / "outputs" / "figures" / "faostat" / "bubble_race.gif"
    images[0].save(
        out_path, save_all=True, append_images=images[1:],
        duration=durations, loop=0, optimize=True,
    )

    print(f"Wrote {out_path} ({len(images)} frames)")
    print(f"File size: {out_path.stat().st_size / 1024:.0f} KB")
    print(f"Total playtime: {sum(durations) / 1000:.1f}s per loop")


if __name__ == "__main__":
    build()

"""Variant of the hero pictogram with Spain and Turkiye added (5 rows instead
of 3). Used as the OPENING slide -- doubles as the dataset/finding overview,
not a 3-second hook. See hero_pictogram.py for the closing bookend version
and the color-design rationale (unchanged here).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

EXPORTED_COLOR = "#F0C54A"
HOME_COLOR = "#C7CCD3"
CAP_COLOR = "#333333"

ROWS = [
    ("Tunisia", 92, "#9c6644",
     "For every 10 liters Tunisia presses, 9.2 are shipped abroad \n"
     "usually in bulk, before anyone attaches Tunisia's name to it."),
    ("Italy", 75, "#2d6a4f",
     "2.5 of every 10 liters Italy sells stay home; the other 7.5 leave.\n"
     "Separately, CNN reports 4 in 5 bottles Italy sells contain oil\n"
     "sourced from elsewhere too."),
    ("Spain", 31, "#c0392b",
     "Spain grows more olive oil than any other country by far\n"
     "but exports just under a third of it, keeping most for itself."),
    ("Türkiye", 25, "#e67e22",
     "Türkiye's harvest swings sharply year to year. Even so, it\n"
     "exports about a quarter of what it grows, similar to Spain."),
    ("Greece", 8, "#1d3557",
     "Greece presses almost as much oil as Italy but keeps 9.2 of\n"
     "every 10 liters at home, almost invisible to the rest of the world."),
]


def draw_bottle(ax, x, y, fill_color, scale=1.0):
    body = FancyBboxPatch(
        (x - 0.16 * scale, y), 0.32 * scale, 0.62 * scale,
        boxstyle=f"round,pad=0,rounding_size={0.06*scale}",
        linewidth=0.7, edgecolor="black", facecolor=fill_color, zorder=3,
    )
    neck = Rectangle(
        (x - 0.06 * scale, y + 0.62 * scale), 0.12 * scale, 0.16 * scale,
        linewidth=0.7, edgecolor="black", facecolor=fill_color, zorder=3,
    )
    cap = Rectangle(
        (x - 0.08 * scale, y + 0.78 * scale), 0.16 * scale, 0.07 * scale,
        linewidth=0.7, edgecolor="black", facecolor=CAP_COLOR, zorder=3,
    )
    ax.add_patch(body)
    ax.add_patch(neck)
    ax.add_patch(cap)


def find_project_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    raise FileNotFoundError("Project root could not be found.")


def build():
    root = find_project_root()
    fig, ax = plt.subplots(figsize=(12, 12.5))

    row_gap = 1.05
    n_bottles = 10
    bottle_spacing = 0.62

    for row_i, (country, pct, accent, caption) in enumerate(ROWS):
        y0 = (len(ROWS) - 1 - row_i) * row_gap
        n_exported = round(pct / 10)

        for i in range(n_bottles):
            x = i * bottle_spacing
            fill = EXPORTED_COLOR if i < n_exported else HOME_COLOR
            draw_bottle(ax, x, y0, fill, scale=1.0)

        ax.text(-1.35, y0 + 0.45, f"{pct}%", fontsize=28, fontweight="bold",
                 color=accent, ha="right", va="center")
        ax.text(-1.35, y0 + 0.85, country, fontsize=14, fontweight="bold",
                 color=accent, ha="right", va="center")
        ax.text(n_bottles * bottle_spacing - 0.05, y0 + 0.35, caption,
                 fontsize=10, color="#333333", ha="left", va="center")

    ax.set_xlim(-3.0, 11.3)
    ax.set_ylim(-0.35, len(ROWS) * row_gap + 0.35)
    ax.axis("off")

    fig.suptitle("Same Harvest, Five Different Fates", fontsize=22, fontweight="bold", y=0.99, x=0.32, ha="center")
    fig.text(0.055, 0.935, "Share of olive oil production exported, 2015–2024 average",
              fontsize=12, color="#555555")

    legend_y = 0.905
    sw = Rectangle((0.055, legend_y), 0.018, 0.015, transform=fig.transFigure,
                    facecolor=EXPORTED_COLOR, edgecolor="black", linewidth=0.6)
    fig.add_artist(sw)
    fig.text(0.078, legend_y + 0.0075, "Exported abroad", fontsize=10.5, color="#333333", va="center")
    sw2 = Rectangle((0.215, legend_y), 0.018, 0.015, transform=fig.transFigure,
                     facecolor=HOME_COLOR, edgecolor="black", linewidth=0.6)
    fig.add_artist(sw2)
    fig.text(0.238, legend_y + 0.0075, "Stays in the country", fontsize=10.5, color="#333333", va="center")

    fig.text(0.055, 0.015,
              "Sources: International Olive Council; CNN/Olive Oil Times reporting on Italian olive oil re-export practices.",
              fontsize=8, color="#888888")

    fig.tight_layout(rect=[0, 0.03, 1, 0.885])
    out_dir = root / "outputs" / "figures" / "combined"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "hero_pictogram_5row.png", dpi=220)
    plt.close(fig)
    print("Wrote hero_pictogram_5row.png")


if __name__ == "__main__":
    build()
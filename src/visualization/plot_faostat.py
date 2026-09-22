from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "faostat_all_countries.csv"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "faostat"

COUNTRY_COLORS = {
    "Spain": "#DDA01A",
    "Türkiye": "#C0272D",
    "Italy": "#2E7D52",
}

LABEL_COLORS = {
    "Spain": "#A8760A",
    "Türkiye": "#A11F24",
    "Italy": "#1F5E3C",
}

INK = "#1A1A1A"
MUTED = "#5F6672"
GRID = "#E4E7EB"
BACKGROUND_LINE = "#D7DBE0"

COMPARISON_COUNTRIES = ["Spain", "Türkiye", "Italy"]
RHYTHM_COUNTRIES = ["Spain", "Türkiye"]
EARLY_PERIOD = (1981, 1990)
RECENT_PERIOD = (2015, 2024)
ANALYSIS_PERIODS = {
    "1961–1990": (1961, 1990),
    "1991–2024": (1991, 2024),
}
N_PERMUTATIONS = 50_000

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Could not find {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, dtype={"m49_code": "string"})
    df = df.sort_values(["country", "year"]).reset_index(drop=True)

    required = {"country", "year", "production_tonnes", "area_harvested_ha"}
    missing = required.difference(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    return df

def save_figure(fig, filename, dpi=220):
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURE_DIR / filename
    fig.savefig(output_path, dpi=dpi, facecolor="white")
    print("Saved:", output_path)

def clean_axes(ax):
    ax.set_axisbelow(True)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)

def add_source(fig):
    fig.text(
        0.5,
        0.028,
        "Source: FAOSTAT",
        ha="center",
        fontsize=10.5,
        color="#8A919C",
    )

def print_dataset_summary(df):
    print("Shape:", df.shape)
    print("Years:", df["year"].min(), "to", df["year"].max())
    print("Countries:", df["country"].nunique())
    print()

    for country in COMPARISON_COUNTRIES:
        latest = (
            df[df["country"] == country]
            .dropna(subset=["production_tonnes"])
            .iloc[-1]
        )
        print(
            f"{country:<9} latest year {int(latest['year'])}: "
            f"{latest['production_tonnes'] / 1_000_000:.2f}M tonnes"
        )

    print()
    print("Missing production values:", df["production_tonnes"].isna().sum())

def plot_production_paths(df):
    fig, ax = plt.subplots(figsize=(12.5, 7.2), dpi=220)
    fig.subplots_adjust(left=0.085, right=0.80, top=0.755, bottom=0.165)

    for country, country_df in df.groupby("country"):
        if country in COMPARISON_COUNTRIES:
            continue

        country_df = country_df.sort_values("year")
        ax.plot(
            country_df["year"],
            country_df["production_tonnes"] / 1_000_000,
            color=BACKGROUND_LINE,
            linewidth=0.8,
            alpha=0.55,
            zorder=1,
        )

    for i, country in enumerate(["Italy", "Türkiye", "Spain"]):
        country_df = df[df["country"] == country].sort_values("year")
        y = country_df["production_tonnes"] / 1_000_000

        ax.plot(
            country_df["year"],
            y,
            color=COUNTRY_COLORS[country],
            linewidth=2.9,
            zorder=3 + i,
            solid_capstyle="round",
        )

        last_row = country_df.dropna(subset=["production_tonnes"]).iloc[-1]
        last_value = last_row["production_tonnes"] / 1_000_000

        ax.plot(
            [last_row["year"]],
            [last_value],
            "o",
            color=COUNTRY_COLORS[country],
            markersize=6.5,
            zorder=6,
            clip_on=False,
        )

        ax.annotate(
            f"{country}  {last_value:.2f}M",
            xy=(last_row["year"], last_value),
            xytext=(12, 0),
            textcoords="offset points",
            color=LABEL_COLORS[country],
            fontsize=13.5,
            fontweight="bold",
            va="center",
            annotation_clip=False,
        )

    ax.set_xlim(df["year"].min(), df["year"].max())
    ax.set_ylim(0, 10.4)
    ax.set_yticks(range(0, 11, 2))
    ax.set_yticklabels(range(0, 11, 2), fontsize=12, color=MUTED)

    year_ticks = list(range(1965, 2021, 5)) + [2024]
    ax.set_xticks(year_ticks)
    ax.set_xticklabels(year_ticks, fontsize=12, color=MUTED)

    ax.tick_params(axis="both", length=0, pad=8)
    ax.set_xlabel("Year", fontsize=12.5, color=MUTED, labelpad=12)
    ax.set_ylabel(
        "Olive production (million tonnes)",
        fontsize=12.5,
        color=MUTED,
        labelpad=12,
    )
    ax.yaxis.grid(True, color=GRID, linewidth=1, zorder=0)
    clean_axes(ax)

    fig.text(
        0.5, 0.955,
        "Three Different Paths in Olive Production",
        ha="center", va="center",
        fontsize=25, fontweight="bold", color=INK,
    )

    subtitle_lines = [
        "Annual olive production, 1961–2024. Spain remains the largest producer,",
        "Türkiye has expanded strongly, while Italy has followed a flatter path.",
        "Other FAOSTAT producers shown in grey.",
    ]

    for i, line in enumerate(subtitle_lines):
        fig.text(
            0.5,
            0.903 - i * 0.039,
            line,
            ha="center",
            va="center",
            fontsize=14,
            color=MUTED,
        )

    add_source(fig)
    save_figure(fig, "olive_production_all_countries.png")
    plt.close(fig)

def period_averages(frame, start_year, end_year):
    period = (
        frame[frame["year"].between(start_year, end_year)]
        .groupby("country")[["area_harvested_ha", "production_tonnes"]]
        .mean()
    )

    period["yield_kg_ha"] = (
        period["production_tonnes"] * 1000
        / period["area_harvested_ha"]
    )

    return period

def calculate_long_term_change(df):
    comparison_df = df[df["country"].isin(COMPARISON_COUNTRIES)].copy()

    early = period_averages(comparison_df, *EARLY_PERIOD)
    recent = period_averages(comparison_df, *RECENT_PERIOD)

    return (
        ((recent / early - 1) * 100)
        .rename(columns={
            "area_harvested_ha": "Harvested area",
            "yield_kg_ha": "Yield",
            "production_tonnes": "Production",
        })
        [["Harvested area", "Yield", "Production"]]
        .reindex(COMPARISON_COUNTRIES)
    )

def plot_agricultural_change(df):
    long_term_change = calculate_long_term_change(df)
    print("\nLong-term agricultural change (%):")
    print(long_term_change.round(1).to_string())

    metrics = ["Harvested area", "Yield", "Production"]
    x = np.arange(len(metrics))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12.5, 7.2), dpi=220)
    fig.subplots_adjust(left=0.085, right=0.97, top=0.745, bottom=0.165)

    for country, offset in zip(COMPARISON_COUNTRIES, [-width, 0, width]):
        values = long_term_change.loc[country, metrics].values

        bars = ax.bar(
            x + offset,
            values,
            width * 0.92,
            label=country,
            color=COUNTRY_COLORS[country],
            edgecolor="none",
            zorder=3,
        )

        for bar, value in zip(bars, values):
            positive = value >= 0

            ax.annotate(
                f"{value:+.0f}%",
                xy=(bar.get_x() + bar.get_width() / 2, value),
                xytext=(0, 7 if positive else -9),
                textcoords="offset points",
                ha="center",
                va="bottom" if positive else "top",
                fontsize=13,
                fontweight="bold",
                color=LABEL_COLORS[country],
                zorder=4,
            )

    ax.set_ylim(-32, 190)
    ax.set_yticks(np.arange(-25, 200, 25))
    ax.set_yticklabels(
        [f"{t}%" for t in np.arange(-25, 200, 25)],
        fontsize=12,
        color=MUTED,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=14, color=INK)
    ax.tick_params(axis="x", length=0, pad=12)
    ax.tick_params(axis="y", length=0, pad=6)
    ax.set_ylabel("Change (%)", fontsize=12.5, color=MUTED, labelpad=12)
    ax.yaxis.grid(True, color=GRID, linewidth=1, zorder=0)
    ax.axhline(0, color="#9AA1AC", linewidth=1.2, zorder=2)
    clean_axes(ax)

    fig.text(
        0.5, 0.935,
        "Different Paths of Agricultural Change",
        ha="center", va="center",
        fontsize=25, fontweight="bold", color=INK,
    )
    fig.text(
        0.5, 0.881,
        f"Change in ten-year averages, {EARLY_PERIOD[0]}–{EARLY_PERIOD[1]} "
        f"to {RECENT_PERIOD[0]}–{RECENT_PERIOD[1]}",
        ha="center", va="center",
        fontsize=14.5, color=MUTED,
    )

    legend = fig.legend(
        *ax.get_legend_handles_labels(),
        loc="center",
        bbox_to_anchor=(0.5, 0.825),
        ncol=3,
        frameon=False,
        fontsize=13.5,
        handlelength=1.1,
        handleheight=1.1,
        handletextpad=0.7,
        columnspacing=2.6,
    )

    for text in legend.get_texts():
        text.set_color(INK)

    add_source(fig)
    save_figure(fig, "agricultural_change_flag_colors.png")
    plt.close(fig)

def calculate_italy_world_index(df):
    wide = df.pivot(
        index="year",
        columns="country",
        values="production_tonnes",
    )

    balanced_countries = wide.loc[1961:2023].dropna(axis=1).columns

    print(f"\nBalanced panel: {len(balanced_countries)} of {wide.shape[1]} countries")
    print(
        "2024 total, balanced vs all: "
        f"{wide[balanced_countries].loc[2024].sum() / 1e6:.2f}M vs "
        f"{wide.loc[2024].sum() / 1e6:.2f}M tonnes"
    )

    world = wide[balanced_countries].sum(axis=1)
    italy = wide["Italy"]

    index_world = world / world.loc[1961:1965].mean() * 100
    index_italy = italy / italy.loc[1961:1965].mean() * 100

    smooth_world = index_world.rolling(5, center=True, min_periods=3).mean()
    smooth_italy = index_italy.rolling(5, center=True, min_periods=3).mean()

    return index_world, index_italy, smooth_world, smooth_italy, len(balanced_countries)

def plot_italy_vs_world(df):
    (
        index_world,
        index_italy,
        smooth_world,
        smooth_italy,
        balanced_count,
    ) = calculate_italy_world_index(df)

    world_color = "#46606E"
    world_label = "#33474F"

    fig, ax = plt.subplots(figsize=(12.5, 7.2), dpi=220)
    fig.subplots_adjust(left=0.085, right=0.80, top=0.755, bottom=0.165)

    ax.plot(
        index_world.index,
        index_world,
        color=world_color,
        linewidth=0.9,
        alpha=0.35,
        zorder=2,
    )
    ax.plot(
        index_italy.index,
        index_italy,
        color=COUNTRY_COLORS["Italy"],
        linewidth=0.9,
        alpha=0.35,
        zorder=2,
    )
    ax.plot(
        smooth_world.index,
        smooth_world,
        color=world_color,
        linewidth=3.0,
        zorder=4,
        solid_capstyle="round",
    )
    ax.plot(
        smooth_italy.index,
        smooth_italy,
        color=COUNTRY_COLORS["Italy"],
        linewidth=3.0,
        zorder=5,
        solid_capstyle="round",
    )
    ax.axhline(
        100,
        color="#C9CED6",
        linewidth=1,
        linestyle=(0, (5, 4)),
        zorder=1,
    )

    for series, color, label_color, name in [
        (smooth_world, world_color, world_label, "All producers"),
        (
            smooth_italy,
            COUNTRY_COLORS["Italy"],
            LABEL_COLORS["Italy"],
            "Italy",
        ),
    ]:
        valid = series.dropna()
        x_last, y_last = valid.index[-1], valid.iloc[-1]

        ax.plot(
            [x_last], [y_last],
            "o",
            color=color,
            markersize=6.5,
            zorder=6,
            clip_on=False,
        )
        ax.annotate(
            f"{name}  {y_last:.0f}",
            xy=(x_last, y_last),
            xytext=(12, 0),
            textcoords="offset points",
            color=label_color,
            fontsize=14,
            fontweight="bold",
            va="center",
            annotation_clip=False,
        )

    ax.set_xlim(1961, 2024)
    ax.set_ylim(0, 340)
    ax.set_yticks(range(0, 350, 50))
    ax.set_yticklabels(range(0, 350, 50), fontsize=12, color=MUTED)

    year_ticks = list(range(1970, 2021, 10)) + [2024]
    ax.set_xticks(year_ticks)
    ax.set_xticklabels(year_ticks, fontsize=12, color=MUTED)

    ax.tick_params(axis="both", length=0, pad=8)
    ax.set_xlabel("Year", fontsize=12.5, color=MUTED, labelpad=12)
    ax.set_ylabel(
        "Olive production (1961–1965 average = 100)",
        fontsize=12.5,
        color=MUTED,
        labelpad=12,
    )
    ax.yaxis.grid(True, color=GRID, linewidth=1, zorder=0)
    clean_axes(ax)

    fig.text(
        0.5, 0.945,
        "Italy Harvests About What It Did in the 1960s",
        ha="center", va="center",
        fontsize=25, fontweight="bold", color=INK,
    )

    subtitle_lines = [
        "Olive production indexed to each series' 1961–1965 average. Everyone else roughly tripled;",
        "Italy ended 2024 within a few points of where it started. Bold lines are five-year averages,",
        f"faint lines the raw annual values. World total covers the {balanced_count} countries reporting every year.",
    ]

    for i, line in enumerate(subtitle_lines):
        fig.text(
            0.5,
            0.888 - i * 0.039,
            line,
            ha="center",
            va="center",
            fontsize=13.5,
            color=MUTED,
        )

    add_source(fig)
    save_figure(fig, "italy_flat_vs_world.png")
    plt.close(fig)

def add_production_direction(df):
    direction_source = df.copy()

    if "production_direction" not in direction_source.columns:
        direction_source["production_change"] = (
            direction_source.groupby("country")["production_tonnes"].diff()
        )

        direction_source["production_direction"] = np.select(
            [
                direction_source["production_change"] > 0,
                direction_source["production_change"] < 0,
            ],
            ["increase", "decrease"],
            default=None,
        )

    return direction_source

def plot_direction_rhythm(direction_source):
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(12.5, 7.2),
        dpi=220,
        sharex=True,
    )
    fig.subplots_adjust(
        left=0.13,
        right=0.97,
        top=0.80,
        bottom=0.14,
        hspace=0.35,
    )

    for ax, country in zip(axes, RHYTHM_COUNTRIES):
        country_df = (
            direction_source[
                (direction_source["country"] == country)
                & direction_source["production_direction"].isin(
                    ["increase", "decrease"]
                )
            ]
            .sort_values("year")
        )

        heights = np.where(
            country_df["production_direction"].eq("increase"),
            1,
            -1,
        )

        ax.bar(
            country_df["year"],
            heights,
            width=0.62,
            color=COUNTRY_COLORS[country],
            zorder=3,
        )
        ax.axhline(0, color="#9AA1AC", linewidth=1, zorder=2)
        ax.set_ylim(-1.6, 1.6)
        ax.set_yticks([1, -1])
        ax.set_yticklabels(
            ["Higher than\nprevious year", "Lower than\nprevious year"],
            fontsize=11,
            color=MUTED,
        )
        ax.set_title(
            country,
            loc="left",
            fontsize=16,
            fontweight="bold",
            color=LABEL_COLORS[country],
            pad=10,
        )
        ax.tick_params(axis="both", length=0, pad=6)
        clean_axes(ax)

    axes[-1].set_xlabel("Year", fontsize=12.5, color=MUTED, labelpad=10)
    axes[-1].tick_params(axis="x", labelsize=12, colors=MUTED)

    fig.text(
        0.5, 0.945,
        "Year-to-Year Direction of Olive Production",
        ha="center", va="center",
        fontsize=24, fontweight="bold", color=INK,
    )
    fig.text(
        0.5, 0.893,
        "Bar position shows direction only, not the size of the annual change",
        ha="center", va="center",
        fontsize=14, color=MUTED,
    )

    save_figure(fig, "faostat_direction_rhythm.png")
    plt.close(fig)

def calculate_alternation(direction_source):
    rng = np.random.default_rng(510)
    results = []

    for country in RHYTHM_COUNTRIES:
        for period_name, (start_year, end_year) in ANALYSIS_PERIODS.items():
            period_df = (
                direction_source[
                    (direction_source["country"] == country)
                    & direction_source["year"].between(start_year, end_year)
                    & direction_source["production_direction"].isin(
                        ["increase", "decrease"]
                    )
                ]
                .sort_values("year")
            )

            directions = period_df["production_direction"].to_numpy()
            observed_rate = (
                (directions[1:] != directions[:-1]).mean() * 100
            )

            null_rates = np.empty(N_PERMUTATIONS)

            for i in range(N_PERMUTATIONS):
                shuffled = rng.permutation(directions)
                null_rates[i] = (
                    shuffled[1:] != shuffled[:-1]
                ).mean() * 100

            p_value = (
                np.sum(null_rates >= observed_rate) + 1
            ) / (N_PERMUTATIONS + 1)

            results.append({
                "country": country,
                "period": period_name,
                "observed_alternation_pct": observed_rate,
                "random_mean_pct": null_rates.mean(),
                "p_value": p_value,
            })

    return pd.DataFrame(results)

def plot_alternation(alternation_results):
    periods = list(ANALYSIS_PERIODS)
    x = np.arange(len(periods))
    width = 0.3

    fig, ax = plt.subplots(figsize=(12.5, 7.2), dpi=220)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.755, bottom=0.145)

    for country, offset in zip(RHYTHM_COUNTRIES, [-width / 2, width / 2]):
        subset = (
            alternation_results[
                alternation_results["country"] == country
            ]
            .set_index("period")
            .reindex(periods)
        )

        bars = ax.bar(
            x + offset,
            subset["observed_alternation_pct"],
            width * 0.92,
            label=country,
            color=COUNTRY_COLORS[country],
            zorder=3,
        )

        for bar, (_, row) in zip(bars, subset.iterrows()):
            p_text = (
                "p < 0.0001"
                if row["p_value"] < 0.0001
                else f"p = {row['p_value']:.4f}"
            )

            ax.annotate(
                f"{row['observed_alternation_pct']:.1f}%\n{p_text}",
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                fontsize=12.5,
                fontweight="bold",
                color=LABEL_COLORS[country],
                zorder=4,
            )

    random_expectation = alternation_results["random_mean_pct"].mean()

    ax.axhline(
        random_expectation,
        color="#8A919C",
        linewidth=1.4,
        linestyle=(0, (6, 4)),
        zorder=2,
    )
    ax.text(
        0.5,
        random_expectation + 3,
        f"Random-order expectation ≈ {random_expectation:.0f}%",
        ha="center",
        va="bottom",
        fontsize=12,
        color=MUTED,
        zorder=4,
    )

    ax.set_ylim(0, 115)
    ax.set_yticks(range(0, 101, 20))
    ax.set_yticklabels(
        [f"{t}%" for t in range(0, 101, 20)],
        fontsize=12,
        color=MUTED,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(periods, fontsize=14, color=INK)
    ax.tick_params(axis="both", length=0, pad=10)
    ax.set_ylabel(
        "Consecutive-year comparisons\nthat switch direction",
        fontsize=12.5,
        color=MUTED,
        labelpad=12,
    )
    ax.yaxis.grid(True, color=GRID, linewidth=1, zorder=0)
    clean_axes(ax)

    fig.text(
        0.5, 0.945,
        "Production Alternation Against Random Ordering",
        ha="center", va="center",
        fontsize=24, fontweight="bold", color=INK,
    )
    fig.text(
        0.5, 0.893,
        f"Observed direction switches compared with {N_PERMUTATIONS:,} random "
        "reorderings of the same increases and decreases",
        ha="center", va="center",
        fontsize=13.5, color=MUTED,
    )

    legend = fig.legend(
        *ax.get_legend_handles_labels(),
        loc="center",
        bbox_to_anchor=(0.5, 0.835),
        ncol=2,
        frameon=False,
        fontsize=13.5,
        handlelength=1.1,
        handleheight=1.1,
        handletextpad=0.7,
        columnspacing=2.6,
    )

    for text in legend.get_texts():
        text.set_color(INK)

    save_figure(fig, "faostat_alternation_rates.png")
    plt.close(fig)

def print_alternation_summary(alternation_results):
    summary = alternation_results.copy()
    summary["observed_alternation_pct"] = (
        summary["observed_alternation_pct"].round(1)
    )
    summary["random_mean_pct"] = summary["random_mean_pct"].round(1)
    summary["p_value"] = summary["p_value"].round(4)
    summary["significant_at_5pct"] = summary["p_value"] < 0.05

    summary.columns = [
        "Country",
        "Period",
        "Observed alternation (%)",
        "Random-order mean (%)",
        "p-value",
        "Significant at 5%",
    ]

    print("\nAlternation summary:")
    print(summary.to_string(index=False))

def main():
    df = load_data()
    print_dataset_summary(df)

    plot_production_paths(df)
    plot_agricultural_change(df)
    plot_italy_vs_world(df)

    direction_source = add_production_direction(df)
    plot_direction_rhythm(direction_source)

    alternation_results = calculate_alternation(direction_source)
    print_alternation_summary(alternation_results)
    plot_alternation(alternation_results)

    print("\nGenerated figures:")
    for path in sorted(FIGURE_DIR.glob("*.png")):
        print(f"{path.name:<42} {path.stat().st_size / 1024:>7.0f} KB")

if __name__ == "__main__":
    main()

from pathlib import Path

import pandas as pd


def find_project_root():
    # Find the project root instead of depending on the script location
    current_path = Path(__file__).resolve()

    for parent in current_path.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent

    raise FileNotFoundError("Project root could not be found.")


def engineer_faostat_features():
    project_root = find_project_root()

    clean_path = (
        project_root
        / "data"
        / "processed"
        / "faostat_clean.csv"
    )

    all_countries_path = (
        project_root
        / "data"
        / "processed"
        / "faostat_all_countries.csv"
    )

    output_path = (
        project_root
        / "data"
        / "processed"
        / "faostat_features.csv"
    )

    # Load the cleaned FAOSTAT datasets
    df = pd.read_csv(
        clean_path,
        dtype={"m49_code": "string"},
    )

    all_countries_df = pd.read_csv(
        all_countries_path,
        dtype={"m49_code": "string"},
    )

    # Sort before creating time-based features
    df = (
        df.sort_values(["country", "year"])
        .reset_index(drop=True)
    )

    # Calculate annual production growth
    df["production_growth_pct"] = (
        df.groupby("country")["production_tonnes"]
        .pct_change(fill_method=None)
        * 100
    )

    # Calculate the five-year rolling production average
    df["production_5yr_avg"] = (
        df.groupby("country")["production_tonnes"]
        .transform(
            lambda x: x.rolling(
                window=5,
                min_periods=5,
            ).mean()
        )
    )

    # Use the 1961-1965 average as the production index baseline
    base_production = (
        df[df["year"].between(1961, 1965)]
        .groupby("country")["production_tonnes"]
        .mean()
    )

    df["production_index"] = (
        df["production_tonnes"]
        / df["country"].map(base_production)
        * 100
    )

    # Use the common period for harvested area and yield comparisons
    area_yield_df = df[df["year"] >= 1980].copy()

    # Calculate annual harvested area growth
    area_yield_df["area_growth_pct"] = (
        area_yield_df
        .groupby("country")["area_harvested_ha"]
        .pct_change(fill_method=None)
        * 100
    )

    # Calculate annual yield growth
    area_yield_df["yield_growth_pct"] = (
        area_yield_df
        .groupby("country")["yield_kg_ha"]
        .pct_change(fill_method=None)
        * 100
    )

    # Calculate the interaction between area and yield growth
    area_yield_df["growth_interaction_pct"] = (
        area_yield_df["area_growth_pct"]
        * area_yield_df["yield_growth_pct"]
        / 100
    )

    # Reconstruct production growth from area and yield changes
    area_yield_df["reconstructed_production_growth_pct"] = (
        area_yield_df["area_growth_pct"]
        + area_yield_df["yield_growth_pct"]
        + area_yield_df["growth_interaction_pct"]
    )

    # Compare reconstructed and observed production growth
    area_yield_df["growth_difference_pct"] = (
        area_yield_df["production_growth_pct"]
        - area_yield_df["reconstructed_production_growth_pct"]
    )

    # Identify the ten countries with the highest cumulative production
    cumulative_production = (
        all_countries_df
        .groupby(
            "country",
            as_index=False,
        )["production_tonnes"]
        .sum(min_count=1)
        .sort_values(
            "production_tonnes",
            ascending=False,
        )
    )

    top_10_producers = (
        cumulative_production
        .head(10)["country"]
        .tolist()
    )

    # Check production coverage within the top ten producers
    total_years = all_countries_df["year"].nunique()

    top_10_df = all_countries_df[
        all_countries_df["country"].isin(top_10_producers)
    ].copy()

    coverage = (
        top_10_df
        .groupby("country")
        .agg(
            years_available=("year", "nunique"),
            production_years=("production_tonnes", "count"),
        )
        .reset_index()
    )

    coverage["complete_coverage"] = (
        coverage["production_years"] == total_years
    )

    # Keep only major producers with complete production coverage
    complete_producers = coverage.loc[
        coverage["complete_coverage"],
        "country",
    ].tolist()

    # Protect the meaning of the comparison group
    if len(complete_producers) != 9:
        excluded = sorted(
            set(top_10_producers)
            - set(complete_producers)
        )

        raise ValueError(
            f"Comparison group has {len(complete_producers)} countries, "
            f"expected 9. Excluded: {excluded}"
        )

    # Calculate total production for the consistent comparison group
    major_df = top_10_df[
        top_10_df["country"].isin(complete_producers)
    ].copy()

    major_totals = (
        major_df
        .groupby("year")["production_tonnes"]
        .sum()
    )

    df["major_production_total"] = (
        df["year"].map(major_totals)
    )

    # Calculate production share within the comparison group
    df["major_producer_share_pct"] = (
        df["production_tonnes"]
        / df["major_production_total"]
        * 100
    )

    # Classify the direction of annual production change
    df["production_direction"] = pd.NA

    df.loc[
        df["production_growth_pct"] > 0,
        "production_direction",
    ] = "increase"

    df.loc[
        df["production_growth_pct"] < 0,
        "production_direction",
    ] = "decrease"

    df.loc[
        df["production_growth_pct"] == 0,
        "production_direction",
    ] = "no_change"

    # Compare each year's direction with the previous year
    previous_direction = (
        df.groupby("country")["production_direction"]
        .shift(1)
    )

    df["alternating_direction"] = pd.Series(
        pd.NA,
        index=df.index,
        dtype="boolean",
    )

    valid_direction = (
        df["production_direction"].isin(
            ["increase", "decrease"]
        )
        & previous_direction.isin(
            ["increase", "decrease"]
        )
    )

    df.loc[
        valid_direction,
        "alternating_direction",
    ] = (
        df.loc[
            valid_direction,
            "production_direction",
        ]
        != previous_direction[valid_direction]
    )

    # Add area and yield features back using country and year
    feature_columns = [
        "area_growth_pct",
        "yield_growth_pct",
        "growth_interaction_pct",
        "reconstructed_production_growth_pct",
        "growth_difference_pct",
    ]

    area_yield_features = area_yield_df[
        ["country", "year"] + feature_columns
    ].copy()

    df = df.merge(
        area_yield_features,
        on=["country", "year"],
        how="left",
        validate="one_to_one",
    )

    # Confirm that country-year observations remain unique
    if df.duplicated(
        subset=["country", "year"]
    ).any():
        raise ValueError(
            "Duplicated country-year observations were created."
        )

    # Validate the production index baseline
    baseline_check = (
        df[df["year"].between(1961, 1965)]
        .groupby("country")["production_index"]
        .mean()
    )

    if baseline_check.empty:
        raise ValueError(
            "Baseline period produced no rows."
        )

    if baseline_check.isna().any():
        raise ValueError(
            "Production index baseline contains missing values."
        )

    if ((baseline_check - 100).abs() > 1e-9).any():
        raise ValueError(
            "Production index baseline does not average 100."
        )

    # Validate that the decomposition produced the expected rows
    decomposition_rows = (
        df["growth_difference_pct"]
        .notna()
        .sum()
    )

    expected_rows = (
        df[df["year"] >= 1980].shape[0]
        - df["country"].nunique()
    )

    if decomposition_rows != expected_rows:
        raise ValueError(
            f"Decomposition computed for {decomposition_rows} rows, "
            f"expected {expected_rows}."
        )

    # Validate the production growth decomposition
    max_difference = (
        df["growth_difference_pct"]
        .abs()
        .max()
    )

    if pd.isna(max_difference):
        raise ValueError(
            "Production growth decomposition produced no valid values."
        )

    if max_difference > 0.05:
        raise ValueError(
            "Production growth decomposition difference is too large."
        )

    # Save the final feature dataset
    df.to_csv(
        output_path,
        index=False,
    )

    # Print a short summary
    alternation_summary = (
        df.dropna(subset=["alternating_direction"])
        .groupby("country")["alternating_direction"]
        .mean()
        .mul(100)
    )

    print("FAOSTAT feature engineering completed.")
    print(f"Final dataset: {df.shape}")
    print(
        "Comparison group:",
        len(complete_producers),
        "countries",
    )
    print(
        f"Maximum decomposition difference: "
        f"{max_difference:.4f} percentage points"
    )
    print("\nAlternating direction (%):")
    print(alternation_summary)


if __name__ == "__main__":
    engineer_faostat_features()
from pathlib import Path

import pandas as pd


def find_project_root():
    # Find the project root instead of depending on the script location
    current_path = Path(__file__).resolve()

    for parent in current_path.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent

    raise FileNotFoundError("Project root could not be found.")


def preprocess_faostat():
    project_root = find_project_root()

    raw_path = project_root / "data" / "raw" / "faostat_olives.csv"
    processed_dir = project_root / "data" / "processed"

    processed_dir.mkdir(parents=True, exist_ok=True)

    # First, we load the raw FAOSTAT dataset
    df = pd.read_csv(raw_path)

    # Confirm that the dataset contains only olives
    if set(df["Item"].dropna().unique()) != {"Olives"}:
        raise ValueError(
            "Expected the FAOSTAT dataset to contain only 'Olives'."
        )

    # Keep only the variables needed for the analysis
    columns = [
        "Country",
        "Year",
        "Production (tonnes)",
        "Production (tonnes) flag",
        "Area harvested (ha)",
        "Area harvested (ha) flag",
        "Yield (kg/ha)",
        "Yield (kg/ha) flag",
    ]

    clean_all = df[columns].copy()

    # Rename the columns to make them easier to use
    clean_all = clean_all.rename(columns={
        "Country": "country",
        "Year": "year",
        "Production (tonnes)": "production_tonnes",
        "Production (tonnes) flag": "production_flag",
        "Area harvested (ha)": "area_harvested_ha",
        "Area harvested (ha) flag": "area_harvested_flag",
        "Yield (kg/ha)": "yield_kg_ha",
        "Yield (kg/ha) flag": "yield_flag",
    })

    # Sort the data by country and year
    clean_all = clean_all.sort_values(
        ["country", "year"]
    ).reset_index(drop=True)

    # Save the cleaned data for all countries
    clean_all.to_csv(
        processed_dir / "faostat_all_countries.csv",
        index=False,
    )

    # Keep Spain and Türkiye for the main analysis
    target_countries = ["Spain", "Türkiye"]

    clean_target = clean_all[
        clean_all["country"].isin(target_countries)
    ].copy()

    # Confirm that both target countries are present
    countries_found = set(clean_target["country"].unique())

    if countries_found != set(target_countries):
        raise ValueError(
            f"Expected Spain and Türkiye, but found: {sorted(countries_found)}"
        )

    # Confirm that there is one observation per country and year
    if clean_target.duplicated(subset=["country", "year"]).any():
        raise ValueError("Duplicated country-year observations were found.")

    # Check that FAOSTAT yield matches production divided by harvested area
    valid_yield = clean_target.dropna(
        subset=[
            "production_tonnes",
            "area_harvested_ha",
            "yield_kg_ha",
        ]
    ).copy()

    calculated_yield = (
        valid_yield["production_tonnes"] * 1000
        / valid_yield["area_harvested_ha"]
    )

    relative_difference = (
        (calculated_yield - valid_yield["yield_kg_ha"]).abs()
        / valid_yield["yield_kg_ha"]
    )

    if relative_difference.max() > 0.001:
        raise ValueError(
            "FAOSTAT yield values do not match production / harvested area."
        )

    # Save the Spain and Türkiye dataset
    clean_target.to_csv(
        processed_dir / "faostat_clean.csv",
        index=False,
    )

    print("FAOSTAT preprocessing completed.")
    print(f"All countries: {clean_all.shape}")
    print(f"Spain and Türkiye: {clean_target.shape}")
    print(
        f"Maximum yield difference: "
        f"{relative_difference.max() * 100:.4f}%"
    )


if __name__ == "__main__":
    preprocess_faostat()
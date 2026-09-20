from pathlib import Path

import pandas as pd


INDICATOR_MAP = {
    "P": "production_tonnes",
    "C": "consumption_tonnes",
    "E": "exports_tonnes",
    "I": "imports_tonnes",
}

COUNTRY_NAME_MAP = {
    "Azerbaïdjan": "Azerbaijan",
    "Azerbaïdjan (Q)": "Azerbaijan",
    "Bosnie-Herzégovine": "Bosnia and Herzegovina",
    "Bosnia and Herzegovine": "Bosnia and Herzegovina",
    "Czech. Rep.": "Czechia",
    "United King.": "United Kingdom",
    "Oth.non-prod.": "Other non-producing countries",
    "Other pr.coun.": "Other producing countries",
    "E.B.L.U.": "Belgium-Luxembourg",
    "USA": "United States",
    "EU *": "EU",
    "EU  *": "EU",
}

AGGREGATE_ENTITIES = {
    "EU",
    "Belgium-Luxembourg",
    "Other producing countries",
    "Other non-producing countries",
    "World",
}

WORLD_SHEETS = {
    "Prod. ": "P",
    "Imp.": "I",
    "Exp.": "E",
    "Con.": "C",
}


def find_project_root():
    # Find the project root instead of depending on the script location
    current_path = Path(__file__).resolve()

    for parent in current_path.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent

    raise FileNotFoundError("Project root could not be found.")


def normalize_crop_year(value):
    """Turn IOC labels such as 1998/9 or 2000/1 into 1998/99 and 2000/01."""
    text = str(value).strip()
    start_text, _, end_text = text.partition("/")
    if not start_text.isdigit():
        raise ValueError(f"Unexpected crop year: {value!r}")

    start_year = int(start_text)
    end_year = start_year + 1
    return f"{start_year}/{str(end_year)[-2:].zfill(2)}"


def year_status(crop_year):
    if crop_year >= "2025/26":
        return "forecast"
    if crop_year == "2024/25":
        return "provisional"
    return "reported"


def entity_type(country):
    if country == "World":
        return "world"
    if country in AGGREGATE_ENTITIES:
        return "aggregate"
    return "country"


def standardize_country(name):
    name = " ".join(str(name).split())
    return COUNTRY_NAME_MAP.get(name, name)


def load_dashboard(raw_path):
    df = pd.read_csv(raw_path)

    # Keep olive oil only. Table olives are a different product.
    olive_oil = df[df["Product Type"] == "OO"].copy()

    if olive_oil.empty:
        raise ValueError("No olive oil (OO) rows were found in the IOC dashboard file.")

    olive_oil["crop_year"] = olive_oil["Haverst period"].map(normalize_crop_year)
    olive_oil["country"] = olive_oil["Country"].map(standardize_country)
    olive_oil["indicator"] = olive_oil["Indicator"]
    # IOC publishes these figures in thousand tonnes.
    olive_oil["value_tonnes"] = olive_oil["Tonnes"] * 1000
    olive_oil["source"] = "ioc_dashboard"

    return olive_oil[
        ["crop_year", "country", "indicator", "value_tonnes", "source"]
    ]


def _find_year_header_row(sheet):
    for row_index in range(min(20, len(sheet))):
        values = [str(value) for value in sheet.iloc[row_index].tolist() if pd.notna(value)]
        if any(value.startswith("1990/") for value in values):
            return row_index
    raise ValueError("Could not find the 1990/91 header row in the world balances file.")


def _english_country_name(french_name, english_name):
    if pd.notna(english_name) and str(english_name).strip():
        return str(english_name).strip()
    if pd.notna(french_name) and str(french_name).strip():
        return str(french_name).strip()
    return None


def parse_world_balances(raw_path):
    """Parse the official IOC world balance workbook (wide format)."""
    frames = []

    for sheet_name, indicator in WORLD_SHEETS.items():
        sheet = pd.read_excel(raw_path, sheet_name=sheet_name, header=None)
        header_row = _find_year_header_row(sheet)
        year_labels = sheet.iloc[header_row, 2:]

        records = []
        for _, row in sheet.iloc[header_row + 1:].iterrows():
            country = _english_country_name(row.iloc[0], row.iloc[1])
            if country is None:
                continue

            combined_label = " ".join(
                str(value) for value in (row.iloc[0], row.iloc[1], country)
                if pd.notna(value)
            ).upper()
            if "WORLD" in combined_label and "TOTAL" in combined_label:
                country = "World"
            else:
                upper = country.upper()
                if upper.startswith("TOTAL") or "ESTIMATE" in upper or "OFFICIAL FIGURE" in upper:
                    continue
                if country.startswith("*") or "intracommunautaire" in country.lower():
                    continue
                country = standardize_country(country.replace("*", "").strip())

            for year_label, value in zip(year_labels, row.iloc[2:]):
                if pd.isna(year_label):
                    continue
                numeric_value = pd.to_numeric(value, errors="coerce")
                if pd.isna(numeric_value):
                    continue
                records.append(
                    {
                        "crop_year": normalize_crop_year(year_label),
                        "country": country,
                        "indicator": indicator,
                        "value_tonnes": float(numeric_value) * 1000,
                        "source": "ioc_world_balances",
                    }
                )

        frames.append(pd.DataFrame.from_records(records))

    world = pd.concat(frames, ignore_index=True)

    # Some countries appear twice (EU accession). Keep one value per cell.
    world = (
        world.groupby(["crop_year", "country", "indicator"], as_index=False)
        .agg(value_tonnes=("value_tonnes", "first"), source=("source", "first"))
    )
    return world


def to_wide(long_df):
    wide = long_df.pivot_table(
        index=["crop_year", "country"],
        columns="indicator",
        values="value_tonnes",
        aggfunc="first",
    ).reset_index()

    wide = wide.rename(columns=INDICATOR_MAP)
    for column in INDICATOR_MAP.values():
        if column not in wide.columns:
            wide[column] = pd.NA

    wide["crop_year_start"] = wide["crop_year"].str.slice(0, 4).astype(int)
    wide["entity_type"] = wide["country"].map(entity_type)
    wide["year_status"] = wide["crop_year"].map(year_status)

    columns = [
        "country",
        "crop_year",
        "crop_year_start",
        "entity_type",
        "year_status",
        "production_tonnes",
        "consumption_tonnes",
        "exports_tonnes",
        "imports_tonnes",
    ]
    return (
        wide[columns]
        .sort_values(["entity_type", "country", "crop_year_start"])
        .reset_index(drop=True)
    )


def preprocess_ioc():
    project_root = find_project_root()
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    dashboard = load_dashboard(project_root / "data" / "raw" / "ioc_olive_oil.csv")
    world_balances = parse_world_balances(
        project_root / "data" / "raw" / "ioc_world_balances.xls"
    )

    # The dashboard is the main country-level file. Use the world workbook
    # only to fill known gaps, not to overwrite newer dashboard figures.
    # Recent Spain production in the .xls is a repeated placeholder (1250).
    dashboard_keys = dashboard.set_index(
        ["crop_year", "country", "indicator"]
    ).index
    missing = world_balances[
        ~world_balances.set_index(
            ["crop_year", "country", "indicator"]
        ).index.isin(dashboard_keys)
    ].copy()

    turkiye_gap = missing[
        (missing["country"] == "Türkiye")
        & (missing["crop_year"] < "2025/26")
    ]
    spain_missing_production = missing[
        (missing["country"] == "Spain")
        & (missing["indicator"] == "P")
        & (missing["crop_year"] == "2007/08")
    ]
    world_totals = missing[
        (missing["country"] == "World")
        & (missing["crop_year"] < "2025/26")
    ]
    fills = pd.concat(
        [turkiye_gap, spain_missing_production, world_totals],
        ignore_index=True,
    )

    combined = pd.concat([dashboard, fills], ignore_index=True)

    if combined.duplicated(subset=["crop_year", "country", "indicator"]).any():
        raise ValueError("Duplicated crop-year / country / indicator rows were found.")

    clean_all = to_wide(combined)

    # Keep Spain and Türkiye for the main analysis
    target_countries = ["Spain", "Türkiye"]
    clean_target = clean_all[clean_all["country"].isin(target_countries)].copy()

    countries_found = set(clean_target["country"].unique())
    if countries_found != set(target_countries):
        raise ValueError(
            f"Expected Spain and Türkiye, but found: {sorted(countries_found)}"
        )

    if clean_target.duplicated(subset=["country", "crop_year"]).any():
        raise ValueError("Duplicated country-crop-year observations were found.")

    spain_years = set(
        clean_target.loc[clean_target["country"] == "Spain", "crop_year"]
    )
    turkiye_years = set(
        clean_target.loc[clean_target["country"] == "Türkiye", "crop_year"]
    )
    if not {"1990/91", "2024/25"}.issubset(spain_years & turkiye_years):
        raise ValueError("Spain and Türkiye do not both cover 1990/91 through 2024/25.")

    # Production + imports should be close to consumption + exports.
    # The leftover is implied stock change, not an error.
    balance = clean_target.dropna(
        subset=[
            "production_tonnes",
            "imports_tonnes",
            "consumption_tonnes",
            "exports_tonnes",
        ]
    ).copy()
    balance["implied_stock_change_tonnes"] = (
        balance["production_tonnes"]
        + balance["imports_tonnes"]
        - balance["consumption_tonnes"]
        - balance["exports_tonnes"]
    )

    clean_all.to_csv(processed_dir / "ioc_all_countries.csv", index=False)
    clean_target.to_csv(processed_dir / "ioc_clean.csv", index=False)

    print("IOC preprocessing completed.")
    print(f"All entities: {clean_all.shape}")
    print(f"Spain and Türkiye: {clean_target.shape}")
    print(f"Cells filled from world balances: {len(fills)}")
    print(
        "Mean implied stock change, Spain/Türkiye: "
        f"{balance['implied_stock_change_tonnes'].mean():,.0f} tonnes"
    )


if __name__ == "__main__":
    preprocess_ioc()

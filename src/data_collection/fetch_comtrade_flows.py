"""Pull bilateral olive oil trade flows from UN Comtrade for the flow diagram.

WHY THIS SCRIPT EXISTS
The credit-gap charts (src/visualization/italy_credit_gap_charts.py) show
Italy and Tunisia exporting far more olive oil than their own production
predicts, using IOC country-level totals. That's strong circumstantial
evidence. This script gets the direct evidence: who actually ships olive
oil to whom, in what quantity, so we can draw the real flow -- e.g. bulk
oil moving Tunisia -> Italy, Spain -> Italy, Greece -> Italy, and then
Italy -> Germany, Italy -> USA, etc.

SETUP (do this once, ~10 min):
1. Register at https://comtradedeveloper.un.org (free account)
2. Subscribe to the "comtrade - v1" product to get an API key
3. pip install comtradeapicall --break-system-packages
4. Set the key as an environment variable:
       export COMTRADE_API_KEY="your-key-here"
   (or paste it directly into API_KEY below -- fine for a class project,
   just don't commit it to git if you do)

RUN:
    python src/data_collection/fetch_comtrade_flows.py

This writes data/raw/comtrade_olive_oil_flows.csv -- one row per
reporter-partner-year-flow, which italy_flow_sankey.py then reads.

NOTE ON NETWORK: this script must be run somewhere with internet access
to comtradeapi.un.org. It will NOT work inside a restricted sandbox --
run it locally (your Mac) or in Colab.
"""

import os
import time
from pathlib import Path

import pandas as pd

try:
    import comtradeapicall
except ImportError:
    raise SystemExit(
        "Missing dependency. Run:\n"
        "    pip install comtradeapicall --break-system-packages"
    )

API_KEY = os.environ.get("COMTRADE_API_KEY", "")

# HS commodity codes for olive oil (HS 2022 nomenclature)
# 150910 = virgin olive oil          150990 = other (refined / blends)
# If your Comtrade access uses an older HS revision, 1509 alone
# (all olive oil) also works and comtradeapicall will match subheadings.
CMD_CODES = "150910,150990"

# Countries in the story. M49 numeric codes (Comtrade uses these, not ISO).
COUNTRIES = {
    "Italy": 380,
    "Spain": 724,
    "Greece": 300,
    "Tunisia": 788,
    "Turkiye": 792,
    "Morocco": 504,
    "Germany": 276,
    "USA": 842,
    "France": 251,
    "World": 0,  # 0 = report against all partners
}

YEARS = list(range(2010, 2025))


def find_project_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    raise FileNotFoundError("Project root could not be found.")


def fetch_italy_flows():
    """Italy's imports (who ships olive oil INTO Italy) and exports
    (who Italy ships olive oil OUT TO), all partners, by year.
    This is the core data for the Sankey diagram.
    """
    root = find_project_root()
    out_path = root / "data" / "raw" / "comtrade_olive_oil_flows.csv"

    all_rows = []

    for flow_code, flow_label in [("M", "import"), ("X", "export")]:
        print(f"Fetching Italy {flow_label}s, all partners, {YEARS[0]}-{YEARS[-1]}...")
        for year in YEARS:
            try:
                df = comtradeapicall.getFinalData(
                    subscription_key=API_KEY,
                    typeCode="C",          # commodities
                    freqCode="A",          # annual
                    clCode="HS",
                    period=str(year),
                    reporterCode=COUNTRIES["Italy"],
                    cmdCode=CMD_CODES,
                    flowCode=flow_code,
                    partnerCode=None,      # None = all partners
                    partner2Code=None,
                    customsCode=None,
                    motCode=None,
                    maxRecords=2500,
                    format_output="JSON",
                    countOnly=None,
                    includeDesc=True,
                )
                if df is not None and not df.empty:
                    df["flow_label"] = flow_label
                    all_rows.append(df)
                    print(f"  {year}: {len(df)} rows")
                time.sleep(1)  # be polite to the API
            except Exception as e:
                print(f"  {year}: FAILED -- {e}")

    if not all_rows:
        print("No data fetched -- check your API key and network access.")
        return

    combined = pd.concat(all_rows, ignore_index=True)

    # Keep just the columns we need for the Sankey
    keep_cols = [
        "refYear", "flowDesc", "flow_label", "reporterDesc", "partnerDesc",
        "cmdCode", "cmdDesc", "netWgt", "primaryValue",
    ]
    keep_cols = [c for c in keep_cols if c in combined.columns]
    combined = combined[keep_cols]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_path, index=False)
    print(f"\nWrote {len(combined)} rows to {out_path}")


if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit(
            "Set your Comtrade API key first:\n"
            '    export COMTRADE_API_KEY="your-key-here"\n'
            "or paste it into API_KEY in this file."
        )
    fetch_italy_flows()

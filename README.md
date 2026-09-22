# Big-Olive

Our project showcasing the marvelous journey of olive juice. aka olive oil.

**Module Project 1: Data Storytelling**  
Alberto Gomez Soteres & Burak Donbekci

We look at olive production and olive oil trade together. FAOSTAT covers the trees (fruit, area, yield). The International Olive Council covers the oil market (production, consumption, exports, imports). UN Comtrade is used only for Italy's bilateral flows. Spain and Türkiye are the main comparison; Italy is in the picture because the bottle often says Italy even when the harvest does not.

The question we keep coming back to:

> Does being strongly associated with olive oil also mean being the country that grows the most olives?

---

## Key Findings

- **Spain is still the largest olive producer** in the FAOSTAT data, about 8.31 million tonnes in 2024.
- **Türkiye has grown a lot**, from both more harvested area and higher yield.
- **Italy is flatter** over the long run than Spain or Türkiye.
- Growing olives and selling oil are different stories. A country can matter in the oil market without matching that with domestic fruit production.
- Spain and Türkiye both swing hard year to year. Türkiye more so.

On the oil-market side (IOC, 2015–2024, mean of each year's export/production ratio): Tunisia exports about 92% of what it produces, Italy about 75%, Greece about 8.5%. Spain and Türkiye sit in the middle, around a quarter to a third.

---

## Datasets

### FAOSTAT Olives

The agricultural side of the project.

- **What it includes:** olive production, harvested area, and yield by country and year
- **Coverage:** 1961–2024
- **Item:** Olives, item code 260 (fruit, not oil)
- **Source:** [FAOSTAT Crops and Livestock Products](https://www.fao.org/faostat/en/#data/QCL)
- **Raw file:** `data/raw/faostat_olives.csv`
- **Processed:** `data/processed/faostat_all_countries.csv` (every country), `data/processed/faostat_clean.csv` (Spain and Türkiye)

Spain's area and yield are missing for 1961–1979 (`flag = M`). Those cells are left missing.

### International Olive Council

The olive oil market side.

- **What it includes:** production, consumption, imports, and exports by crop year (October–September)
- **Coverage:** 1990/91–2024/25
- **Units:** original files are thousand tonnes; processed files are tonnes
- **Source:** [IOC Statistics](https://www.internationaloliveoil.org/what-we-do/statistics/)
- **Raw files:** `data/raw/ioc_olive_oil.csv`, `data/raw/ioc_world_balances.xls`
- **Processed:** `data/processed/ioc_all_countries.csv`, `data/processed/ioc_clean.csv` (Spain and Türkiye)

The dashboard is the country-level source of truth. The world workbook fills known gaps only (Türkiye 1998/99–2007/08, Spain production in 2007/08, and world totals). Table olives are dropped. `EU` includes Spain, so Spain + EU double-counts. 2024/25 is still provisional.

### UN Comtrade

Used for Italy's olive oil in and out: who ships to Italy, and where Italy ships. This is the input to the Sankey, not a third full dataset.

- **Script:** `src/data_collection/fetch_comtrade_flows.py`
- **Output:** `data/raw/comtrade_olive_oil_flows.csv` (not committed; regenerate locally)

Setup (once):

1. Free account at [comtradedeveloper.un.org](https://comtradedeveloper.un.org)
2. Subscribe to **comtrade - v1** and copy the API key
3. Install the client and set the key in the environment (do not put the key in the repo):

```bash
pip install comtradeapicall plotly
export COMTRADE_API_KEY="your-key-here"
python src/data_collection/fetch_comtrade_flows.py
python src/visualization/italy_flow_sankey.py
```

That writes `outputs/figures/combined/italy_flow_sankey.html`. Open it in a browser.

---

## Repository Structure

```text
Big-Olive/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
│   ├── 01_faostat_exploration_cleaning.ipynb
│   ├── 02_faostat_feature_engineering.ipynb
│   ├── 03_faostat_visualization_analysis.ipynb
│   └── 04_ioc_exploration_cleaning.ipynb
├── src/
│   ├── data_collection/
│   ├── preprocessing/
│   ├── features/
│   └── visualization/
├── outputs/
│   └── figures/
│       ├── faostat/
│       ├── ioc/
│       └── combined/
├── requirements.txt
└── README.md
```

Notebooks can be run from `notebooks/` or from the project root. Paths work either way.

---

## Reproduce the Analysis

```bash
git clone https://github.com/burakdon/Big-Olive.git
cd Big-Olive
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` covers pandas and the Excel readers. Figures also need:

```bash
pip install matplotlib plotly pillow
```

Cleaning:

```bash
python src/preprocessing/preprocess_faostat.py
python src/preprocessing/preprocess_ioc.py
```

FAOSTAT features and Alberto's FAOSTAT charts:

```bash
python src/features/engineer_faostat_features.py
python src/visualization/plot_faostat.py
```

Other figures (already saved under `outputs/figures/`; rerun only if you want to rebuild):

```bash
python src/visualization/growth_and_trade_charts.py
python src/visualization/italy_credit_gap_charts.py
python src/visualization/export_share_timeseries.py
python src/visualization/production_rank_slope.py
python src/visualization/bubble_race_faostat.py
python src/visualization/bubble_race_gif.py
python src/visualization/hero_pictogram.py
```

Processed tables go to `data/processed/`. Figures go to `outputs/figures/`.

Then open the notebooks listed above.

---

## Feature Engineering

The FAOSTAT workflow adds:

- annual production growth
- five-year production averages
- harvested-area growth
- yield growth
- production growth decomposition
- production direction
- year-to-year alternation
- production share within a consistent major-producer group

These are descriptive. They are not causal claims.

Export shares in the combined charts use the **mean of each year's own ratio** (2015–2024), not the ratio of the period averages. That lives in `load_export_share_ratio` in `src/visualization/italy_credit_gap_charts.py`.

---

## Methodological Notes

The three sources are not the same clock, and they are not the same product:

- **FAOSTAT** — olive fruit, calendar year
- **IOC** — olive oil, crop year (October–September)
- **UN Comtrade** — reported trade flows (HS 150910 / 150990)

We do not force them onto one timeline. Trade totals also do not tell you who bottled the oil or whose name is on the label.

---

## Collaboration

We split the work by dataset, reviewed each other on pull requests, and merged into `dev`.

---

## Course

**AIPI 510 — Sourcing Data for Analytics**  
Duke University  
Fall 2026

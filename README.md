# Big-Olive

Our project showcasing the marvelous journey of olive juice. aka olive oil.

**Module Project 1: Data Storytelling**  
Alberto Gomez Soteres & Burak Donbekci

This repository looks at olive oil through two official datasets. FAOSTAT covers the agricultural side (olive trees: production, harvested area, and yield), with a focus on Spain and Türkiye. IOC covers the olive oil market (production, consumption, exports, and imports) for the same two countries, against a global baseline.

## Datasets

### FAOSTAT olives (QCL)

- **What it is:** Country-year olive production, area harvested, and yield, 1961–2024.
- **Item:** Olives (item code 260), not olive oil.
- **Source:** [FAOSTAT Crops and livestock products](https://www.fao.org/faostat/en/#data/QCL)
- **Raw file:** `data/raw/faostat_olives.csv`

### International Olive Council balances

- **What it is:** Olive oil production, consumption, exports, and imports by country and crop year (October–September), 1990/91–2024/25.
- **Units in the original files:** thousand tonnes. Processed files are converted to tonnes.
- **Sources:**
  - IOC Statistics Dashboard download: [IOC Statistics](https://www.internationaloliveoil.org/what-we-do/statistics/)
  - World balance sheets, November 2025 session: [HO-W.xls](https://www.internationaloliveoil.org/wp-content/uploads/2025/12/HO-W.xls)
- **Raw files:** `data/raw/ioc_olive_oil.csv`, `data/raw/ioc_world_balances.xls`

The dashboard is the main country-level file. The world workbook is used only to fill known gaps (Türkiye 1998/99–2007/08, Spain production in 2007/08, and world totals).

## Reproduce

```bash
git clone https://github.com/burakdon/Big-Olive.git
cd Big-Olive
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/preprocessing/preprocess_faostat.py
python src/preprocessing/preprocess_ioc.py
```

Then open:

- `notebooks/01_faostat_exploration_cleaning.ipynb`
- `notebooks/04_ioc_exploration_cleaning.ipynb`

Run notebooks from the `notebooks/` folder or from the project root. Paths are set up for both.

## Repository layout

```
data/raw/            original extracts
data/processed/      cleaned tables
notebooks/           exploration and analysis
src/preprocessing/   reproducible cleaning scripts
src/features/        feature engineering scripts
src/visualization/   figure scripts
outputs/figures/     saved plots
```

Each teammate works on one dataset, then we review each other through pull requests.

# Big-Olive

**Module Project 1: Data Storytelling**  
Alberto Gomez Soteres & Burak Donbekci

Big Olive explores the relationship between **olive production and olive oil trade**.

Using public data from FAOSTAT, the International Olive Council, and UN Comtrade, we compare the agricultural and market roles of major Mediterranean countries, with particular attention to Spain, Türkiye, and Italy.

Our main question is simple:

> Does being strongly associated with olive oil also mean being the country that grows the most olives?

---

## Key Findings

- **Spain remains the largest olive producer** in the FAOSTAT data, reaching about 8.31 million tonnes in 2024.
- **Türkiye has expanded strongly**, through a combination of larger harvested area and higher yield.
- **Italy follows a much flatter long-term production path** than Spain and Türkiye.
- Agricultural production and international trade do not tell the same story: a country can play an important role in the olive oil market without having the same domestic production trajectory.
- Spain and Türkiye also show strong year-to-year variation in olive production, especially Türkiye.

---

## Datasets

### FAOSTAT Olives

FAOSTAT provides the agricultural side of the project.

- **What it includes:** olive production, harvested area, and yield by country and year
- **Coverage:** 1961-2024
- **Item:** Olives, item code 260
- **Source:** [FAOSTAT Crops and Livestock Products](https://www.fao.org/faostat/en/#data/QCL)
- **Raw file:** `data/raw/faostat_olives.csv`

> FAOSTAT measures olive fruit, not olive oil.

### International Olive Council

The International Olive Council provides the olive oil market side of the project.

- **What it includes:** production, consumption, imports, and exports
- **Coverage:** 1990/91-2024/25 crop years
- **Source:** [International Olive Council Statistics](https://www.internationaloliveoil.org/what-we-do/statistics/)
- **Raw files:**
  - `data/raw/ioc_olive_oil.csv`
  - `data/raw/ioc_world_balances.xls`

The dashboard data is used as the main country-level source. The world workbook is used to supplement known gaps and world totals.

### UN Comtrade

UN Comtrade is used to examine bilateral olive oil trade flows, including Italy's major suppliers and export destinations.

Data collection script:

```text
src/data_collection/fetch_comtrade_flows.py
```

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
├── requirements.txt
└── README.md
```

---

## Reproduce the Analysis

Clone the repository:

```bash
git clone https://github.com/burakdon/Big-Olive.git
cd Big-Olive
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run preprocessing:

```bash
python src/preprocessing/preprocess_faostat.py
python src/preprocessing/preprocess_ioc.py
```

Run FAOSTAT feature engineering:

```bash
python src/features/engineer_faostat_features.py
```

Generate the FAOSTAT visualizations:

```bash
python src/visualization/plot_faostat.py
```

Processed datasets are saved in:

```text
data/processed/
```

Final figures are saved in:

```text
outputs/figures/
```

---

## Feature Engineering

The FAOSTAT workflow includes:

- annual production growth
- five-year production averages
- harvested-area growth
- yield growth
- production growth decomposition
- production direction
- year-to-year alternation
- production share within a consistent major-producer comparison group

These features are descriptive and are not interpreted as causal relationships.

---

## Methodological Notes

The three main data sources describe different parts of the olive oil system:

- **FAOSTAT** reports olive fruit by calendar year
- **IOC** reports olive oil by crop year
- **UN Comtrade** reports international trade flows

Because these datasets use different definitions and time periods, they are not treated as perfectly synchronized observations.

Trade data also represents aggregate flows between countries. It does not trace individual batches of olive oil or directly identify where branding or retail value is captured.

---

## Collaboration

The project was developed using GitHub branches and pull requests.

Each team member worked on separate parts of the analysis and reviewed changes before integration into the shared development branch.

---

## Course

**AIPI 510 - Sourcing Data for Analytics**  
Duke University  
Fall 2026

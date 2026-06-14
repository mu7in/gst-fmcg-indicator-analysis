# GST Collections as a Leading Indicator for FMCG Stock Returns

A time-series analysis of whether monthly GST data can predict quarterly stock returns for India's major FMCG companies — built with Python, PostgreSQL, and Power BI.

---

## The Question

GST is a consumption tax. When people spend more on everyday goods — soaps, biscuits, packaged food, shampoo — GST collections go up. FMCG companies sell exactly those goods. So the question I wanted to test was: does a rise in GST collections in one quarter actually show up in FMCG stock returns the following quarter?

It sounds straightforward but there are real complications. GST data is aggregate — you get total collections, not FMCG-specific ones. It's a proxy, not a direct signal. And stock prices react to dozens of things at once, so isolating any single variable is hard. The project accounts for all of that.

---

## What I Found

The short version: there is a detectable signal, but it is subtle and depends heavily on the lag.

Running a pooled OLS regression across all seven companies and 30 quarters, using Lag 1 (prior quarter GST growth) and Lag 2 (two quarters prior) as predictors:

- The model is statistically significant — F-test p-value of 0.0003
- R² = 0.094, meaning GST lags account for roughly 9.4% of the variance in stock returns
- Lag 1 coefficient is positive (0.125, p = 0.009): stronger GST growth one quarter ago predicts better stock returns this quarter
- Lag 2 coefficient is negative (−0.168, p = 0.0002): that same earlier GST growth predicts a pullback two quarters out

The negative Lag 2 coefficient is the most interesting part. It suggests markets partially price in the GST signal one quarter ahead, then correct as the effect fades. I'm calling this an echo pattern in the write-up.

Granger causality tests came back without clear evidence of causality at the per-company level, which is expected — with only 25 usable observations per company, the test simply doesn't have enough power. That's a limitation I've documented.

The COVID quarters (2020 Q2 and Q3) are a structural break. GST collapsed 42% YoY in Q2 2020 but FMCG stocks like Britannia and Godrej Consumer actually surged — people panic-bought packaged food. Excluding those two quarters makes Lag 1 significant at p = 0.010. I run both versions in the analysis.

---

## Data

| Source | What it covers | Period |
|---|---|---|
| GST.gov.in / Kaggle | Monthly state-wise GST collections | Jul 2017 – Dec 2024 |
| Yahoo Finance (yfinance) | Daily OHLCV for 7 NSE-listed FMCG stocks | Jul 2017 – Dec 2024 |
| Screener.in | Annual P&L for 7 companies | FY2016 – FY2025 |

**Companies:** HUL, ITC, Nestle India, Britannia, Dabur, Marico, Godrej Consumer Products

One thing worth being upfront about: quarterly revenue data from Screener only goes back to late 2023, which is too short for statistical analysis. So the primary dependent variable throughout is quarterly stock returns computed from daily prices, not reported revenues. The annual revenue data (which goes back to FY2017) is used as a supplementary check.

---

## Stack

Python for data collection, cleaning, and statistical analysis. PostgreSQL (via psycopg2 + SQLAlchemy) for storage and querying. DBeaver as the SQL client. Power BI Desktop for the dashboard.

---

## Project Structure

```
gst_fmcg-indicator-analysis/
│
├── 02_data_cleaning.py          # Parses 9 GST CSVs, cleans stock and revenue data
├── 03_build_database.py         # Loads cleaned data into PostgreSQL
├── 04_statistical_analysis.py   # Correlation, OLS regression, Granger tests, charts
├── 05_export_for_powerbi.py     # Exports pre-joined flat tables for Power BI
│
├── sql/
│   ├── q1_gst_monthly_trend.sql
│   ├── q2_gst_quarterly_growth.sql
│   ├── q3_best_quarter_per_company.sql
│   ├── q4_gst_vs_stock_same_quarter.sql
│   ├── q5_lagged_gst_vs_stock.sql          # Core query
│   ├── q6_avg_return_per_company.sql
│   ├── q7_negative_gst_quarters.sql
│   ├── q8_rolling_avg_gst_vs_returns.sql
│   └── q9_annual_gst_vs_revenue.sql
│
├── data/
│   ├── raw/                     # Original downloaded files, untouched
│   ├── cleaned/                 # Output of 02_data_cleaning.py
│   └── powerbi/                 # Output of 05_export_for_powerbi.py
│
└── outputs/
    └── charts/                  # Six charts from 04_statistical_analysis.py
```

---

## How It Was Built

The project ran across seven phases. Here's what each one actually involved.

**Phase 1 — Environment setup.** Python 3.11, PostgreSQL, DBeaver, Power BI Desktop. Standard stuff. The only decision worth mentioning is choosing PostgreSQL over SQLite — it's what professional analyst environments actually use, and it meant the SQL queries could use proper data types (`DATE`, `NUMERIC`, `SERIAL`) rather than SQLite's loosely typed equivalents.

**Phase 2 — Data collection.** GST data came from Kaggle as nine separate CSV files, one per financial year (2017-18 through 2025-26). Stock prices were pulled using `yfinance` for all seven companies from July 2017 to December 2024. The FMCG revenue data from Screener.in turned out to be the messiest part — the quarterly export only goes back to late 2023, which is not enough for analysis. That's what pushed the primary dependent variable toward stock returns rather than reported revenues, since price data goes back the full seven years.

**Phase 3 — Data cleaning.** The GST CSVs have a five-row merged-cell header, state-wise columns, and comma-formatted numbers. Each file also labels its Grand Total row differently — older files say "Grand Total", the 2024-25 and 2025-26 files switched to "Domestic GST Collection - All India". The cleaning script handles both. Stock prices needed two metadata rows skipped before the actual OHLCV data started. Screener's Excel files had the P&L section starting at a different row offset per company, so the script searches by row label rather than relying on fixed offsets. Six cleaned CSVs came out the other end.

**Phase 4 — SQL database.** Six tables loaded into PostgreSQL via SQLAlchemy. Nine query files in the `sql/` folder, written to cover progressively more complex concepts — starting from basic `SELECT` and `ORDER BY` through to `LAG()` window functions, CTEs, and rolling averages with `ROWS BETWEEN`. The lagged join in `q5_lagged_gst_vs_stock.sql` is the core analytical query the whole project is built around.

**Phase 5 — Statistical analysis.** Pearson correlations tested across five lag lengths (Lag 0 through Lag 4) to find where the signal was strongest. Lag 1 and Lag 2 together went into a pooled OLS regression. Granger causality was tested per company using `statsmodels`, though with 25 observations per company the tests don't have much power. Rolling 8-quarter correlations were computed to see whether the signal was stable across the period (it isn't — which is itself a finding). Six charts saved to `outputs/charts/`.

**Phase 6 — Power BI dashboard.** Rather than connecting Power BI directly to PostgreSQL (which requires an additional ODBC driver and is fiddly to set up), the analysis tables were pre-joined and pre-lagged in Python and exported as flat CSVs to `data/powerbi/`. This also meant the lagged values and rolling correlations — which are complex to reproduce in DAX — were already computed before the data hit Power BI. Three dashboard pages: GST Trends, FMCG Performance, and The Signal.

**Phase 7 — Documentation.** This README, plus `FINDINGS.md` which goes deeper into the statistical interpretation and the interview talking points.

---

## How to Run It

**1. Install dependencies**
```bash
pip install pandas numpy yfinance openpyxl statsmodels matplotlib seaborn scipy psycopg2-binary sqlalchemy
```

**2. Set up PostgreSQL**

Create a database called `gst_fmcg`, then open `03_build_database.py` and update the `DB_PASS` variable on line 18 to your PostgreSQL password.

**3. Run the pipeline in order**

```bash
python 02_data_cleaning.py
python 03_build_database.py
python 04_statistical_analysis.py
python 05_export_for_powerbi.py
```

Each script picks up where the previous one left off. `02` writes to `data/cleaned/`, `03` loads that into PostgreSQL, `04` reads from `data/cleaned/` and writes charts to `outputs/charts/`, and `05` writes to `data/powerbi/` for the dashboard.

**4. SQL queries**

Open DBeaver, connect to `localhost:5432/gst_fmcg`, and run any file from the `sql/` folder. `q5_lagged_gst_vs_stock.sql` is the one that matters most — it shows the lagged GST growth alongside stock returns for the following quarter.

**5. Power BI**

Open Power BI Desktop → Get Data → load all six CSVs from `data/powerbi/` → follow the relationship setup and DAX measures in the project documentation.

---

## SQL Concepts Covered

The nine query files go from basic to advanced in a deliberate order. By the end you have working examples of window functions (`RANK`, `LAG`, rolling `AVG OVER`), CTEs, multi-table joins, and aggregate filtering — all on a real dataset with a genuine analytical question behind them.

---

## Limitations

A few honest ones:

The 30-quarter window is not long enough to make confident causal claims. GST was only introduced in July 2017, so that's a hard ceiling on the data. More quarters would strengthen everything.

Granger causality needs more per-company observations than we have here. The pooled analysis is more informative than the per-company tests.

This is a domestic GST aggregate — it captures all consumption, not just FMCG. The assumption that FMCG tracks aggregate consumption is reasonable but not perfect, and it breaks down during supply disruptions (COVID being the obvious case).

Stock returns are also influenced by global risk-off periods, RBI rate decisions, and company-specific events — none of which are controlled for in this single-variable setup.

---

## Author

Muhsin — B.Tech Electronics & Instrumentation, MIT Manipal | Minor in Data Science

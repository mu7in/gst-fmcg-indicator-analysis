# GST Indicator Model for FMCG Stock Returns

A time-series analysis of whether monthly GST data can predict quarterly stock returns for India's major FMCG companies, built with Python, PostgreSQL, and Power BI.

---

## Research Question

GST is a consumption tax. When spending on everyday goods rises (soaps, biscuits, packaged food, shampoo), GST collections increase. FMCG companies sell exactly those goods, which raises a testable question: does a rise in GST collections in one quarter predict FMCG stock returns in the following quarter?

The analysis accounts for real complications. GST data is aggregate, capturing total collections rather than FMCG-specific ones, and functions as a proxy rather than a direct signal. Stock prices also respond to many variables simultaneously, making any single-variable analysis inherently limited in its explanatory scope.

---

## Key Findings

A pooled OLS regression was run across seven companies and 30 quarters, using Lag 1 (prior quarter GST growth) and Lag 2 (two quarters prior) as predictors.

### OLS Regression

- **F-test p-value: 0.0003** -- The model is statistically significant.
- **R² = 0.094** -- GST lags account for approximately 9.4% of the variance in stock returns.
- **Lag 1 coefficient: +0.125 (p = 0.009)** -- Stronger GST growth one quarter prior predicts higher FMCG stock returns in the following quarter.
- **Lag 2 coefficient: -0.168 (p = 0.0002)** -- The same earlier GST growth predicts a correction two quarters out. Markets appear to partially price in the signal one quarter ahead and then correct as the effect fades. This pattern is referred to as the echo effect in the analysis.

### Granger Causality

- No clear evidence of causality was found at the per-company level.
- With only 25 usable observations per company, the tests lack sufficient statistical power. This is a documented limitation of the analysis.

### Structural Break: COVID Quarters

- 2020 Q2 and Q3 constitute a structural break in the data.
- GST collections collapsed 42% year-on-year in Q2 2020, yet FMCG stocks such as Britannia and Godrej Consumer surged, driven by panic-buying of packaged food.
- Excluding these two quarters strengthens Lag 1 significance to p = 0.010. Both versions (full dataset and COVID-excluded) are reported in the analysis.

### Rolling Correlations

- An 8-quarter rolling correlation was computed to assess whether the signal held consistently across the full period.
- The relationship between GST growth and FMCG returns is not stable over time, shifting across different macroeconomic regimes. This is treated as a finding in its own right.

---

## Data

| Source | What it covers | Period |
|---|---|---|
| GST.gov.in / Kaggle | Monthly state-wise GST collections | Jul 2017 -- Dec 2024 |
| Yahoo Finance (yfinance) | Daily OHLCV for 7 NSE-listed FMCG stocks | Jul 2017 -- Dec 2024 |
| Screener.in | Annual P&L for 7 companies | FY2016 -- FY2025 |

**Companies:** HUL, ITC, Nestle India, Britannia, Dabur, Marico, Godrej Consumer Products

Quarterly revenue data from Screener.in extends only to late 2023, which is insufficient for the full analysis window. The primary dependent variable is therefore quarterly stock returns computed from daily price data, covering the complete seven-year period. Annual revenue data (FY2017 onwards) is used as a supplementary check.

---

## Stack

- **Python**
  - `pandas`, `numpy` -- data processing and numerical computation
  - `yfinance` -- stock price collection
  - `statsmodels` -- OLS regression and Granger causality tests
  - `scipy` -- Pearson correlation
  - `matplotlib`, `seaborn` -- chart generation
  - `openpyxl` -- reading Screener.in Excel exports
- **PostgreSQL** (via `psycopg2` + `SQLAlchemy`) -- storage and querying
- **DBeaver** -- SQL client
- **Power BI Desktop** -- dashboard and visualisation

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

The project ran across seven phases.

**Phase 1 -- Environment setup.** Python 3.11, PostgreSQL, DBeaver, and Power BI Desktop. PostgreSQL was chosen over SQLite to align with professional analyst environments, enabling the use of proper data types (`DATE`, `NUMERIC`, `SERIAL`) rather than SQLite's loosely typed equivalents.

**Phase 2 -- Data collection.** GST data came from Kaggle as nine separate CSV files, one per financial year (2017-18 through 2025-26). Stock prices were collected using `yfinance` for all seven companies from July 2017 to December 2024. Quarterly revenue data from Screener.in extends only to late 2023, which is insufficient for the full analysis window. This is what directed the primary dependent variable toward stock returns rather than reported revenues, since price data covers the complete seven years.

**Phase 3 -- Data cleaning.** The GST CSVs carry a five-row merged-cell header, state-wise columns, and comma-formatted numbers. Each file also labels its Grand Total row differently: older files use "Grand Total", while the 2024-25 and 2025-26 files switched to "Domestic GST Collection - All India". The cleaning script handles both conventions. Stock prices required two metadata rows to be skipped before the OHLCV data began. Screener's Excel files had the P&L section starting at a different row offset per company, so the script searches by row label rather than relying on fixed offsets. Six cleaned CSVs were produced.

**Phase 4 -- SQL database.** Six tables were loaded into PostgreSQL via SQLAlchemy. Nine query files in the `sql/` folder address progressively complex analytical questions, from basic aggregation through to `LAG()` window functions, CTEs, and rolling averages with `ROWS BETWEEN`. The lagged join in `q5_lagged_gst_vs_stock.sql` is the core analytical query the project is built around.

**Phase 5 -- Statistical analysis.** Pearson correlations were tested across five lag lengths (Lag 0 through Lag 4) to identify where the signal was strongest. Lag 1 and Lag 2 together went into a pooled OLS regression. Granger causality was tested per company using `statsmodels`. Rolling 8-quarter correlations were computed to assess whether the signal held consistently across the period. Six charts were saved to `outputs/charts/`.

**Phase 6 -- Power BI dashboard.** Rather than connecting Power BI directly to PostgreSQL (which requires an additional ODBC driver), the analysis tables were pre-joined and pre-lagged in Python and exported as flat CSVs to `data/powerbi/`. This ensured that lagged values and rolling correlations were already computed before the data reached Power BI, avoiding complex DAX reproduction. Three dashboard pages: GST Trends, FMCG Performance, and The Signal.

**Phase 7 -- Documentation.** This README, plus `FINDINGS.md`, which covers the statistical interpretation in greater depth along with interview talking points.

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

Open DBeaver, connect to `localhost:5432/gst_fmcg`, and run any file from the `sql/` folder. `q5_lagged_gst_vs_stock.sql` is the core query: it joins lagged GST growth values against subsequent quarterly stock returns, forming the basis of the regression analysis.

**5. Power BI**

Open Power BI Desktop, load all six CSVs from `data/powerbi/` via Get Data, and follow the relationship setup and DAX measures in the project documentation.

---

## SQL Implementation

Nine query files cover the full analytical pipeline. The core query (`q5_lagged_gst_vs_stock.sql`) constructs lagged GST growth values alongside subsequent quarterly stock returns, forming the direct input for the OLS regression. Supporting queries implement window functions (`RANK`, `LAG`, rolling `AVG OVER`), CTEs, multi-table joins, and aggregate filtering across the full nine-year dataset.

---

## Limitations

- **Data window:** GST was introduced in July 2017, limiting the analysis to 30 quarters. A longer time series would strengthen the reliability of causal inferences.
- **Granger causality power:** With only 25 observations per company, per-company causality tests lack sufficient statistical power. The pooled OLS analysis is more informative than the per-company tests.
- **Aggregate proxy:** The GST figures used are national aggregates, not FMCG-specific. The assumption that FMCG revenues track aggregate consumption holds under normal conditions but breaks down during supply disruptions such as COVID-19.
- **Omitted variables:** Stock returns are influenced by global risk sentiment, RBI monetary policy decisions, and company-specific events, none of which are controlled for in this single-variable framework.

---

## Author

Muhsin | B.Tech Electronics & Instrumentation, MIT Manipal | Minor in Data Science

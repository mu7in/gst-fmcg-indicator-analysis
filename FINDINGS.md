# Analysis Findings

This document covers the statistical findings in detail and is intended to be read alongside the Power BI dashboard.

---

## Lag Structure

Pearson correlations between GST year-on-year growth and quarterly stock returns were tested at five lag lengths before any formal regression. Results across 168 pooled observations:

| Lag | Pearson r | p-value | Note |
|---|---|---|---|
| 0 (same quarter) | -0.033 | 0.659 | No relationship |
| 1 quarter prior | +0.129 | 0.096 | Borderline |
| 2 quarters prior | -0.235 | 0.002 | Significant |
| 3 quarters prior | -0.145 | 0.066 | Borderline |
| 4 quarters prior | +0.011 | 0.888 | No relationship |

The Lag 1 and Lag 2 pattern shaped the regression design. A positive signal at Lag 1 followed by a negative one at Lag 2 suggests markets partially absorb the GST signal one quarter ahead and then correct. Whether that reversal reflects mean reversion or sampling noise across 30 quarters is difficult to isolate definitively.

---

## OLS Regression

A pooled OLS regression was run across all seven companies using Lag 1 and Lag 2 GST year-on-year growth as predictors:

```
quarterly_return = 3.65 + 0.125 × lag1_gst_yoy − 0.168 × lag2_gst_yoy
```

- **F-test p-value: 0.0003** -- The model is statistically significant.
- **R² = 0.094** -- GST lags account for approximately 9.4% of the variance in stock returns. This is modest but meaningful for a single macroeconomic proxy; real equity return models also incorporate interest rates, global risk sentiment, input costs, and company-specific factors, none of which are included here.
- **Lag 1 coefficient: +0.125 (p = 0.009)** -- Stronger GST growth one quarter prior predicts higher FMCG stock returns in the following quarter.
- **Lag 2 coefficient: -0.168 (p = 0.0002)** -- The same earlier GST growth predicts a correction two quarters out, consistent with the echo effect described above.
- **Intercept: 3.65** -- The model predicts approximately 3.7% average quarterly return when GST growth is flat, close to the observed unweighted average of 3.4% across all seven companies over the full period.

---

## COVID as a Structural Break

Q2 2020 (Apr-Jun 2020) saw GST collections fall 42% year-on-year as the lockdown suppressed economic activity. During those same quarters, FMCG stocks diverged sharply from the GST signal:

- **Britannia:** +35% return in Q3 2020
- **Godrej Consumer:** +32%
- **Dabur:** +22%

Lockdowns increased demand for packaged and branded goods through panic-buying, institutional rotation into consumer staples as a defensive trade, and sustained rural demand. The standard GST-to-returns relationship broke down during this period.

Excluding Q2 and Q3 2020:

- **Lag 1 significance:** improves from p = 0.096 to p = 0.010
- **Pooled correlation:** improves from r = 0.129 to r = 0.202

Both versions (full dataset and COVID-excluded) are reported in the analysis. The COVID quarters are flagged in the Power BI dashboard with a toggle slicer.

---

## Granger Causality

No statistically significant Granger causality was found from GST growth to stock returns at the per-company level. P-values ranged from 0.18 (Nestle, Lag 1) to 0.89 (Marico).

The result is attributable to sample size rather than an absence of a relationship. Granger causality tests evaluate whether past values of X improve predictions of Y beyond Y's own past values. With only 25 usable observations per company, the F-test lacks sufficient statistical power; at least 50 observations per variable are generally required for reliable results. The pooled analysis (168 observations) is more statistically meaningful and is treated as the primary result.

---

## Annual Revenue Check

Correlating annual GST growth with annual revenue growth (pooled, n = 49) produced r = -0.035 (p = 0.81), indicating no meaningful relationship.

Annual aggregation reduces the observation count significantly, and revenue growth is affected by pricing decisions, distribution expansion, and category mix in ways that quarterly stock returns are not. The annual revenue data serves as background context rather than a primary analytical variable.

---

## Rolling Correlations

The rolling 8-quarter correlation between Lag 1 GST year-on-year growth and stock returns fluctuates between approximately -0.5 and +0.6 across the full period, with no consistent direction. The correlation is positive and relatively stable from 2023 to early 2024, representing the most recent period of normal market conditions in the dataset.

The instability of the rolling correlation is treated as a finding: the GST-to-returns relationship shifts across macroeconomic regimes and should not be relied upon as a standalone predictive signal.

---

## Summary

- **OLS model:** Statistically significant (F-test p = 0.0003); R² of 9.4% from a single macroeconomic proxy with no additional controls.
- **Lag structure:** Positive Lag 1 and negative Lag 2 coefficients suggest partial pricing-in of the consumption signal one quarter ahead, followed by a correction (echo effect).
- **COVID quarters:** A genuine structural break. Excluding 2020 Q2 and Q3 strengthens the signal. Both versions are reported.
- **Granger causality:** Inconclusive at the per-company level due to insufficient observations. The pooled analysis is the more reliable result.
- **Rolling correlations:** The signal is not stable over time, limiting its utility as a standalone predictive tool.
- **Annual revenue:** No meaningful correlation with GST growth. Used as supplementary context only.

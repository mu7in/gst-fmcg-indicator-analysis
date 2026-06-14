# Analysis Findings

This document records what the numbers actually showed, and the reasoning behind how I interpret them. It's meant to be read alongside the Power BI dashboard rather than as a standalone report.

---

## The Lag Structure

Before running any formal test, I checked Pearson correlation between GST YoY growth and stock returns at five different lag lengths — from zero (same quarter) to four quarters prior. The results:

| Lag | Pearson r | p-value | Note |
|---|---|---|---|
| 0 (same quarter) | −0.033 | 0.659 | No relationship |
| 1 quarter prior | +0.129 | 0.096 | Borderline |
| 2 quarters prior | −0.235 | 0.002 | Significant |
| 3 quarters prior | −0.145 | 0.066 | Borderline |
| 4 quarters prior | +0.011 | 0.888 | Nothing |

The pattern at Lag 1 and Lag 2 is what drove the rest of the analysis. A positive signal at Lag 1 followed by a negative one at Lag 2 suggests the market reacts to the GST data one quarter out, then partially reverses. Whether that reversal is mean reversion or just noise from a small sample is hard to say definitively with 30 quarters.

---

## OLS Regression

Putting Lag 1 and Lag 2 together in a pooled OLS across all seven companies:

```
quarterly_return = 3.65 + 0.125 × lag1_gst_yoy − 0.168 × lag2_gst_yoy
```

Model F-test p-value: 0.0003
R²: 0.094

Both coefficients are significant (Lag 1 at p = 0.009, Lag 2 at p = 0.0002). The model explains about 9.4% of the variance in stock returns, which is modest but reasonable for a single macroeconomic proxy. Real equity return models include interest rates, global risk sentiment, input costs, and company-specific factors — none of which are in here.

The intercept of 3.65 means the model predicts roughly 3.7% average quarterly return even when GST growth is flat. That's close to what the data shows — the unweighted average quarterly return across all seven companies over the period was around 3.4%.

---

## COVID as a Structural Break

Q2 2020 (Apr–Jun 2020) saw GST collections fall 42% YoY — the lockdown essentially paused the economy. But during those same quarters, FMCG stocks behaved oddly:

- Britannia: +35% return in Q3 2020
- Godrej Consumer: +32%
- Dabur: +22%

This happened because lockdowns actually increased demand for packaged and branded goods — people panic-bought, institutions shifted toward consumer staples as a defensive trade, and rural demand held up. The GST-returns relationship broke down entirely during this period.

Excluding Q2 and Q3 2020 strengthens Lag 1 from p = 0.096 to p = 0.010, and the pooled correlation improves from r = 0.129 to r = 0.202. Both versions are reported in the analysis. The COVID quarters are flagged in the Power BI dashboard with a toggle slicer so anyone viewing the report can see both pictures.

---

## Granger Causality

None of the seven companies showed statistically significant Granger causality from GST growth to stock returns. The p-values ranged from 0.18 (Nestle, Lag 1) to 0.89 (Marico).

This is not as negative as it sounds. Granger causality tests work by asking whether past values of X help predict Y beyond Y's own past values. With 25 usable observations per company, the test has very little power. A standard rule of thumb is that you need at least 50 observations per variable for the F-test to be reliable. The pooled analysis — which has 168 observations — is more meaningful than the per-company tests.

---

## Annual Revenue Check

The Screener data gives annual revenue going back to FY2017. Correlating annual GST growth with annual revenue growth (pooled, n = 49) gave r = −0.035, p = 0.81 — essentially no relationship.

This is not surprising. Annual data has far fewer points, and revenue growth is affected by pricing, distribution expansion, and category mix in ways that quarterly stock returns are not. It also means the annual revenue data is more of a background context layer than an analytical variable in this project.

---

## What The Rolling Correlation Shows

The rolling 8-quarter correlation (between Lag 1 GST YoY and stock returns) fluctuates between roughly −0.5 and +0.6 across the period, with no consistent direction. It's positive and somewhat stable from 2023 to early 2024, which is the most recent evidence that the signal has been working in normal market conditions.

The instability of the rolling correlation is itself a finding — it means the GST-to-returns relationship is not stable across time, which limits how much anyone should rely on it as a standalone trading signal.

---

## Summary For Interviews

If someone asks about this project in an interview, the core points are:

The OLS model is statistically significant (p = 0.0003) with Lag 1 and Lag 2 GST YoY growth as predictors. R² of 9.4% is modest but meaningful for a single macro variable with no controls.

The positive Lag 1, negative Lag 2 pattern suggests partial pricing-in of the consumption signal — the market reacts one quarter ahead, then reverts.

COVID is a genuine structural break and excluding those quarters improves the signal. Both versions are reported honestly.

GST is a proxy for aggregate consumption, not an FMCG-specific measure. The underlying assumption — that FMCG revenues track aggregate consumption — is reasonable in normal times but breaks down during supply disruptions.

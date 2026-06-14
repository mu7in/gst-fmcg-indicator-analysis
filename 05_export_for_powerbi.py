# =============================================================
# PHASE 6 PREP: Export Power BI-Ready Tables
# GST-FMCG Indicator Analysis Project
# =============================================================
# Run this before opening Power BI.
# It creates 6 flat CSV files in data/powerbi/ that you load
# directly into Power BI Desktop.
# =============================================================

import pandas as pd
import numpy as np
from scipy import stats
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('data/powerbi', exist_ok=True)

gst_m   = pd.read_csv('data/cleaned/gst_monthly_clean.csv')
gst_q   = pd.read_csv('data/cleaned/gst_quarterly_clean.csv').sort_values(['cal_year','quarter']).reset_index(drop=True)
returns = pd.read_csv('data/cleaned/stock_quarterly_returns.csv')
annual  = pd.read_csv('data/cleaned/fmcg_annual_revenue.csv')

# Precompute lag columns needed across tables
gst_q['lagged_gst_yoy'] = gst_q['yoy_growth_pct'].shift(1)
gst_q['lag2_gst_yoy']   = gst_q['yoy_growth_pct'].shift(2)
gst_q['period_label']   = gst_q['cal_year'].astype(str) + '-Q' + gst_q['quarter'].astype(str)

# ── TABLE 1: Monthly GST ────────────────────────────────────
pbi_gst_m = gst_m.copy()
pbi_gst_m['date']           = pd.to_datetime(pbi_gst_m['date'])
pbi_gst_m['quarter']        = pbi_gst_m['date'].dt.quarter
pbi_gst_m['gst_billion']    = (pbi_gst_m['total_collection_crore'] / 100).round(2)
pbi_gst_m = pbi_gst_m.rename(columns={'total_collection_crore': 'gst_crore'})
pbi_gst_m.to_csv('data/powerbi/pbi_gst_monthly.csv', index=False)
print(f"[1/6] pbi_gst_monthly.csv        → {len(pbi_gst_m)} rows")

# ── TABLE 2: Quarterly GST ──────────────────────────────────
pbi_gst_q = gst_q[['cal_year','quarter','total_gst_crore','qoq_growth_pct','yoy_growth_pct','period_label']].copy()
pbi_gst_q = pbi_gst_q.rename(columns={'cal_year': 'year'})
pbi_gst_q['gst_thousand_crore'] = (pbi_gst_q['total_gst_crore'] / 1000).round(2)
pbi_gst_q.to_csv('data/powerbi/pbi_gst_quarterly.csv', index=False)
print(f"[2/6] pbi_gst_quarterly.csv      → {len(pbi_gst_q)} rows")

# ── TABLE 3: Stock Quarterly Returns ────────────────────────
pbi_ret = returns.copy()
pbi_ret['period_label']    = pbi_ret['year'].astype(str) + '-Q' + pbi_ret['quarter'].astype(str)
pbi_ret['return_positive'] = pbi_ret['quarterly_return_pct'] > 0
pbi_ret.to_csv('data/powerbi/pbi_stock_returns.csv', index=False)
print(f"[3/6] pbi_stock_returns.csv      → {len(pbi_ret)} rows")

# ── TABLE 4: Signal Analysis (pre-joined, pre-lagged) ───────
signal = returns.merge(
    gst_q[['cal_year','quarter','yoy_growth_pct','lagged_gst_yoy','lag2_gst_yoy','period_label']],
    left_on=['year','quarter'], right_on=['cal_year','quarter'], how='inner'
).dropna(subset=['quarterly_return_pct','lagged_gst_yoy'])

signal['covid_flag'] = signal.apply(
    lambda r: 'COVID Quarter' if (r['year']==2020 and r['quarter'] in [2,3]) else 'Normal', axis=1
)
for company in signal['company'].unique():
    mask = signal['company'] == company
    sub  = signal[mask].sort_values(['year','quarter'])
    signal.loc[sub.index, 'rolling_8q_corr'] = (
        sub['lagged_gst_yoy'].rolling(8).corr(sub['quarterly_return_pct'])
    )
signal.to_csv('data/powerbi/pbi_signal_analysis.csv', index=False)
print(f"[4/6] pbi_signal_analysis.csv    → {len(signal)} rows")

# ── TABLE 5: Annual Revenue ──────────────────────────────────
annual_gst = (gst_q.groupby('cal_year')['total_gst_crore'].sum().pct_change()*100).reset_index()
annual_gst.columns = ['fy_year','gst_annual_yoy_pct']
pbi_ann = annual.merge(annual_gst, on='fy_year', how='left')
pbi_ann.to_csv('data/powerbi/pbi_annual_revenue.csv', index=False)
print(f"[5/6] pbi_annual_revenue.csv     → {len(pbi_ann)} rows")

# ── TABLE 6: Correlation by Lag ──────────────────────────────
lag_rows = []
for lag in range(0, 5):
    gst_q[f'lag_{lag}'] = gst_q['yoy_growth_pct'].shift(lag)
    df_lag = returns.merge(
        gst_q[['cal_year','quarter', f'lag_{lag}']],
        left_on=['year','quarter'], right_on=['cal_year','quarter']
    ).dropna(subset=['quarterly_return_pct', f'lag_{lag}'])
    r, p = stats.pearsonr(df_lag[f'lag_{lag}'], df_lag['quarterly_return_pct'])
    lag_rows.append({
        'lag_quarters': lag,
        'lag_label'   : f'Lag {lag}' + (' (same Q)' if lag==0 else f' ({lag}Q prior)'),
        'pearson_r'   : round(r, 4),
        'p_value'     : round(p, 4),
        'significant' : 'Yes' if p < 0.05 else ('Marginal' if p < 0.10 else 'No'),
        'n_obs'       : len(df_lag)
    })
pd.DataFrame(lag_rows).to_csv('data/powerbi/pbi_correlation_by_lag.csv', index=False)
print(f"[6/6] pbi_correlation_by_lag.csv → 5 rows")

print()
print("All Power BI tables ready in data/powerbi/")
print("Now open Power BI Desktop and load these 6 files.")

# =============================================================
# PHASE 5: STATISTICAL ANALYSIS
# GST-FMCG Indicator Analysis Project
# =============================================================
# BEFORE RUNNING:
#   pip install statsmodels matplotlib seaborn scipy
# =============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.stattools import grangercausalitytests
import os
import warnings

warnings.filterwarnings('ignore')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('outputs/charts', exist_ok=True)

# ── Global chart style ────────────────────────────────────────
plt.rcParams.update({
    'font.family'      : 'DejaVu Sans',
    'axes.spines.top'  : False,
    'axes.spines.right': False,
    'axes.grid'        : True,
    'grid.alpha'       : 0.3,
    'figure.dpi'       : 120,
})
COLORS = ['#2563EB','#16A34A','#DC2626','#D97706','#7C3AED','#0891B2','#BE185D']

print("Loading data from PostgreSQL...")
print("=" * 55)

# ─────────────────────────────────────────────────────────────
# DATA LOAD
# To pull from PostgreSQL instead of CSVs, replace the
# pd.read_csv() lines with:
#
#   from sqlalchemy import create_engine
#   engine = create_engine('postgresql+psycopg2://postgres:your_password@localhost:5432/gst_fmcg')
#   gst_m   = pd.read_sql('SELECT * FROM gst_monthly',            engine)
#   gst_q   = pd.read_sql('SELECT * FROM gst_quarterly',          engine)
#   returns = pd.read_sql('SELECT * FROM stock_quarterly_returns', engine)
#   annual  = pd.read_sql('SELECT * FROM fmcg_annual_revenue',     engine)
# ─────────────────────────────────────────────────────────────

gst_m   = pd.read_csv('data/cleaned/gst_monthly_clean.csv')
gst_q   = pd.read_csv('data/cleaned/gst_quarterly_clean.csv').sort_values(['cal_year','quarter']).reset_index(drop=True)
returns = pd.read_csv('data/cleaned/stock_quarterly_returns.csv')
annual  = pd.read_csv('data/cleaned/fmcg_annual_revenue.csv')

# Pre-compute lag columns
gst_q['lagged_gst_yoy'] = gst_q['yoy_growth_pct'].shift(1)
gst_q['lag2_gst_yoy']   = gst_q['yoy_growth_pct'].shift(2)
gst_q['period']         = gst_q['cal_year'].astype(str) + '-Q' + gst_q['quarter'].astype(str)
companies               = sorted(returns['company'].unique())

# Master join: returns + lagged GST
df_main = returns.merge(
    gst_q[['cal_year','quarter','yoy_growth_pct','lagged_gst_yoy','lag2_gst_yoy']],
    left_on=['year','quarter'], right_on=['cal_year','quarter']
).dropna(subset=['quarterly_return_pct','lagged_gst_yoy'])

print(f"Master dataframe: {len(df_main)} rows | "
      f"{df_main['year'].min()}-Q{df_main[df_main['year']==df_main['year'].min()]['quarter'].min()} "
      f"→ {df_main['year'].max()}-Q{df_main[df_main['year']==df_main['year'].max()]['quarter'].max()}")


# ─────────────────────────────────────────────────────────────
# ANALYSIS 1: Pearson Correlation — Lagged GST vs Returns
# ─────────────────────────────────────────────────────────────
print()
print("ANALYSIS 1 — Pearson Correlation (Lag 1 Quarter)")
print("-" * 55)
print(f"{'Company':<12} {'r':>7} {'p-value':>10} {'n':>5} {'Significant?'}")
print("-" * 55)

corr_results = []
for company in companies:
    sub = df_main[df_main['company'] == company]
    r, p = stats.pearsonr(sub['lagged_gst_yoy'], sub['quarterly_return_pct'])
    sig  = "Yes (p<0.05)" if p < 0.05 else ("Weak (p<0.10)" if p < 0.10 else "No")
    corr_results.append({'company': company, 'r': r, 'p_value': p})
    print(f"{company:<12} {r:>7.4f} {p:>10.4f} {len(sub):>5}  {sig}")

r_pool, p_pool = stats.pearsonr(df_main['lagged_gst_yoy'], df_main['quarterly_return_pct'])
print("-" * 55)
print(f"{'POOLED':<12} {r_pool:>7.4f} {p_pool:>10.4f} {len(df_main):>5}  "
      f"{'Yes (p<0.05)' if p_pool<0.05 else ('Weak (p<0.10)' if p_pool<0.10 else 'No')}")


# ─────────────────────────────────────────────────────────────
# ANALYSIS 2: Correlation Across Lag Lengths (0 to 4 quarters)
# ─────────────────────────────────────────────────────────────
print()
print("ANALYSIS 2 — Pooled Correlation at Different Lag Lengths")
print("-" * 55)
print(f"{'Lag':<8} {'r':>7} {'p-value':>10} {'n':>5}")
print("-" * 35)

lag_results = []
for lag in range(0, 5):
    gst_q[f'lag_test_{lag}'] = gst_q['yoy_growth_pct'].shift(lag)
    df_lag = returns.merge(
        gst_q[['cal_year','quarter', f'lag_test_{lag}']],
        left_on=['year','quarter'], right_on=['cal_year','quarter']
    ).dropna(subset=['quarterly_return_pct', f'lag_test_{lag}'])
    r, p = stats.pearsonr(df_lag[f'lag_test_{lag}'], df_lag['quarterly_return_pct'])
    lag_results.append({'lag': lag, 'r': r, 'p': p})
    sig  = " ← p<0.05" if p < 0.05 else (" ← p<0.10" if p < 0.10 else "")
    print(f"Lag {lag:<4} {r:>7.4f} {p:>10.4f} {len(df_lag):>5}{sig}")


# ─────────────────────────────────────────────────────────────
# ANALYSIS 3: OLS Regression (Lag 1 + Lag 2, pooled)
# ─────────────────────────────────────────────────────────────
print()
print("ANALYSIS 3 — OLS Regression: Lag1 + Lag2 GST → Stock Return")
print("-" * 55)

df_ols = df_main.dropna(subset=['lag2_gst_yoy'])
X      = sm.add_constant(df_ols[['lagged_gst_yoy','lag2_gst_yoy']])
y      = df_ols['quarterly_return_pct']
model  = sm.OLS(y, X).fit()
print(model.summary())


# ─────────────────────────────────────────────────────────────
# ANALYSIS 4: Granger Causality Test per Company
# ─────────────────────────────────────────────────────────────
print()
print("ANALYSIS 4 — Granger Causality: Does GST Granger-cause Returns?")
print("H0: Past GST growth does NOT help predict stock returns")
print("-" * 65)
print(f"{'Company':<12}  {'Lag1 p':>8}  {'Lag2 p':>8}  {'Lag3 p':>8}  {'Verdict'}")
print("-" * 65)

for company in companies:
    sub = returns[returns['company']==company].sort_values(['year','quarter']).reset_index(drop=True)
    sub = sub.merge(
        gst_q[['cal_year','quarter','yoy_growth_pct']],
        left_on=['year','quarter'], right_on=['cal_year','quarter']
    ).dropna(subset=['quarterly_return_pct','yoy_growth_pct'])

    data = sub[['quarterly_return_pct','yoy_growth_pct']].values
    try:
        res     = grangercausalitytests(data, maxlag=3, verbose=False)
        p1, p2, p3 = res[1][0]['ssr_ftest'][1], res[2][0]['ssr_ftest'][1], res[3][0]['ssr_ftest'][1]
        min_p   = min(p1, p2, p3)
        verdict = "Granger-causes ✓" if min_p < 0.05 else ("Weak signal" if min_p < 0.10 else "No evidence")
        print(f"{company:<12}  {p1:>8.4f}  {p2:>8.4f}  {p3:>8.4f}  {verdict}")
    except Exception as e:
        print(f"{company:<12}  ERROR: {e}")


# ─────────────────────────────────────────────────────────────
# ANALYSIS 5: Annual GST Growth vs Annual Revenue Growth
# ─────────────────────────────────────────────────────────────
print()
print("ANALYSIS 5 — Annual: GST Growth vs Revenue Growth")
print("-" * 55)

ann_gst = (gst_q.groupby('cal_year')['total_gst_crore'].sum().pct_change()*100).reset_index()
ann_gst.columns = ['fy_year','gst_annual_yoy']
ann_df  = annual.merge(ann_gst, on='fy_year').dropna(subset=['sales_yoy_growth_pct','gst_annual_yoy'])

r_ann, p_ann = stats.pearsonr(ann_df['gst_annual_yoy'], ann_df['sales_yoy_growth_pct'])
print(f"Pooled: r = {r_ann:.4f},  p = {p_ann:.4f},  n = {len(ann_df)}")


# ═════════════════════════════════════════════════════════════
# CHARTS
# ═════════════════════════════════════════════════════════════

# ── Chart 1: GST Monthly Trend ────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5))
gst_plot = gst_m[gst_m['date'] >= '2018-01-01'].copy()
gst_plot['date_dt'] = pd.to_datetime(gst_plot['date'])
ax.fill_between(gst_plot['date_dt'], gst_plot['total_collection_crore']/1000, alpha=0.15, color=COLORS[0])
ax.plot(gst_plot['date_dt'], gst_plot['total_collection_crore']/1000, color=COLORS[0], linewidth=2)
ax.axvspan(pd.Timestamp('2020-03-01'), pd.Timestamp('2020-09-30'), alpha=0.12, color='red', label='COVID period')
ax.set_title('India Monthly GST Collections (₹ Thousand Crore)', fontsize=14, fontweight='bold', pad=12)
ax.set_ylabel('₹ Thousand Crore')
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig('outputs/charts/chart1_gst_monthly_trend.png', bbox_inches='tight')
plt.close()

# ── Chart 2: GST Quarterly YoY Growth ───────────────────────
gst_q_plot  = gst_q.dropna(subset=['yoy_growth_pct'])
fig, ax = plt.subplots(figsize=(13, 5))
bar_colors  = [COLORS[2] if v < 0 else COLORS[0] for v in gst_q_plot['yoy_growth_pct']]
ax.bar(range(len(gst_q_plot)), gst_q_plot['yoy_growth_pct'], color=bar_colors, width=0.7)
ax.axhline(0, color='black', linewidth=0.8)
xtick_pos    = [i for i, r in enumerate(gst_q_plot.itertuples()) if r.quarter == 1]
xtick_labels = [str(r.cal_year) for r in gst_q_plot.itertuples() if r.quarter == 1]
ax.set_xticks(xtick_pos); ax.set_xticklabels(xtick_labels)
ax.set_title('GST Collections — Quarterly YoY Growth (%)', fontsize=14, fontweight='bold', pad=12)
ax.set_ylabel('YoY Growth (%)')
ax.legend(handles=[mpatches.Patch(color=COLORS[0], label='Positive'), mpatches.Patch(color=COLORS[2], label='Negative')], frameon=False)
plt.tight_layout()
plt.savefig('outputs/charts/chart2_gst_quarterly_yoy.png', bbox_inches='tight')
plt.close()

# ── Chart 3: Scatter — Lagged GST vs Returns (all companies) ─
fig, axes = plt.subplots(2, 4, figsize=(15, 8))
axes = axes.flatten()
for i, company in enumerate(companies):
    sub = df_main[df_main['company'] == company]
    ax  = axes[i]
    ax.scatter(sub['lagged_gst_yoy'], sub['quarterly_return_pct'], alpha=0.65, color=COLORS[i], s=50, edgecolors='white', linewidth=0.4)
    m, b, r, p, _ = stats.linregress(sub['lagged_gst_yoy'], sub['quarterly_return_pct'])
    x_line = np.linspace(sub['lagged_gst_yoy'].min(), sub['lagged_gst_yoy'].max(), 100)
    ax.plot(x_line, m*x_line+b, color='black', linewidth=1.2, linestyle='--', alpha=0.7)
    ax.axhline(0, color='grey', linewidth=0.5); ax.axvline(0, color='grey', linewidth=0.5)
    ax.set_title(f'{company}  (r={r:.2f}, p={p:.2f})', fontsize=10)
    ax.set_xlabel('Lagged GST YoY %', fontsize=8); ax.set_ylabel('Quarterly Return %', fontsize=8)
ax = axes[7]
for i, company in enumerate(companies):
    sub = df_main[df_main['company'] == company]
    ax.scatter(sub['lagged_gst_yoy'], sub['quarterly_return_pct'], alpha=0.45, color=COLORS[i], s=30, label=company)
m, b, r, p, _ = stats.linregress(df_main['lagged_gst_yoy'], df_main['quarterly_return_pct'])
x_line = np.linspace(df_main['lagged_gst_yoy'].min(), df_main['lagged_gst_yoy'].max(), 100)
ax.plot(x_line, m*x_line+b, color='black', linewidth=1.5, linestyle='--')
ax.set_title(f'Pooled  (r={r:.2f}, p={p:.2f})', fontsize=10)
ax.set_xlabel('Lagged GST YoY %', fontsize=8); ax.set_ylabel('Quarterly Return %', fontsize=8)
fig.suptitle('Lagged GST YoY Growth vs Next-Quarter Stock Returns', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('outputs/charts/chart3_scatter_lagged_gst_vs_returns.png', bbox_inches='tight')
plt.close()

# ── Chart 4: Correlation by Lag Length ────────────────────────
lag_df = pd.DataFrame(lag_results)
fig, ax = plt.subplots(figsize=(8, 5))
bar_colors = [COLORS[2] if v < 0 else COLORS[0] for v in lag_df['r']]
ax.bar(lag_df['lag'], lag_df['r'], color=bar_colors, width=0.5, edgecolor='white')
for _, row in lag_df.iterrows():
    if row['p'] < 0.05:
        ax.text(row['lag'], row['r']+(0.01 if row['r']>0 else -0.025), '**', ha='center', fontsize=13)
    elif row['p'] < 0.10:
        ax.text(row['lag'], row['r']+(0.01 if row['r']>0 else -0.025), '*', ha='center', fontsize=13)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_xticks(lag_df['lag']); ax.set_xticklabels([f'Lag {l}\n({l}Q prior)' for l in lag_df['lag']])
ax.set_ylabel('Pearson r')
ax.set_title('Pooled Correlation: GST YoY vs Stock Returns\n(** p<0.05,  * p<0.10)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('outputs/charts/chart4_correlation_by_lag.png', bbox_inches='tight')
plt.close()

# ── Chart 5: Rolling 8-Quarter Correlation per Company ────────
fig, ax = plt.subplots(figsize=(13, 6))
for i, company in enumerate(companies):
    sub = returns[returns['company']==company].sort_values(['year','quarter']).reset_index(drop=True)
    sub = sub.merge(gst_q[['cal_year','quarter','lagged_gst_yoy']], left_on=['year','quarter'], right_on=['cal_year','quarter']).dropna(subset=['quarterly_return_pct','lagged_gst_yoy'])
    sub['rolling_corr'] = sub['lagged_gst_yoy'].rolling(8).corr(sub['quarterly_return_pct'])
    valid = sub.dropna(subset=['rolling_corr'])
    ax.plot(range(len(valid)), valid['rolling_corr'], color=COLORS[i], linewidth=1.6, label=company, marker='o', markersize=3)
ax.axhline(0, color='black', linewidth=1, linestyle='--', alpha=0.5)
ax.axhline(0.3, color='grey', linewidth=0.7, linestyle=':', alpha=0.6)
ax.axhline(-0.3, color='grey', linewidth=0.7, linestyle=':', alpha=0.6)
ax.set_title('Rolling 8-Quarter Correlation: Lagged GST YoY → Stock Returns', fontsize=13, fontweight='bold')
ax.set_ylabel('Pearson r (rolling)'); ax.set_xlabel('Quarter index')
ax.legend(ncol=4, frameon=False, fontsize=9); ax.set_ylim(-1, 1)
plt.tight_layout()
plt.savefig('outputs/charts/chart5_rolling_correlation.png', bbox_inches='tight')
plt.close()

# ── Chart 6: Annual GST vs Revenue Growth per Company ─────────
fig, axes = plt.subplots(2, 4, figsize=(15, 8))
axes = axes.flatten()
for i, company in enumerate(companies):
    sub = ann_df[ann_df['company'] == company]
    ax  = axes[i]
    ax.scatter(sub['gst_annual_yoy'], sub['sales_yoy_growth_pct'], color=COLORS[i], s=80, edgecolors='white', linewidth=0.5, zorder=3)
    for _, row in sub.iterrows():
        ax.annotate(str(int(row['fy_year'])), (row['gst_annual_yoy'], row['sales_yoy_growth_pct']), textcoords='offset points', xytext=(4,4), fontsize=7, color='gray')
    if len(sub) >= 3:
        m, b, r, p, _ = stats.linregress(sub['gst_annual_yoy'], sub['sales_yoy_growth_pct'])
        x_line = np.linspace(sub['gst_annual_yoy'].min(), sub['gst_annual_yoy'].max(), 100)
        ax.plot(x_line, m*x_line+b, color='black', linewidth=1, linestyle='--', alpha=0.6)
    ax.set_title(f'{company}', fontsize=10, fontweight='bold')
    ax.set_xlabel('Annual GST YoY %', fontsize=8); ax.set_ylabel('Revenue YoY %', fontsize=8)
axes[7].axis('off')
fig.suptitle('Annual GST Growth vs FMCG Revenue Growth (FY2018–FY2025)', fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('outputs/charts/chart6_annual_gst_vs_revenue.png', bbox_inches='tight')
plt.close()

print()
print("=" * 55)
print("Phase 5 complete.")
print("Charts saved to outputs/charts/")
print()
print("KEY FINDINGS SUMMARY")
print("-" * 55)
print(f"  Lag 1 pooled r   = {r_pool:.4f}  (p = {p_pool:.4f})")
print(f"  OLS R-squared    = {model.rsquared:.4f}  (model p = {model.f_pvalue:.6f})")
print(f"  Lag 1 coeff      = {model.params['lagged_gst_yoy']:.4f}  (p = {model.pvalues['lagged_gst_yoy']:.4f})")
print(f"  Lag 2 coeff      = {model.params['lag2_gst_yoy']:.4f}  (p = {model.pvalues['lag2_gst_yoy']:.4f})")

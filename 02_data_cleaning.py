# =============================================================
# PHASE 3: DATA CLEANING
# GST-FMCG Indicator Analysis Project
# ===========================================================
import pandas as pd
import numpy as np
import re
import os


os.makedirs('data/cleaned', exist_ok=True)

print("Starting Phase 3: Data Cleaning...")
print("=" * 55)





# ─────────────────────────────────────────────────────────────
# SECTION 1: GST MONTHLY DATA
# What we do: Loop through all 9 GST CSVs, parse the messy
# headers, extract the Grand Total row for each month, and
# combine into one clean table.
# ─────────────────────────────────────────────────────────────

def parse_gst_file(filepath):
    raw = pd.read_csv(filepath, header=None, encoding='utf-8-sig')

    # Row 4 has month names (Jul-17, Aug-17 etc.) starting at col 7
    month_row = raw.iloc[4]
    months = []
    for col_idx, val in enumerate(month_row):
        if re.match(r'[A-Za-z]{3}-\d{2}', str(val).strip()):
            months.append((str(val).strip(), col_idx))

    # Find Grand Total row
    # Older files (up to 2023-24): col0 = 'Grand Total'
    # Newer files (2024-25, 2025-26): col0 = 'Domestic GST Collection...'
    grand_total_row = None
    for i, row in raw.iterrows():
        cell = str(row[0]).strip()
        if cell == 'Grand Total' or cell.startswith('Domestic GST Collect'):
            grand_total_row = row
            break

    if grand_total_row is None:
        return pd.DataFrame()

    # TOTAL column for each month = month_col + 4
    # (sub-columns are: CGST, SGST, IGST, CESS, TOTAL)
    records = []
    for month_str, month_col in months:
        total_col = month_col + 4
        raw_val   = str(grand_total_row[total_col]).strip().replace(',', '')
        try:
            total = float(raw_val)
        except:
            total = np.nan

        dt = pd.to_datetime(month_str, format='%b-%y')
        records.append({
            'month_year'             : month_str,
            'date'                   : dt.strftime('%Y-%m-01'),
            'year'                   : dt.year,
            'month'                  : dt.month,
            'total_collection_crore' : total
        })
    return pd.DataFrame(records)


all_gst = []
for f in sorted(os.listdir('data/raw/gst_collections')):
    if f.endswith('.csv'):
        df = parse_gst_file(f'data/raw/gst_collections/{f}')
        all_gst.append(df)

gst_monthly = (pd.concat(all_gst, ignore_index=True)
                 .sort_values('date')
                 .reset_index(drop=True))

# Keep only up to Dec 2024 (aligns with stock price data)
gst_monthly = gst_monthly[gst_monthly['date'] <= '2024-12-01']

# Add YoY growth % (compare same month, prior year)
gst_monthly['yoy_growth_pct'] = (
    gst_monthly['total_collection_crore']
    .pct_change(periods=12) * 100
).round(2)

gst_monthly.to_csv('data/cleaned/gst_monthly_clean.csv', index=False)
print(f"[1/6] gst_monthly_clean.csv      → {len(gst_monthly)} rows "
      f"| {gst_monthly['date'].min()} to {gst_monthly['date'].max()}")


# ─────────────────────────────────────────────────────────────
# SECTION 2: GST QUARTERLY (aggregated from monthly)
# ─────────────────────────────────────────────────────────────

gst_monthly['quarter']  = pd.to_datetime(gst_monthly['date']).dt.quarter
gst_monthly['cal_year'] = pd.to_datetime(gst_monthly['date']).dt.year

gst_quarterly = (gst_monthly
    .groupby(['cal_year', 'quarter'])
    .agg(
        total_gst_crore      =('total_collection_crore', 'sum'),
        months_in_quarter    =('total_collection_crore', 'count')
    )
    .reset_index())

# Only keep complete quarters (all 3 months present)
gst_quarterly = gst_quarterly[gst_quarterly['months_in_quarter'] == 3].copy()

# QoQ growth: vs previous quarter
gst_quarterly['qoq_growth_pct'] = (
    gst_quarterly['total_gst_crore'].pct_change(periods=1) * 100
).round(2)

# YoY growth: same quarter, prior year
gst_quarterly['yoy_growth_pct'] = (
    gst_quarterly['total_gst_crore'].pct_change(periods=4) * 100
).round(2)

gst_quarterly.to_csv('data/cleaned/gst_quarterly_clean.csv', index=False)
print(f"[2/6] gst_quarterly_clean.csv    → {len(gst_quarterly)} rows "
      f"| 30 complete quarters (2017-Q3 to 2024-Q4)")


# ─────────────────────────────────────────────────────────────
# SECTION 3: STOCK DAILY PRICES (clean format)
# ─────────────────────────────────────────────────────────────

company_map = {
    'stock_pricesHUL_prices.csv'      : 'HUL',
    'stock_pricesITC_prices.csv'      : 'ITC',
    'stock_pricesBritannia_prices.csv': 'Britannia',
    'stock_pricesDabur_prices.csv'    : 'Dabur',
    'stock_pricesGodrej_prices.csv'   : 'Godrej',
    'stock_pricesMarico_prices.csv'   : 'Marico',
    'stock_pricesNestle_prices.csv'   : 'Nestle'
}

all_daily = []
all_quarterly_returns = []

for filename, company in company_map.items():
    # The raw file has 2 metadata rows before actual data
    df = pd.read_csv(f'data/raw/stock_prices/{filename}')
    df = df.iloc[2:].copy()
    df = df.rename(columns={'Price': 'Date'})
    df['Date']    = pd.to_datetime(df['Date'])
    df['Close']   = pd.to_numeric(df['Close'], errors='coerce')
    df['company'] = company
    df = df[['company', 'Date', 'Close']].dropna()
    all_daily.append(df)

    # ── Quarterly returns ────────────────────
    df['year']    = df['Date'].dt.year
    df['quarter'] = df['Date'].dt.quarter

    # Last close price of each quarter
    qtr = (df.groupby(['year', 'quarter'])
             .agg(end_price    =('Close', 'last'),
                  start_price  =('Close', 'first'),
                  trading_days =('Close', 'count'))
             .reset_index()
             .sort_values(['year', 'quarter'])
             .reset_index(drop=True))

    # Return = (this quarter end price / last quarter end price - 1) * 100
    qtr['quarterly_return_pct'] = (
        (qtr['end_price'] / qtr['end_price'].shift(1) - 1) * 100
    ).round(4)

    qtr['company'] = company
    all_quarterly_returns.append(qtr)

daily_df = pd.concat(all_daily, ignore_index=True)
returns_df = pd.concat(all_quarterly_returns, ignore_index=True)

daily_df.to_csv('data/cleaned/stock_daily_prices.csv', index=False)
returns_df.to_csv('data/cleaned/stock_quarterly_returns.csv', index=False)

print(f"[3/6] stock_daily_prices.csv     → {len(daily_df)} rows")
print(f"[4/6] stock_quarterly_returns.csv→ {len(returns_df)} rows "
      f"| 30 quarters × 7 companies")


# ─────────────────────────────────────────────────────────────
# SECTION 4: FMCG ANNUAL REVENUE (from Screener)
# ─────────────────────────────────────────────────────────────

def get_row_by_label(df, section_start, label):
    for j in range(section_start, section_start + 20):
        if str(df.iloc[j][0]).strip() == label:
            return df.iloc[j]
    return None

screener_map = {
    'Hind. Unilever.xlsx' : 'HUL',
    'ITC.xlsx'            : 'ITC',
    'Britannia Inds.xlsx' : 'Britannia',
    'Dabur India.xlsx'    : 'Dabur',
    'Godrej Consumer.xlsx': 'Godrej',
    'Marico.xlsx'         : 'Marico',
    'Nestle India.xlsx'   : 'Nestle'
}

annual_records    = []
quarterly_records = []

for filename, company in screener_map.items():
    df = pd.read_excel(f'data/raw/screener_alldata/{filename}',
                       sheet_name='Data Sheet', header=None)

    # ── Annual P&L ───────────────────────────
    for idx, row in df.iterrows():
        if str(row[0]).strip() == 'PROFIT & LOSS':
            date_row   = df.iloc[idx + 1]
            sales_row  = get_row_by_label(df, idx, 'Sales')
            profit_row = get_row_by_label(df, idx, 'Net profit')
            pbt_row    = get_row_by_label(df, idx, 'Profit before tax')

            for col in range(1, len(date_row)):
                dv = date_row[col]
                if pd.isna(dv) or 'Report' in str(dv):
                    continue
                try:
                    dt = pd.to_datetime(dv)
                    annual_records.append({
                        'company'      : company,
                        'fy_end_date'  : dt.strftime('%Y-%m-%d'),
                        'fy_year'      : dt.year,
                        'sales_cr'     : pd.to_numeric(sales_row[col],  errors='coerce'),
                        'net_profit_cr': pd.to_numeric(profit_row[col], errors='coerce'),
                        'pbt_cr'       : pd.to_numeric(pbt_row[col],    errors='coerce'),
                    })
                except:
                    continue
            break

    # ── Quarterly ────────────────────────────
    for idx, row in df.iterrows():
        if str(row[0]).strip() == 'Quarters':
            date_row   = df.iloc[idx + 1]
            sales_row  = df.iloc[idx + 2]
            profit_row = df.iloc[idx + 8]
            op_row     = df.iloc[idx + 9]

            for col in range(1, len(date_row)):
                dv = date_row[col]
                if pd.isna(dv) or 'Report' in str(dv):
                    continue
                try:
                    dt = pd.to_datetime(dv)
                    quarterly_records.append({
                        'company'      : company,
                        'quarter_end'  : dt.strftime('%Y-%m-%d'),
                        'year'         : dt.year,
                        'quarter'      : dt.quarter,
                        'sales_cr'     : pd.to_numeric(sales_row[col],  errors='coerce'),
                        'net_profit_cr': pd.to_numeric(profit_row[col], errors='coerce'),
                        'op_profit_cr' : pd.to_numeric(op_row[col],     errors='coerce'),
                    })
                except:
                    continue
            break

annual_df = pd.DataFrame(annual_records).sort_values(['company','fy_year']).reset_index(drop=True)
annual_df['sales_yoy_growth_pct'] = (
    annual_df.groupby('company')['sales_cr'].pct_change() * 100
).round(2)

qtr_df = pd.DataFrame(quarterly_records).sort_values(['company','quarter_end']).reset_index(drop=True)
qtr_df['sales_qoq_growth_pct'] = (
    qtr_df.groupby('company')['sales_cr'].pct_change() * 100
).round(2)

annual_df.to_csv('data/cleaned/fmcg_annual_revenue.csv', index=False)
qtr_df.to_csv('data/cleaned/fmcg_quarterly_revenue.csv', index=False)

print(f"[5/6] fmcg_annual_revenue.csv    → {len(annual_df)} rows "
      f"| FY2016–FY2026, 7 companies")
print(f"[6/6] fmcg_quarterly_revenue.csv → {len(qtr_df)} rows "
      f"| Q3 2023–Q4 2025, 7 companies")

print()
print("=" * 55)
print("Phase 3 complete. Files saved to data/cleaned/")
print()
print("Files created:")
for f in sorted(os.listdir('data/cleaned')):
    df = pd.read_csv(f'data/cleaned/{f}')
    print(f"  {f:<40} {len(df)} rows × {len(df.columns)} cols")

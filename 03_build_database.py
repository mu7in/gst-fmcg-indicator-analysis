# =============================================================
# PHASE 4: BUILD PostgreSQL DATABASE
# GST-FMCG Indicator Analysis Project
# =============================================================
# BEFORE RUNNING:
#   1. Install PostgreSQL and create a database called gst_fmcg
#   2. pip install psycopg2-binary sqlalchemy
#   3. Update DB_PASS below with your PostgreSQL password
# =============================================================

import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ── CONNECTION SETTINGS ── Update DB_PASS to your password ───
DB_USER = 'postgres'
DB_PASS = 'admin'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'gst_fmcg'
# ─────────────────────────────────────────────────────────────

conn_str = f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine   = create_engine(conn_str)

print("Connecting to PostgreSQL...")
print("=" * 55)

# ─────────────────────────────────────────────────────────────
# STEP 1: DROP old tables and CREATE fresh ones
# ─────────────────────────────────────────────────────────────

ddl = """

DROP TABLE IF EXISTS fmcg_quarterly_revenue;
DROP TABLE IF EXISTS fmcg_annual_revenue;
DROP TABLE IF EXISTS stock_quarterly_returns;
DROP TABLE IF EXISTS stock_daily_prices;
DROP TABLE IF EXISTS gst_quarterly;
DROP TABLE IF EXISTS gst_monthly;

CREATE TABLE gst_monthly (
    id                     SERIAL PRIMARY KEY,
    month_year             VARCHAR(10)    NOT NULL,
    collection_date        DATE           NOT NULL,
    year                   SMALLINT       NOT NULL,
    month                  SMALLINT       NOT NULL,
    total_collection_crore NUMERIC(12,2),
    yoy_growth_pct         NUMERIC(8,2)
);

CREATE TABLE gst_quarterly (
    id                 SERIAL PRIMARY KEY,
    cal_year           SMALLINT       NOT NULL,
    quarter            SMALLINT       NOT NULL,
    total_gst_crore    NUMERIC(12,2),
    months_in_quarter  SMALLINT,
    qoq_growth_pct     NUMERIC(8,2),
    yoy_growth_pct     NUMERIC(8,2)
);

CREATE TABLE stock_daily_prices (
    id        SERIAL PRIMARY KEY,
    company   VARCHAR(20)   NOT NULL,
    price_date DATE         NOT NULL,
    close     NUMERIC(10,4) NOT NULL,
    year      SMALLINT      NOT NULL,
    quarter   SMALLINT      NOT NULL
);

CREATE TABLE stock_quarterly_returns (
    id                   SERIAL PRIMARY KEY,
    company              VARCHAR(20)   NOT NULL,
    year                 SMALLINT      NOT NULL,
    quarter              SMALLINT      NOT NULL,
    start_price          NUMERIC(10,4),
    end_price            NUMERIC(10,4),
    trading_days         SMALLINT,
    quarterly_return_pct NUMERIC(8,4)
);

CREATE TABLE fmcg_annual_revenue (
    id                   SERIAL PRIMARY KEY,
    company              VARCHAR(30)   NOT NULL,
    fy_end_date          DATE          NOT NULL,
    fy_year              SMALLINT      NOT NULL,
    sales_cr             NUMERIC(12,2),
    net_profit_cr        NUMERIC(12,2),
    pbt_cr               NUMERIC(12,2),
    sales_yoy_growth_pct NUMERIC(8,2)
);

CREATE TABLE fmcg_quarterly_revenue (
    id                   SERIAL PRIMARY KEY,
    company              VARCHAR(30)   NOT NULL,
    quarter_end          DATE          NOT NULL,
    year                 SMALLINT      NOT NULL,
    quarter              SMALLINT      NOT NULL,
    sales_cr             NUMERIC(12,2),
    net_profit_cr        NUMERIC(12,2),
    op_profit_cr         NUMERIC(12,2),
    sales_qoq_growth_pct NUMERIC(8,2)
);

"""

with engine.connect() as con:
    for statement in ddl.strip().split(';'):
        stmt = statement.strip()
        if stmt:
            con.execute(text(stmt))
    con.commit()

print("[1/2] All 6 tables created in PostgreSQL")

# ─────────────────────────────────────────────────────────────
# STEP 2: LOAD cleaned CSVs into PostgreSQL tables
# Note: Column name mapping where CSV names differ from DB names
# ─────────────────────────────────────────────────────────────

def load_table(csv_path, table_name, rename_cols=None, drop_cols=None):
    df = pd.read_csv(csv_path)
    df.columns = [c.lower() for c in df.columns]

    if drop_cols:
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    if rename_cols:
        df = df.rename(columns=rename_cols)

    df.to_sql(table_name, engine, if_exists='append', index=False)

    with engine.connect() as con:
        count = con.execute(text(f'SELECT COUNT(*) FROM {table_name}')).fetchone()[0]
    print(f"    {table_name:<30} → {count} rows")


# gst_monthly: rename 'date' → 'collection_date' (date is a reserved word)
load_table(
    'data/cleaned/gst_monthly_clean.csv',
    'gst_monthly',
    rename_cols={'date': 'collection_date'}
)

# gst_quarterly: no renames needed
load_table(
    'data/cleaned/gst_quarterly_clean.csv',
    'gst_quarterly'
)

# stock_daily_prices: rename 'date' → 'price_date', 'close' already lowercase
load_table(
    'data/cleaned/stock_daily_prices.csv',
    'stock_daily_prices',
    rename_cols={'date': 'price_date'}
)

# stock_quarterly_returns: no renames needed
load_table(
    'data/cleaned/stock_quarterly_returns.csv',
    'stock_quarterly_returns'
)

# fmcg_annual_revenue: no renames needed
load_table(
    'data/cleaned/fmcg_annual_revenue.csv',
    'fmcg_annual_revenue'
)

# fmcg_quarterly_revenue: no renames needed
load_table(
    'data/cleaned/fmcg_quarterly_revenue.csv',
    'fmcg_quarterly_revenue'
)

print(f"[2/2] All data loaded into PostgreSQL")
print()
print(f"Open DBeaver → connect to localhost:5432/gst_fmcg → you're ready.")

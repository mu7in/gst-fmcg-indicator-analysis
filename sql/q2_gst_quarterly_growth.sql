-- Q2: GST Quarterly Growth — all 30 quarters
-- Concepts: SELECT, ROUND, ORDER BY

SELECT
    cal_year                                   AS year,
    quarter,
    ROUND(total_gst_crore / 1000.0, 1)        AS gst_thousand_cr,
    ROUND(yoy_growth_pct, 2)                  AS yoy_pct,
    ROUND(qoq_growth_pct, 2)                  AS qoq_pct
FROM gst_quarterly
ORDER BY cal_year, quarter;

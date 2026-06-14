-- Q9: Annual GST Growth vs FMCG Revenue Growth (Secondary Analysis)
-- Joins annual macro and annual company revenue
-- Concepts: Multi-level CTE, SUM, LAG, JOIN across aggregated tables

WITH annual_gst AS (
    SELECT
        cal_year,
        SUM(total_gst_crore) AS annual_gst_crore,
        ROUND(
            (SUM(total_gst_crore) - LAG(SUM(total_gst_crore)) OVER (ORDER BY cal_year))
            * 100.0
            / NULLIF(LAG(SUM(total_gst_crore)) OVER (ORDER BY cal_year), 0)
        , 2) AS gst_annual_yoy_pct
    FROM gst_quarterly
    GROUP BY cal_year
)
SELECT
    f.fy_year,
    f.company,
    ROUND(f.sales_cr, 0)                  AS sales_cr,
    ROUND(f.sales_yoy_growth_pct, 2)      AS revenue_yoy_pct,
    ROUND(g.gst_annual_yoy_pct, 2)        AS gst_yoy_pct
FROM fmcg_annual_revenue f
JOIN annual_gst g
    ON f.fy_year = g.cal_year
WHERE f.sales_yoy_growth_pct IS NOT NULL
ORDER BY f.company, f.fy_year;

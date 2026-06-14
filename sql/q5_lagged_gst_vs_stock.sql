-- Q5: Lagged GST Growth → Next Quarter Stock Return
-- Core project query: does prior quarter GST predict stock return?
-- Concepts: CTE (WITH), LAG() window function, JOIN

WITH gst_lagged AS (
    SELECT
        cal_year,
        quarter,
        yoy_growth_pct,
        LAG(yoy_growth_pct, 1) OVER (
            ORDER BY cal_year, quarter
        ) AS prev_quarter_gst_yoy
    FROM gst_quarterly
)
SELECT
    g.cal_year                              AS year,
    g.quarter,
    ROUND(g.prev_quarter_gst_yoy, 2)       AS lagged_gst_yoy_pct,
    s.company,
    ROUND(s.quarterly_return_pct, 2)       AS stock_return_pct
FROM gst_lagged g
JOIN stock_quarterly_returns s
    ON  g.cal_year = s.year
    AND g.quarter  = s.quarter
WHERE g.prev_quarter_gst_yoy  IS NOT NULL
  AND s.quarterly_return_pct  IS NOT NULL
ORDER BY year, g.quarter, s.company;

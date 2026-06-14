-- Q8: Rolling 4-Quarter Avg GST YoY vs Stock Returns
-- Smooths out single-quarter noise for a cleaner signal
-- Concepts: Rolling window AVG with ROWS BETWEEN, CTE, JOIN

WITH rolling_gst AS (
    SELECT
        cal_year,
        quarter,
        yoy_growth_pct,
        AVG(yoy_growth_pct) OVER (
            ORDER BY cal_year, quarter
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS rolling_4q_avg_gst_yoy
    FROM gst_quarterly
    WHERE yoy_growth_pct IS NOT NULL
)
SELECT
    r.cal_year                               AS year,
    r.quarter,
    ROUND(r.yoy_growth_pct, 2)              AS gst_yoy_pct,
    ROUND(r.rolling_4q_avg_gst_yoy, 2)     AS rolling_4q_avg,
    s.company,
    ROUND(s.quarterly_return_pct, 2)        AS stock_return_pct
FROM rolling_gst r
JOIN stock_quarterly_returns s
    ON  r.cal_year = s.year
    AND r.quarter  = s.quarter
WHERE s.quarterly_return_pct IS NOT NULL
ORDER BY year, r.quarter, s.company;

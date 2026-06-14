-- Q7: Stock Returns During Negative GST Quarters (Stress Periods)
-- Concepts: JOIN, WHERE with filter on joined column

SELECT
    g.cal_year                             AS year,
    g.quarter,
    ROUND(g.yoy_growth_pct, 2)            AS gst_yoy_pct,
    s.company,
    ROUND(s.quarterly_return_pct, 2)      AS stock_return_pct
FROM gst_quarterly g
JOIN stock_quarterly_returns s
    ON  g.cal_year = s.year
    AND g.quarter  = s.quarter
WHERE g.yoy_growth_pct < 0
  AND s.quarterly_return_pct IS NOT NULL
ORDER BY g.cal_year, g.quarter, s.company;

-- Q4: GST Growth vs Stock Return — Same Quarter, All Companies
-- Concepts: JOIN on two columns, WHERE, ORDER BY

SELECT
    g.cal_year                            AS year,
    g.quarter,
    ROUND(g.total_gst_crore / 1000, 1)   AS gst_k_crore,
    ROUND(g.yoy_growth_pct, 2)           AS gst_yoy_pct,
    s.company,
    ROUND(s.quarterly_return_pct, 2)     AS stock_return_pct
FROM gst_quarterly g
JOIN stock_quarterly_returns s
    ON  g.cal_year = s.year
    AND g.quarter  = s.quarter
WHERE s.quarterly_return_pct IS NOT NULL
ORDER BY year, g.quarter, s.company;

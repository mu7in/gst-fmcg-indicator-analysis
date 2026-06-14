-- Q1: GST Monthly Trend
-- Concepts: SELECT, ROUND, ORDER BY

SELECT
    month_year,
    collection_date,
    ROUND(total_collection_crore, 0)  AS gst_crore,
    ROUND(yoy_growth_pct, 2)          AS yoy_pct
FROM gst_monthly
ORDER BY collection_date ASC;

-- Q6: Summary Statistics per Company (Full Period)
-- Concepts: GROUP BY, AVG, MAX, MIN, COUNT, ORDER BY

SELECT
    company,
    COUNT(*)                                AS quarters,
    ROUND(AVG(quarterly_return_pct), 2)    AS avg_return_pct,
    ROUND(MAX(quarterly_return_pct), 2)    AS best_quarter_pct,
    ROUND(MIN(quarterly_return_pct), 2)    AS worst_quarter_pct,
    ROUND(STDDEV(quarterly_return_pct), 2) AS volatility_pct
FROM stock_quarterly_returns
WHERE quarterly_return_pct IS NOT NULL
GROUP BY company
ORDER BY avg_return_pct DESC;

-- Q3: Best Single Quarter per Company
-- Concepts: RANK() window function, PARTITION BY, subquery

SELECT *
FROM (
    SELECT
        company,
        year,
        quarter,
        ROUND(quarterly_return_pct, 2)   AS return_pct,
        RANK() OVER (
            PARTITION BY company
            ORDER BY quarterly_return_pct DESC
        ) AS rank_best
    FROM stock_quarterly_returns
    WHERE quarterly_return_pct IS NOT NULL
) ranked
WHERE rank_best = 1
ORDER BY return_pct DESC;

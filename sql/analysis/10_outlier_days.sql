-- Q5. Outlier days at the corridor chokepoints: daily transits more than 50% away from the
-- centred 15-day median. AIS reception gaps and the 48-hour de-duplication rule both create
-- one-day spikes and dips that wash out in weekly or monthly averages.
WITH daily AS (
    SELECT "date", chokepoint_id, sum(transits) AS transits
    FROM gold.fact_chokepoint_transits
    JOIN gold.dim_chokepoint USING (chokepoint_id)
    WHERE route_role IS NOT NULL
    GROUP BY ALL
),
smoothed AS (
    SELECT "date", chokepoint_id, transits,
           median(transits) OVER (
               PARTITION BY chokepoint_id ORDER BY "date"
               ROWS BETWEEN 7 PRECEDING AND 7 FOLLOWING
           ) AS median_15d
    FROM daily
)
SELECT
    c.chokepoint_name,
    s."date",
    s.transits,
    s.median_15d,
    s.transits / s.median_15d - 1 AS deviation
FROM smoothed AS s
JOIN gold.dim_chokepoint AS c USING (chokepoint_id)
WHERE s.median_15d > 0 AND abs(s.transits / s.median_15d - 1) > 0.5
ORDER BY abs(s.transits / s.median_15d - 1) DESC;

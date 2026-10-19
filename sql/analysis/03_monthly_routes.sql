-- Q1-Q2 time series: average daily transits and estimated volume per month for the five
-- corridor chokepoints. Months with fewer than 20 days of data are flagged as partial.
SELECT
    c.chokepoint_id,
    c.chokepoint_name,
    d.month_start,
    count(DISTINCT f."date")                              AS days,
    sum(f.transits) / count(DISTINCT f."date")            AS transits_per_day,
    sum(f.volume_t) / count(DISTINCT f."date")            AS volume_t_per_day,
    count(DISTINCT f."date") < 20                         AS is_partial
FROM gold.fact_chokepoint_transits AS f
JOIN gold.dim_date AS d USING ("date")
JOIN gold.dim_chokepoint AS c USING (chokepoint_id)
WHERE c.route_role IS NOT NULL
GROUP BY ALL
ORDER BY c.chokepoint_id, d.month_start;

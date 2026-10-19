-- Q2. Where did the traffic go? Suez, Bab el-Mandeb, the Cape of Good Hope, Gibraltar and
-- Malacca (the upstream control), per period, against the pre-attack baseline.
WITH daily AS (
    SELECT "date", chokepoint_id, sum(transits) AS transits, sum(volume_t) AS volume_t
    FROM gold.fact_chokepoint_transits
    JOIN gold.dim_chokepoint USING (chokepoint_id)
    WHERE route_role IS NOT NULL
    GROUP BY ALL
),
by_period AS (
    SELECT d.chokepoint_id, p.period, p.period_label, p.sort_order,
           avg(d.transits) AS transits_per_day,
           avg(d.volume_t) AS volume_t_per_day
    FROM daily AS d
    JOIN gold.dim_period AS p ON d."date" BETWEEN p.start_date AND p.end_date
    GROUP BY ALL
)
SELECT
    c.chokepoint_name,
    c.route_role,
    b.period,
    b.period_label,
    b.transits_per_day,
    b.volume_t_per_day,
    b.transits_per_day - base.transits_per_day          AS transits_change_per_day,
    b.transits_per_day / base.transits_per_day - 1      AS transits_vs_baseline,
    b.volume_t_per_day / base.volume_t_per_day - 1      AS volume_vs_baseline
FROM by_period AS b
JOIN by_period AS base ON base.chokepoint_id = b.chokepoint_id AND base.period = 'baseline'
JOIN gold.dim_chokepoint AS c ON c.chokepoint_id = b.chokepoint_id
ORDER BY CASE c.chokepoint_id WHEN 'chokepoint1' THEN 1 WHEN 'chokepoint4' THEN 2
         WHEN 'chokepoint7' THEN 3 WHEN 'chokepoint8' THEN 4 ELSE 5 END, b.sort_order;

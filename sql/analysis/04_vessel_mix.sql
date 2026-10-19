-- Q3. Which vessel types left Suez the most? Daily transits and volume by type, baseline vs
-- 2024 vs the latest window, and each type's share of the transits lost in 2024.
WITH by_type AS (
    SELECT f.vessel_type, p.period,
           sum(f.transits) / count(DISTINCT f."date") AS transits,
           sum(f.volume_t) / count(DISTINCT f."date") AS volume
    FROM gold.fact_chokepoint_transits AS f
    JOIN gold.dim_period AS p ON f."date" BETWEEN p.start_date AND p.end_date
    WHERE f.chokepoint_id = 'chokepoint1' AND p.period IN ('baseline', 'crisis_2024', 'latest')
    GROUP BY ALL
),
wide AS (
    SELECT vessel_type,
           max(transits) FILTER (WHERE period = 'baseline')    AS baseline_transits,
           max(transits) FILTER (WHERE period = 'crisis_2024') AS crisis_2024_transits,
           max(transits) FILTER (WHERE period = 'latest')      AS latest_transits,
           max(volume) FILTER (WHERE period = 'baseline')      AS baseline_volume_t,
           max(volume) FILTER (WHERE period = 'crisis_2024')   AS crisis_2024_volume_t,
           max(volume) FILTER (WHERE period = 'latest')        AS latest_volume_t
    FROM by_type
    GROUP BY vessel_type
)
SELECT
    v.vessel_type,
    v.vessel_label,
    w.baseline_transits,
    w.crisis_2024_transits,
    w.latest_transits,
    w.crisis_2024_transits / w.baseline_transits - 1 AS transits_change_2024,
    w.latest_transits / w.baseline_transits - 1      AS transits_change_latest,
    w.baseline_volume_t,
    w.crisis_2024_volume_t,
    w.latest_volume_t,
    w.crisis_2024_volume_t / w.baseline_volume_t - 1 AS volume_change_2024,
    w.latest_volume_t / w.baseline_volume_t - 1      AS volume_change_latest,
    w.baseline_transits / sum(w.baseline_transits) OVER ()  AS baseline_share,
    w.latest_transits / sum(w.latest_transits) OVER ()      AS latest_share,
    (w.baseline_transits - w.crisis_2024_transits)
        / sum(w.baseline_transits - w.crisis_2024_transits) OVER () AS share_of_lost_transits_2024,
    (w.baseline_volume_t - w.crisis_2024_volume_t)
        / sum(w.baseline_volume_t - w.crisis_2024_volume_t) OVER () AS share_of_lost_volume_2024
FROM wide AS w
JOIN gold.dim_vessel_type AS v USING (vessel_type)
ORDER BY v.sort_order;

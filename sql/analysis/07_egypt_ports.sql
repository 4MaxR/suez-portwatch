-- Q4c. Did Egypt's own ports gain or lose? Port calls and estimated import + export tonnage per
-- day, per port, baseline vs 2024 vs the latest window. Ports averaging fewer than one call a
-- week in the baseline stay in the gold layer but are left out here.
WITH by_port AS (
    SELECT f.port_id, p.period,
           sum(f.port_calls) / count(DISTINCT f."date")                AS calls,
           sum(f.port_calls) FILTER (WHERE f.vessel_type = 'container')
               / count(DISTINCT f."date")                              AS box_calls,
           sum(f.import_t + f.export_t) / count(DISTINCT f."date")     AS trade_t
    FROM gold.fact_port_calls AS f
    JOIN gold.dim_period AS p ON f."date" BETWEEN p.start_date AND p.end_date
    WHERE p.period IN ('baseline', 'crisis_2024', 'latest')
    GROUP BY ALL
),
wide AS (
    SELECT port_id,
           max(calls) FILTER (WHERE period = 'baseline')        AS baseline_calls,
           max(calls) FILTER (WHERE period = 'crisis_2024')     AS crisis_2024_calls,
           max(calls) FILTER (WHERE period = 'latest')          AS latest_calls,
           max(box_calls) FILTER (WHERE period = 'baseline')    AS baseline_container_calls,
           max(box_calls) FILTER (WHERE period = 'latest')      AS latest_container_calls,
           max(trade_t) FILTER (WHERE period = 'baseline')      AS baseline_trade_t,
           max(trade_t) FILTER (WHERE period = 'latest')        AS latest_trade_t
    FROM by_port
    GROUP BY port_id
)
SELECT
    d.port_name,
    d.coast,
    w.baseline_calls,
    w.crisis_2024_calls,
    w.latest_calls,
    w.crisis_2024_calls / w.baseline_calls - 1                        AS calls_change_2024,
    w.latest_calls / w.baseline_calls - 1                             AS calls_change_latest,
    w.baseline_container_calls,
    w.latest_container_calls,
    w.latest_container_calls / nullif(w.baseline_container_calls, 0) - 1
                                                                       AS container_calls_change_latest,
    w.baseline_trade_t,
    w.latest_trade_t,
    w.latest_trade_t / nullif(w.baseline_trade_t, 0) - 1               AS trade_t_change_latest
FROM wide AS w
JOIN gold.dim_port AS d USING (port_id)
WHERE w.baseline_calls >= 1.0 / 7
ORDER BY w.baseline_calls DESC;

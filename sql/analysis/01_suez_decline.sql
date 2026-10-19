-- Q1. How far did Suez Canal transits and estimated cargo volume fall, and have they recovered?
-- Daily averages per period, compared with the pre-attack baseline (Jan-Oct 2023).
WITH daily AS (
    SELECT "date", sum(transits) AS transits, sum(volume_t) AS volume_t
    FROM gold.fact_chokepoint_transits
    WHERE chokepoint_id = 'chokepoint1'
    GROUP BY "date"
),
by_period AS (
    SELECT p.period, p.period_label, p.sort_order, p.start_date, p.end_date,
           count(*)          AS days,
           avg(d.transits)   AS transits_per_day,
           avg(d.volume_t)   AS volume_t_per_day
    FROM gold.dim_period AS p
    JOIN daily AS d ON d."date" BETWEEN p.start_date AND p.end_date
    GROUP BY ALL
)
SELECT
    period, period_label, start_date, end_date, days,
    transits_per_day,
    volume_t_per_day,
    transits_per_day / (SELECT transits_per_day FROM by_period WHERE period = 'baseline') - 1
        AS transits_vs_baseline,
    volume_t_per_day / (SELECT volume_t_per_day FROM by_period WHERE period = 'baseline') - 1
        AS volume_vs_baseline,
    volume_t_per_day / transits_per_day AS tonnes_per_transit
FROM by_period
ORDER BY sort_order;

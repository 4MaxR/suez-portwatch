-- Q4b. Transits and tonnage that did not pass Suez since the first attack (19 Nov 2023),
-- measured against the baseline's average for the same calendar month (Jan-Oct 2023). Nov and
-- Dec fall outside the baseline and use its overall average instead.
WITH daily AS (
    SELECT "date", sum(transits) AS transits, sum(volume_t) AS volume_t
    FROM gold.fact_chokepoint_transits
    WHERE chokepoint_id = 'chokepoint1'
    GROUP BY "date"
),
base AS (
    SELECT * FROM daily WHERE "date" BETWEEN DATE '{baseline_start}' AND DATE '{baseline_end}'
),
by_month AS (
    SELECT month("date") AS m, avg(transits) AS t_exp, avg(volume_t) AS v_exp
    FROM base GROUP BY ALL
),
flat AS (SELECT avg(transits) AS t_exp, avg(volume_t) AS v_exp FROM base),
gap AS (
    SELECT d."date",
           d.transits,
           d.volume_t,
           coalesce(e.t_exp, flat.t_exp) AS expected_transits,
           coalesce(e.v_exp, flat.v_exp) AS expected_volume_t
    FROM daily AS d
    LEFT JOIN by_month AS e ON e.m = month(d."date")
    CROSS JOIN flat
    WHERE d."date" >= DATE '2023-11-19'
),
yearly AS (
    SELECT
        year("date")                                AS year,
        count(*)                                    AS days,
        sum(transits)                               AS actual_transits,
        sum(expected_transits)                      AS expected_transits,
        sum(expected_transits - transits)           AS lost_transits,
        sum(volume_t)                               AS actual_volume_t,
        sum(expected_volume_t)                      AS expected_volume_t,
        sum(expected_volume_t - volume_t)           AS lost_volume_t
    FROM gap
    GROUP BY year("date")
)
SELECT
    *,
    lost_transits / expected_transits                        AS lost_transit_share,
    lost_volume_t / expected_volume_t                        AS lost_volume_share,
    sum(lost_transits) OVER (ORDER BY year)                  AS cumulative_lost_transits,
    sum(lost_volume_t) OVER (ORDER BY year)                  AS cumulative_lost_volume_t
FROM yearly
ORDER BY year;

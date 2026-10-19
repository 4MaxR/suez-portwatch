-- Q5. Data quality per place: date coverage, zero days, and whether PortWatch's totals equal
-- the sum of its five vessel-type columns.
WITH chokepoint AS (
    SELECT
        'chokepoint'                                     AS layer,
        c.chokepoint_name                                AS place,
        count(*)                                         AS days_present,
        (SELECT count(*) FROM gold.dim_date)             AS days_expected,
        min(s."date")                                    AS first_date,
        max(s."date")                                    AS last_date,
        count(*) FILTER (WHERE s.transits_total = 0)     AS zero_days,
        count(*) FILTER (WHERE s.transits_total <> s.transits_container + s.transits_dry_bulk
            + s.transits_general_cargo + s.transits_roro + s.transits_tanker)
                                                         AS count_mismatch_days,
        max(abs(s.volume_total_t - (s.volume_container_t + s.volume_dry_bulk_t
            + s.volume_general_cargo_t + s.volume_roro_t + s.volume_tanker_t)))
                                                         AS max_volume_gap_t
    FROM silver.chokepoint_daily AS s
    JOIN gold.dim_chokepoint AS c USING (chokepoint_id)
    WHERE c.route_role IS NOT NULL
    GROUP BY ALL
),
port AS (
    SELECT
        'port',
        p.port_name,
        count(*),
        (SELECT count(*) FROM gold.dim_date
         WHERE "date" <= (SELECT max("date") FROM silver.port_daily)),
        min(s."date"),
        max(s."date"),
        count(*) FILTER (WHERE s.calls_total = 0),
        count(*) FILTER (WHERE s.calls_total <> s.calls_container + s.calls_dry_bulk
            + s.calls_general_cargo + s.calls_roro + s.calls_tanker),
        max(abs(s.import_total_t - (s.import_container_t + s.import_dry_bulk_t
            + s.import_general_cargo_t + s.import_roro_t + s.import_tanker_t)))
    FROM silver.port_daily AS s
    JOIN gold.dim_port AS p USING (port_id)
    GROUP BY ALL
)
SELECT
    *,
    days_present / days_expected   AS coverage,
    zero_days / days_present       AS zero_share
FROM (SELECT * FROM chokepoint UNION ALL SELECT * FROM port)
ORDER BY layer, days_present - zero_days DESC;

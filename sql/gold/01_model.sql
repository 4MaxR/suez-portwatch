-- Gold: analysis-ready star schema. Facts are long (one row per day x place x vessel type),
-- so every query can slice by vessel type without repeating five column names.

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.dim_vessel_type AS
SELECT * FROM (VALUES
    ('container',     'Container',     1),
    ('dry_bulk',      'Dry bulk',      2),
    ('tanker',        'Tanker',        3),
    ('general_cargo', 'General cargo', 4),
    ('roro',          'Ro-ro',         5)
) AS t(vessel_type, vessel_label, sort_order);

-- route_role places each chokepoint on the Asia-Europe corridor (NULL = elsewhere).
CREATE OR REPLACE TABLE gold.dim_chokepoint AS
SELECT
    chokepoint_id,
    chokepoint_name,
    lat,
    lon,
    CASE chokepoint_id
        WHEN 'chokepoint1' THEN 'Red Sea route (north end)'
        WHEN 'chokepoint4' THEN 'Red Sea route (south end)'
        WHEN 'chokepoint7' THEN 'Diversion route'
        WHEN 'chokepoint8' THEN 'Mediterranean gateway'
        WHEN 'chokepoint5' THEN 'Upstream control'
    END AS route_role
FROM silver.chokepoints;

-- Coast decides whether a port sits on the canal's Mediterranean side or on the Red Sea side.
CREATE OR REPLACE TABLE gold.dim_port AS
SELECT
    port_id,
    port_name,
    locode,
    lat,
    lon,
    CASE
        WHEN port_name IN ('Alexandria', 'El Dekheila', 'Sidi Kerir', 'Damietta', 'Port Said',
                           'Egyptian LNG Terminal') THEN 'Mediterranean'
        WHEN port_name IN ('El Sokhna', 'As Suways', 'Al Adabiyah', 'Ras Gharib', 'Zeit Bay',
                           'Ras Shukheir') THEN 'Gulf of Suez'
        ELSE 'Red Sea'
    END AS coast,
    share_egypt_maritime_imports,
    share_egypt_maritime_exports
FROM silver.egypt_ports;

-- Analysis periods. "latest" is the last {latest_window_days} days that both layers cover (the
-- port layer can lag the chokepoint layer by a few days); "latest_2023" is the same calendar
-- window in 2023, a like-for-like seasonal comparison from before the attacks.
CREATE OR REPLACE TABLE gold.dim_period AS
WITH last_day AS (
    SELECT least(
        (SELECT max("date") FROM silver.chokepoint_daily),
        (SELECT max("date") FROM silver.port_daily)
    ) AS d
),
latest AS (
    SELECT CAST(d - INTERVAL ({latest_window_days} - 1) DAY AS DATE) AS start_date, d AS end_date
    FROM last_day
)
SELECT * FROM (
    SELECT 'y2019' AS period, '2019 (pre-COVID)' AS period_label, 1 AS sort_order,
           DATE '2019-01-01' AS start_date, DATE '2019-12-31' AS end_date
    UNION ALL
    SELECT 'baseline', 'Jan-Oct 2023 (baseline)', 2, DATE '{baseline_start}', DATE '{baseline_end}'
    UNION ALL
    SELECT 'crisis_2024', '2024', 3, DATE '{crisis_2024_start}', DATE '{crisis_2024_end}'
    UNION ALL
    SELECT 'year_2025', '2025', 4, DATE '{year_2025_start}', DATE '{year_2025_end}'
    UNION ALL
    SELECT 'latest_2023', 'Same ' || {latest_window_days} || ' days of 2023', 5,
           CAST(start_date - to_years(year(end_date) - 2023) AS DATE),
           CAST(end_date - to_years(year(end_date) - 2023) AS DATE)
    FROM latest
    UNION ALL
    SELECT 'latest', 'Latest ' || {latest_window_days} || ' days', 6, start_date, end_date
    FROM latest
)
ORDER BY sort_order;

CREATE OR REPLACE TABLE gold.dim_date AS
SELECT
    d::DATE                         AS "date",
    year(d)                         AS year,
    month(d)                        AS month,
    CAST(date_trunc('month', d) AS DATE) AS month_start,
    CAST(date_trunc('week', d) AS DATE)  AS week_start
FROM range(
    (SELECT min("date") FROM silver.chokepoint_daily),
    (SELECT max("date") FROM silver.chokepoint_daily) + INTERVAL 1 DAY,
    INTERVAL 1 DAY
) AS t(d);

CREATE OR REPLACE TABLE gold.fact_chokepoint_transits AS
SELECT
    "date",
    chokepoint_id,
    vessel_type,
    transits,
    volume_t
FROM (
    UNPIVOT silver.chokepoint_daily
    ON (transits_container, volume_container_t)         AS container,
       (transits_dry_bulk, volume_dry_bulk_t)           AS dry_bulk,
       (transits_general_cargo, volume_general_cargo_t) AS general_cargo,
       (transits_roro, volume_roro_t)                   AS roro,
       (transits_tanker, volume_tanker_t)               AS tanker
    INTO NAME vessel_type VALUE transits, volume_t
);

CREATE OR REPLACE TABLE gold.fact_port_calls AS
SELECT
    "date",
    port_id,
    vessel_type,
    port_calls,
    import_t,
    export_t
FROM (
    UNPIVOT silver.port_daily
    ON (calls_container, import_container_t, export_container_t)             AS container,
       (calls_dry_bulk, import_dry_bulk_t, export_dry_bulk_t)                AS dry_bulk,
       (calls_general_cargo, import_general_cargo_t, export_general_cargo_t) AS general_cargo,
       (calls_roro, import_roro_t, export_roro_t)                            AS roro,
       (calls_tanker, import_tanker_t, export_tanker_t)                      AS tanker
    INTO NAME vessel_type VALUE port_calls, import_t, export_t
);

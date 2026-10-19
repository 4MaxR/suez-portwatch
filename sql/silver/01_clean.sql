-- Silver: typed, renamed, de-duplicated daily records and clean reference lists.

CREATE SCHEMA IF NOT EXISTS silver;

-- One row per chokepoint per UTC day. Transits are vessel counts; volume_* is PortWatch's
-- estimate of cargo carried (payload share x deadweight tonnage), in metric tonnes.
CREATE OR REPLACE TABLE silver.chokepoint_daily AS
SELECT DISTINCT ON (portid, "date")
    CAST("date" AS DATE)                      AS "date",
    CAST(portid AS VARCHAR)                   AS chokepoint_id,
    CAST(portname AS VARCHAR)                 AS chokepoint_name,
    CAST(n_container AS INTEGER)              AS transits_container,
    CAST(n_dry_bulk AS INTEGER)               AS transits_dry_bulk,
    CAST(n_general_cargo AS INTEGER)          AS transits_general_cargo,
    CAST(n_roro AS INTEGER)                   AS transits_roro,
    CAST(n_tanker AS INTEGER)                 AS transits_tanker,
    CAST(n_total AS INTEGER)                  AS transits_total,
    CAST(capacity_container AS DOUBLE)        AS volume_container_t,
    CAST(capacity_dry_bulk AS DOUBLE)         AS volume_dry_bulk_t,
    CAST(capacity_general_cargo AS DOUBLE)    AS volume_general_cargo_t,
    CAST(capacity_roro AS DOUBLE)             AS volume_roro_t,
    CAST(capacity_tanker AS DOUBLE)           AS volume_tanker_t,
    CAST(capacity AS DOUBLE)                  AS volume_total_t,
    CAST(_extracted_at AS TIMESTAMPTZ)        AS extracted_at
FROM bronze.chokepoint_transits
ORDER BY portid, "date", _extracted_at DESC;

-- One row per Egyptian port per UTC day. Port calls exclude short stops with no draft change
-- (bunkering, anchoring); import/export are estimated tonnes unloaded/loaded.
CREATE OR REPLACE TABLE silver.port_daily AS
SELECT DISTINCT ON (portid, "date")
    CAST("date" AS DATE)                      AS "date",
    CAST(portid AS VARCHAR)                   AS port_id,
    CAST(portname AS VARCHAR)                 AS port_name,
    CAST(portcalls_container AS INTEGER)      AS calls_container,
    CAST(portcalls_dry_bulk AS INTEGER)       AS calls_dry_bulk,
    CAST(portcalls_general_cargo AS INTEGER)  AS calls_general_cargo,
    CAST(portcalls_roro AS INTEGER)           AS calls_roro,
    CAST(portcalls_tanker AS INTEGER)         AS calls_tanker,
    CAST(portcalls AS INTEGER)                AS calls_total,
    CAST(import_container AS DOUBLE)          AS import_container_t,
    CAST(import_dry_bulk AS DOUBLE)           AS import_dry_bulk_t,
    CAST(import_general_cargo AS DOUBLE)      AS import_general_cargo_t,
    CAST(import_roro AS DOUBLE)               AS import_roro_t,
    CAST(import_tanker AS DOUBLE)             AS import_tanker_t,
    CAST("import" AS DOUBLE)                  AS import_total_t,
    CAST(export_container AS DOUBLE)          AS export_container_t,
    CAST(export_dry_bulk AS DOUBLE)           AS export_dry_bulk_t,
    CAST(export_general_cargo AS DOUBLE)      AS export_general_cargo_t,
    CAST(export_roro AS DOUBLE)               AS export_roro_t,
    CAST(export_tanker AS DOUBLE)             AS export_tanker_t,
    CAST(export AS DOUBLE)                    AS export_total_t,
    CAST(_extracted_at AS TIMESTAMPTZ)        AS extracted_at
FROM bronze.egypt_port_calls
ORDER BY portid, "date", _extracted_at DESC;

CREATE OR REPLACE TABLE silver.chokepoints AS
SELECT
    CAST(portid AS VARCHAR)       AS chokepoint_id,
    CAST(portname AS VARCHAR)     AS chokepoint_name,
    CAST(lat AS DOUBLE)           AS lat,
    CAST(lon AS DOUBLE)           AS lon,
    CAST(vessel_count_total AS INTEGER) AS ref_annual_vessels
FROM bronze.ref_chokepoints;

CREATE OR REPLACE TABLE silver.egypt_ports AS
SELECT
    CAST(portid AS VARCHAR)       AS port_id,
    CAST(portname AS VARCHAR)     AS port_name,
    NULLIF(CAST(LOCODE AS VARCHAR), '') AS locode,
    CAST(lat AS DOUBLE)           AS lat,
    CAST(lon AS DOUBLE)           AS lon,
    CAST(vessel_count_total AS INTEGER) AS ref_annual_vessels,
    CAST(share_country_maritime_import AS DOUBLE) / 100 AS share_egypt_maritime_imports,
    CAST(share_country_maritime_export AS DOUBLE) / 100 AS share_egypt_maritime_exports
FROM bronze.ref_egypt_ports;

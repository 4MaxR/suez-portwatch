-- Q4c time series: monthly port calls per day for Egypt's ports, by coast and vessel type.
SELECT
    p.coast,
    f.vessel_type,
    d.month_start,
    sum(f.port_calls) / count(DISTINCT f."date")              AS calls_per_day,
    sum(f.import_t + f.export_t) / count(DISTINCT f."date")   AS trade_t_per_day
FROM gold.fact_port_calls AS f
JOIN gold.dim_port AS p USING (port_id)
JOIN gold.dim_date AS d USING ("date")
GROUP BY ALL
ORDER BY p.coast, f.vessel_type, d.month_start;

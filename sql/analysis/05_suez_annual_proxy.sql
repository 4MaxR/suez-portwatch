-- Q4a. Impact on Egypt: Suez transits and tonnage by calendar year, indexed to 2023, with an
-- illustrative revenue figure that scales the SCA's reported 2023 revenue by the tonnage index.
-- Canal tolls are charged on Suez Canal Net Tonnage, so tonnage tracks revenue better than
-- ship counts do. It is still a proxy, not a reconstruction of SCA accounts: toll rates,
-- rebates and the vessel mix all changed after 2023.
WITH yearly AS (
    SELECT d.year,
           count(DISTINCT f."date")                     AS days,
           sum(f.transits)                              AS transits,
           sum(f.volume_t)                              AS volume_t
    FROM gold.fact_chokepoint_transits AS f
    JOIN gold.dim_date AS d USING ("date")
    WHERE f.chokepoint_id = 'chokepoint1'
    GROUP BY d.year
),
ref AS (SELECT transits / days AS t_day, volume_t / days AS v_day FROM yearly WHERE year = 2023)
SELECT
    y.year,
    y.days,
    y.days < 365                                         AS is_partial_year,
    y.transits,
    y.volume_t,
    y.transits / y.days                                  AS transits_per_day,
    (y.transits / y.days) / ref.t_day                    AS transit_index_2023,
    (y.volume_t / y.days) / ref.v_day                    AS volume_index_2023,
    -- annualised, so a partial year is comparable with full ones
    {sca_revenue_2023_usd} * (y.volume_t / y.days) / ref.v_day AS revenue_proxy_usd_annualised,
    {sca_transits_2023} / (SELECT transits FROM yearly WHERE year = 2023)
                                                         AS sca_to_portwatch_transits_2023
FROM yearly AS y, ref
ORDER BY y.year;

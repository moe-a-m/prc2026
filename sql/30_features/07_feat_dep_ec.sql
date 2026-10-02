-- EUROCONTROL airport aggregates joined to each departure (M-017), config-gated (extra_tables).
--   monthly (airport × UTC month of take-off): unimpeded reference and additional taxi-out per flight, seconds
--   daily (airport × UTC date of take-off): pre-departure delay per IFR departure (min), ATFM slot adherence shares
CREATE OR REPLACE TABLE feat_dep_ec AS
WITH m AS (
    SELECT APT_ICAO AS airport, make_date(YEAR::INT, MONTH_NUM::INT, 1) AS month,
           60.0 * TOTAL_REF_TIME_MIN / NULLIF(TOTAL_REF_NB_FL, 0) AS ec_m_taxi_ref_s,
           60.0 * TOTAL_ADD_TIME_MIN / NULLIF(TOTAL_REF_NB_FL, 0) AS ec_m_taxi_add_s,
           TF AS ec_m_flights
    FROM raw_ec_taxi
),
p AS (SELECT APT_ICAO AS airport, FLT_DATE::DATE AS d, FLT_DEP_1 AS ec_d_dep,
             DLY_ALL_PRE_2 / NULLIF(FLT_DEP_IFR_2, 0) AS ec_d_predep_dly_min FROM raw_ec_predep),
s AS (SELECT APT_ICAO AS airport, FLT_DATE::DATE AS d,
             FLT_DEP_OUT_LATE_1 / NULLIF(FLT_DEP_REG_1, 0) AS ec_d_slot_late_share,
             FLT_DEP_OUT_EARLY_1 / NULLIF(FLT_DEP_REG_1, 0) AS ec_d_slot_early_share,
             FLT_DEP_REG_1 AS ec_d_regulated_dep FROM raw_ec_slot),
d AS (SELECT mvt_id, airport, month, (timezone('UTC', to_timestamp(t_mvt_epoch)))::DATE AS d FROM feat_dep)
SELECT d.mvt_id, m.ec_m_taxi_ref_s, m.ec_m_taxi_add_s, m.ec_m_taxi_ref_s + m.ec_m_taxi_add_s AS ec_m_taxi_mean_s,
       p.ec_d_dep, p.ec_d_predep_dly_min, s.ec_d_slot_late_share, s.ec_d_slot_early_share, s.ec_d_regulated_dep
FROM d
LEFT JOIN m ON m.airport = d.airport AND m.month = d.month
LEFT JOIN p ON p.airport = d.airport AND p.d = d.d
LEFT JOIN s ON s.airport = d.airport AND s.d = d.d;

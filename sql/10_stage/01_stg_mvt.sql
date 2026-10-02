-- Typed, renamed movements: training + ranking in one table, timestamps as naive UTC.
-- `airport` = ADEP for DEP, ADES for ARR (verified: reports/checks/p1_airport_columns.md).
-- `y` = TAXITIME_SEC_mvt; NULL for ranking DEP rows (blanked by the organizers).
CREATE OR REPLACE TABLE stg_mvt AS
WITH u AS (
    SELECT 'train' AS ds, src_month, * EXCLUDE (src_month, src_file, filename) FROM raw_training
    UNION ALL BY NAME
    SELECT 'rank' AS ds, date_trunc('month', timezone('UTC', MVT_TIME_UTC_mvt))::DATE AS src_month,
           * EXCLUDE (src_file, filename) FROM raw_ranking
)
SELECT
    ds,
    src_month                                   AS month,
    CAST(MVT_ID_mvt AS BIGINT)                  AS mvt_id,
    CAST(FLIGHT_ID_mvt AS BIGINT)               AS flight_id,
    PHASE_mvt                                   AS phase,
    CASE PHASE_mvt WHEN 'DEP' THEN ADEP_mvt ELSE ADES_mvt END AS airport,
    ADEP_mvt AS adep_mvt, ADES_mvt AS ades_mvt,
    FLIGHT_mvt AS flight_mvt, FLIGHT_RULE_mvt AS flight_rule_mvt,
    timezone('UTC', MVT_TIME_UTC_mvt)           AS t_mvt,
    timezone('UTC', BLOCK_TIME_UTC_mvt)         AS t_block,
    timezone('UTC', SCHED_TIME_UTC_mvt)         AS t_sched,
    AIRCRAFT_TYPE_mvt AS actype_mvt,
    NULLIF(RUNWAY_mvt, 'NA')                    AS runway,
    STAND_mvt                                   AS stand,
    TAXITIME_SEC_mvt                            AS y,
    timezone('UTC', LOBT_flt)  AS t_lobt,
    timezone('UTC', IOBT_flt)  AS t_iobt,
    timezone('UTC', EOBT_1_flt) AS t_eobt1,
    timezone('UTC', ARVT_1_flt) AS t_arvt1,
    timezone('UTC', AOBT_3_flt) AS t_aobt3,
    timezone('UTC', ARVT_3_flt) AS t_arvt3,
    CALLSIGN_flt AS callsign, ADEP_flt AS adep_flt, ADES_flt AS ades_flt, ADES_FILED_flt AS ades_filed_flt,
    MARKET_SEGMENT_flt AS market, FLIGHT_RULE_flt AS flight_rule_flt, FLIGHT_TYPE_flt AS flight_type,
    AIRCRAFT_TYPE_flt AS actype_flt, WK_TBL_CAT_flt AS wake, AIRCRAFT_OPERATOR_flt AS operator
FROM u;

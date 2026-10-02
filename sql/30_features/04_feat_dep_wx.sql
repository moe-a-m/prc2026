-- Weather at the take-off (CLAUDE.md §6). Station = airport ICAO. Two reference views:
--   * latest METAR at or before the take-off (ASOF); observation age kept; if age > 120 min every
--     as-of field is NULL and wx_stale = true (no silent imputation);
--   * aggregates over the 3 h before the take-off (covers the taxi and de-icing window).
-- Feature table kept separate from feat_dep so weather can be switched on/off per config (ablation).
CREATE OR REPLACE TABLE feat_dep_wx AS
WITH d AS (SELECT mvt_id, airport, timezone('UTC', to_timestamp(t_mvt_epoch)) AS t FROM feat_dep),
a AS (
    SELECT d.mvt_id, m.t_obs, m.temp_c, m.dewpt_c, m.wind_dir_deg, m.wind_ms, m.gust_ms, m.vis_m, m.ceiling_m,
           m.rvr_min_m, m.wx_snow, m.wx_freezing, m.wx_thunder, m.wx_rain, m.wx_fog,
           (epoch(d.t) - epoch(m.t_obs)) / 60.0 AS wx_age_min
    FROM d ASOF LEFT JOIN stg_metar m ON m.station = d.airport AND m.t_obs <= d.t
),
w AS (
    SELECT d.mvt_id,
        count(m.t_obs)                       AS wx3h_n_obs,
        min(m.vis_m)                         AS wx3h_min_vis_m,
        min(m.ceiling_m)                     AS wx3h_min_ceiling_m,
        min(m.temp_c)                        AS wx3h_min_temp_c,
        max(coalesce(m.gust_ms, m.wind_ms))  AS wx3h_max_wind_ms,
        bool_or(m.wx_snow)                   AS wx3h_snow,
        bool_or(m.wx_freezing)               AS wx3h_freezing,
        bool_or(m.wx_thunder)                AS wx3h_thunder,
        sum(m.wx_snow::INT)                  AS wx3h_snow_obs
    FROM d LEFT JOIN stg_metar m
      ON m.station = d.airport AND m.t_obs <= d.t AND m.t_obs > d.t - INTERVAL 3 HOURS
    GROUP BY d.mvt_id
)
SELECT a.mvt_id,
    a.wx_age_min, a.wx_age_min IS NULL OR a.wx_age_min > 120 AS wx_stale,
    CASE WHEN a.wx_age_min <= 120 THEN a.temp_c END       AS wx_temp_c,
    CASE WHEN a.wx_age_min <= 120 THEN a.temp_c - a.dewpt_c END AS wx_dewpt_spread_c,
    CASE WHEN a.wx_age_min <= 120 THEN a.wind_ms END      AS wx_wind_ms,
    CASE WHEN a.wx_age_min <= 120 THEN a.gust_ms END      AS wx_gust_ms,
    CASE WHEN a.wx_age_min <= 120 THEN a.vis_m END        AS wx_vis_m,
    CASE WHEN a.wx_age_min <= 120 THEN a.ceiling_m END    AS wx_ceiling_m,
    CASE WHEN a.wx_age_min <= 120 THEN a.rvr_min_m END    AS wx_rvr_min_m,
    CASE WHEN a.wx_age_min <= 120 THEN a.wx_snow END      AS wx_snow,
    CASE WHEN a.wx_age_min <= 120 THEN a.wx_freezing END  AS wx_freezing,
    CASE WHEN a.wx_age_min <= 120 THEN a.wx_thunder END   AS wx_thunder,
    CASE WHEN a.wx_age_min <= 120 THEN a.wx_rain END      AS wx_rain,
    CASE WHEN a.wx_age_min <= 120 THEN a.wx_fog END       AS wx_fog,
    w.* EXCLUDE (mvt_id)
FROM a JOIN w USING (mvt_id);

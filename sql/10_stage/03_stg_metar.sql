-- Typed METAR in SI units. Source units (IEM download page, snapshot docs/references/iem_asos_download_page_2026-10-02.html):
-- tmpf/dwpf °F, sknt/gust knots, vsby statute miles, skyl* feet, alti inches Hg; 'M' = missing.
-- Factors: 1 kt = 0.514444 m/s; 1 statute mile = 1609.344 m; 1 ft = 0.3048 m (exact definitions).
-- Duplicate rule: one row per (station, valid); if several, keep the one whose raw METAR contains ' COR '
-- (correction supersedes original), else the longest raw text. Enforced by sql/90_checks/07_metar_unique.sql.
CREATE OR REPLACE TABLE stg_metar AS
WITH t AS (
    SELECT
        station,
        strptime(valid, '%Y-%m-%d %H:%M') AS t_obs,     -- requested with tz=Etc/UTC
        (TRY_CAST(NULLIF(tmpf, 'M') AS DOUBLE) - 32) * 5 / 9  AS temp_c,
        (TRY_CAST(NULLIF(dwpf, 'M') AS DOUBLE) - 32) * 5 / 9  AS dewpt_c,
        TRY_CAST(NULLIF(drct, 'M') AS DOUBLE)                  AS wind_dir_deg,
        TRY_CAST(NULLIF(sknt, 'M') AS DOUBLE) * 0.514444       AS wind_ms,
        TRY_CAST(NULLIF(gust, 'M') AS DOUBLE) * 0.514444       AS gust_ms,
        TRY_CAST(NULLIF(vsby, 'M') AS DOUBLE) * 1609.344       AS vis_m,
        -- ceiling: lowest BKN/OVC/VV layer base
        least(
            CASE WHEN skyc1 IN ('BKN','OVC','VV') THEN TRY_CAST(NULLIF(skyl1,'M') AS DOUBLE) END,
            CASE WHEN skyc2 IN ('BKN','OVC','VV') THEN TRY_CAST(NULLIF(skyl2,'M') AS DOUBLE) END,
            CASE WHEN skyc3 IN ('BKN','OVC','VV') THEN TRY_CAST(NULLIF(skyl3,'M') AS DOUBLE) END,
            CASE WHEN skyc4 IN ('BKN','OVC','VV') THEN TRY_CAST(NULLIF(skyl4,'M') AS DOUBLE) END
        ) * 0.3048                                             AS ceiling_m,
        NULLIF(wxcodes, 'M')                                   AS wxcodes,
        metar,
        metar LIKE '% AUTO %'                                  AS is_auto,
        metar LIKE '% COR %'                                   AS is_cor,
        -- min RVR in metres over all runway groups, e.g. R25C/P2000N, R07R/0550V0800U (first value used)
        list_min(list_transform(regexp_extract_all(metar, ' R\d{2}[LCR]?/[PM]?(\d{4})', 1), x -> CAST(x AS INTEGER))) AS rvr_min_m,
        src_file
    FROM raw_metar
),
r AS (
    SELECT *, row_number() OVER (PARTITION BY station, t_obs ORDER BY is_cor DESC, length(metar) DESC, metar) AS rn FROM t  -- metar: deterministic tie-break
)
SELECT * EXCLUDE (rn),
    -- present-weather groups, WMO code table 4678 (w'w') descriptors/phenomena, matched on IEM's parsed codes
    coalesce(regexp_matches(wxcodes, 'SN|SG|PL'), false)         AS wx_snow,
    coalesce(regexp_matches(wxcodes, 'FZ'), false)               AS wx_freezing,
    coalesce(regexp_matches(wxcodes, 'TS'), false)               AS wx_thunder,
    coalesce(regexp_matches(wxcodes, '(^|[^A-Z])(\+|-)?(SH|TS|FZ)?(RA|DZ)'), false) AS wx_rain,
    coalesce(regexp_matches(wxcodes, 'FG'), false)               AS wx_fog,
    coalesce(regexp_matches(wxcodes, 'GR|GS'), false)            AS wx_hail
FROM r WHERE rn = 1;

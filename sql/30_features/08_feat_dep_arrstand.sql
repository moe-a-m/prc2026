-- Stand remoteness from ARRIVALS (M-024): median and count of ARR taxi-in (0–3600 s) per (airport, stand) over
-- 2025 + 2026 arrivals. Uses only ARR labels, which are intact in the ranking set, so it is current for 2026 stands
-- (e.g. EDDM 103–108, unseen in 2025 departures) and never reads departure labels.
CREATE OR REPLACE TABLE feat_dep_arrstand AS
WITH a AS (
    SELECT airport, stand, median(y) AS arr_stand_taxi_in_med, count(*) AS arr_stand_n
    FROM stg_mvt WHERE phase = 'ARR' AND stand IS NOT NULL AND y BETWEEN 0 AND 3600 GROUP BY ALL
)
SELECT f.mvt_id, a.arr_stand_taxi_in_med, a.arr_stand_n
FROM feat_dep f LEFT JOIN a USING (airport, stand);

-- requires-glob: data/external/osm_aeroway/raw/*.json
-- Stand coordinates per challenge stand code (M-021). Codes normalised (upper case, no spaces/dashes, leading zeros of
-- the numeric part removed). Several OSM elements with one ref are averaged. Fallback for sub-stands (EDDM 210A/210B
-- vs challenge 210): match on the code without a trailing letter, averaged over the sub-stands.
CREATE OR REPLACE TABLE stg_stand_geo AS
WITH norm AS (
    SELECT airport, lat, lon,
           regexp_replace(upper(replace(replace(coalesce(ref, name), ' ', ''), '-', '')), '^([A-Z]*)0+([0-9])', '\1\2') AS code
    FROM raw_osm_aeroway WHERE aeroway = 'parking_position' AND coalesce(ref, name) IS NOT NULL
),
exact AS (SELECT airport, code, avg(lat) AS lat, avg(lon) AS lon, count(*) AS n_osm FROM norm GROUP BY ALL),
base AS (SELECT airport, regexp_replace(code, '[A-Z]$', '') AS code, avg(lat) AS lat, avg(lon) AS lon, count(*) AS n_osm
         FROM norm WHERE regexp_matches(code, '[0-9][A-Z]$') GROUP BY ALL),
stands AS (
    SELECT DISTINCT airport, stand,
           regexp_replace(upper(replace(replace(stand, ' ', ''), '-', '')), '^([A-Z]*)0+([0-9])', '\1\2') AS code
    FROM stg_mvt WHERE stand IS NOT NULL
)
SELECT s.airport, s.stand, coalesce(e.lat, b.lat) AS lat, coalesce(e.lon, b.lon) AS lon,
       CASE WHEN e.lat IS NOT NULL THEN 'exact' ELSE 'base' END AS match_kind
FROM stands s
LEFT JOIN exact e ON e.airport = s.airport AND e.code = s.code
LEFT JOIN base b ON b.airport = s.airport AND b.code = s.code
WHERE coalesce(e.lat, b.lat) IS NOT NULL;

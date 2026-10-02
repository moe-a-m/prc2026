-- requires-glob: data/external/osm_aeroway/raw/*.json
-- OSM aeroway features (ODbL; docs/data_sources/osm_aeroway.md), one row per element; ways use the Overpass centre.
CREATE OR REPLACE TABLE raw_osm_aeroway AS
SELECT regexp_extract(filename, '([A-Z]{4})_', 1) AS airport, e.type AS osm_type, e.id AS osm_id,
       e.tags.aeroway AS aeroway, e.tags.ref AS ref, e.tags.name AS name,
       coalesce(e.lat, e.center.lat) AS lat, coalesce(e.lon, e.center.lon) AS lon,
       regexp_extract(filename, '[^/]+$') AS src_file
FROM (SELECT unnest(elements) AS e, filename
      FROM read_json('data/external/osm_aeroway/raw/*.json', filename = true, union_by_name = true,
                     maximum_object_size = 50000000));

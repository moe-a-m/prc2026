-- Airport reference point and field elevation (OurAirports) for the 10 challenge airports.
CREATE OR REPLACE TABLE ref_airport_geo AS
SELECT ident AS airport, latitude_deg AS lat, longitude_deg AS lon, elevation_ft AS elev_ft
FROM raw_oa_airports WHERE ident IN (SELECT airport FROM ref_airport);

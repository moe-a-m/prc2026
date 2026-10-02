-- IANA time zone of each challenge airport (for local-time calendar features).
CREATE OR REPLACE TABLE ref_airport AS
SELECT * FROM (VALUES
    ('EDDF', 'Europe/Berlin'), ('EDDM', 'Europe/Berlin'), ('EGLL', 'Europe/London'),
    ('EHAM', 'Europe/Amsterdam'), ('LEBL', 'Europe/Madrid'), ('LEMD', 'Europe/Madrid'),
    ('LFPG', 'Europe/Paris'), ('LIRF', 'Europe/Rome'), ('LTFM', 'Europe/Istanbul'),
    ('LSZH', 'Europe/Zurich')
) t(airport, tz);

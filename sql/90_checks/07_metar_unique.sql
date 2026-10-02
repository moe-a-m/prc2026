-- One METAR per station and observation time after the duplicate rule in sql/10_stage/03_stg_metar.sql.
SELECT station, t_obs, count(*) FROM stg_metar GROUP BY ALL HAVING count(*) > 1;

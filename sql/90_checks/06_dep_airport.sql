-- Every departure belongs to one of the 10 challenge airports.
SELECT DISTINCT airport FROM clean_dep WHERE airport NOT IN (SELECT airport FROM ref_airport);

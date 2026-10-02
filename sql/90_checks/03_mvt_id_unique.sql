-- mvt_id is unique across training + ranking and integral.
SELECT mvt_id, count(*) FROM stg_mvt GROUP BY mvt_id HAVING count(*) > 1
UNION ALL
SELECT CAST(MVT_ID_mvt AS BIGINT), 1 FROM raw_training WHERE MVT_ID_mvt <> floor(MVT_ID_mvt);

-- final_submitting.parquet IDs must equal the ranking DEP IDs exactly, with no duplicates.
SELECT 'missing_in_sub' AS issue, MVT_ID_mvt FROM raw_ranking WHERE PHASE_mvt = 'DEP'
    AND MVT_ID_mvt NOT IN (SELECT MVT_ID_mvt FROM raw_submitting)
UNION ALL
SELECT 'extra_in_sub', MVT_ID_mvt FROM raw_submitting
    WHERE MVT_ID_mvt NOT IN (SELECT MVT_ID_mvt FROM raw_ranking WHERE PHASE_mvt = 'DEP')
UNION ALL
SELECT 'dup_in_sub', MVT_ID_mvt FROM raw_submitting GROUP BY MVT_ID_mvt HAVING count(*) > 1;

-- Final-phase ranking set must have exactly 670,790 DEP rows (final_submitting.parquet rows,
-- reports/checks/final_phase_files.md; the public phase had 344,841).
SELECT n FROM (SELECT count(*) n FROM raw_ranking WHERE PHASE_mvt = 'DEP') WHERE n <> 670790;

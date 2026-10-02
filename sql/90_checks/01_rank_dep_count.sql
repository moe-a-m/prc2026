-- Ranking set must have exactly 344,841 DEP rows (organizer result JSON, reissue 2026-09-04).
SELECT n FROM (SELECT count(*) n FROM raw_ranking WHERE PHASE_mvt = 'DEP') WHERE n <> 344841;

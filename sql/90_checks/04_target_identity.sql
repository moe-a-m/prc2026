-- Target identity on training DEP rows: TAXITIME = MVT − BLOCK (seconds).
SELECT mvt_id, y, epoch(t_mvt) - epoch(t_block) AS d FROM clean_dep
WHERE ds = 'train' AND (y IS NULL OR y <> epoch(t_mvt) - epoch(t_block));

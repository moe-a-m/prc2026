-- Ranking DEP rows must have block time and target blank (train/serve parity assumption).
SELECT mvt_id FROM clean_dep WHERE ds = 'rank' AND (y IS NOT NULL OR t_block IS NOT NULL);

# Final-phase challenge files (2026-10-08)

Organizer e-mail 2026-10-08 (docs/references/organizer_email_2026-10-08_final_phase.md). Bucket
`dc26:prc-2026-datasets` gained `final_ranking.parquet` (85,853,399 bytes, SHA256 4b0692a7…) and
`final_submitting.parquet` (3,003,722 bytes, SHA256 b3445d80…); downloaded with `make download` into
data/raw/ranking/ and data/raw/submitting/ (manifest). DuckDB 1.x, session `SET TimeZone='UTC'`.

## Rows per UTC month and phase (final_ranking.parquet)

```sql
SELECT month(MVT_TIME_UTC_mvt) m, PHASE_mvt, count(*) FROM 'data/raw/ranking/final_ranking.parquet' GROUP BY ALL ORDER BY ALL
```
| m | PHASE | n |
|---|---|---|
| 1 | ARR | 152,871 |
| 1 | DEP | 152,719 |
| 2 | ARR | 144,274 |
| 2 | DEP | 144,158 |
| 6 | ARR | 181,440 |
| 6 | DEP | 181,791 |
| 7 | ARR | 191,822 |
| 7 | DEP | 192,122 |

Totals: DEP 670,790, ARR 670,407. All DEP rows have BLOCK_TIME_UTC_mvt and TAXITIME_SEC_mvt null; all ARR rows have both.

## Submission template

final_submitting.parquet: 670,790 rows, 670,790 distinct MVT_ID_mvt (DOUBLE), TAXITIME_SEC_mvt (INTEGER) all null.
Anti-joins with the final ranking DEP IDs: 0 template IDs missing from the ranking, 0 ranking DEP IDs missing from the template.

## Relation to the public-phase ranking.parquet

- Same 33 columns with identical types.
- All 689,534 rows of ranking.parquet (344,841 DEP + 344,693 ARR) have their MVT_ID_mvt in the final file (left join, 0 unmatched); no duplicate IDs.
- Per-column differences on the joined rows (`IS DISTINCT FROM`): MVT_TIME_UTC_mvt 633,739; TAXITIME_SEC_mvt 330,721
  (ARR only); BLOCK_TIME_UTC_mvt 316,835 (ARR only); every other column identical (AOBT_3_flt: 0 changed).
- Change in MVT_TIME (final − old): integers in [−12, +12] s, symmetric, triangular-shaped (DEP: 28,190 at 0, 26,360 / 25,888
  at ∓1, … 412 / 477 at ∓12); mean +0.01 s. ARR block-time change is almost exactly opposite (corr −0.99 with the
  MVT change), and the ARR taxi-in is recomputed from the changed times.
- Same perturbation pattern exists in the files we already had: at LTFM, MVT − AOBT_3_flt for departures has no spike
  at exactly 1,200 s but a spread over 1,188–1,212 s in the 2025 training files and in both ranking files:

| file | x = 1200 s | 1188 ≤ x ≤ 1212 | x whole minute | n |
|---|---|---|---|---|
| training 2025-01 | 533 | 6,719 | 1,709 | 21,136 |
| training 2025-07 | 998 | 11,823 | 2,083 | 24,746 |
| ranking.parquet | 1,440 | 18,117 | 3,877 | 46,860 |
| final_ranking.parquet | 3,004 | 35,433 | 7,408 | 88,464 |

  (x = epoch(MVT_TIME_UTC_mvt) − epoch(AOBT_3_flt), LTFM departures, `ADEP_mvt='LTFM'`.)

Reading: the final file carries a fresh draw of the organizers' timestamp perturbation (±12 s) on MVT and ARR block
times; training and the earlier ranking file show the same kind of perturbation, so it is not a new train/serve
difference. Predictions for the Jan/Jul rows will differ slightly from v11's public-phase predictions because the
inputs moved by a few seconds. The scored truth for departures (original or perturbed take-off) is not stated — asked
in docs/OPEN_QUESTIONS.md.

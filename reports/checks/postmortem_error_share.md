# Check: postmortem_error_share

Run at 2026-11-09T13:12:11+00:00 (UTC). Input: `reports/experiments/EXP-118.md` (final v11 recipe, Jan/Jul-2025 hold-outs), table "Flagged vs clean / NM-matched vs unmatched", flag `f_no_nm_match`. Pure arithmetic on that table; no new model run.

## 1. Where our squared error sits

| fold | n_unmatched | share of rows | rmse_unmatched | rmse_matched | rmse_all | unmatched share of SSE |
|---|---|---|---|---|---|---|
| jan | 1432 | 0.93% | 2842.3 | 191.7 | 334.2 | 67.4% |
| jul | 3934 | 2.06% | 1215.3 | 247.5 | 300.8 | 33.7% |
| combined | 5366 | 1.56% | 1799.7 | 224.2 | 316.1 | 50.5% |

## 2. July 2025 counterfactuals (other teams' stated July figures; their folds and row filters differ from ours, so these are indicative)

| scenario | rmse_unmatched | rmse_matched | pooled Jul RMSE | change vs ours |
|---|---|---|---|---|
| ours (EXP-118) | 1215.3 | 247.5 | 300.8 | +0.0 |
| unmatched at strong-crane July no-NM RMSE 1,090 s | 1090 | 247.5 | 290.7 | -10.1 |
| matched at zesty-puzzle July NM-matched RMSE 200.4 s | 1215.3 | 200.4 | 264.2 | -36.6 |
| both | 1090 | 200.4 | 252.7 | -48.1 |

January is not given a counterfactual: no top team states a January unmatched-row RMSE we could find. For reference, zesty-puzzle states January NM-matched RMSE 167.2 s (ours 191.7 s).

## 3. Same July-2025 hold-out rows vs strong-crane (rank 8)

strong-crane `paper/paper_final_phase.pdf` (commit deba7d3a8cb4) Tables 7–8 score the July-2025 hold-out on 190,713 departures (3,938 without an NM record) — the same row count as ours (3,934 unmatched by our `f_no_nm_match`). Their "Final" stage is before their LOBT window (259.9; 259.4 after it).

| population | ours (EXP-118) | strong-crane | difference |
|---|---|---|---|
| all | 300.76 | 259.9 | +40.9 |
| NM record / matched | 247.5 | 211.1 | +36.4 |
| no NM record / unmatched | 1215.3 | 1076.5 | +138.8 |

| airport | ours | strong-crane | difference |
|---|---|---|---|
| LIRF | 751.3 | 629.7 | +121.6 |
| LSZH | 182.2 | 120.7 | +61.5 |
| EDDF | 180.7 | 125.5 | +55.2 |
| EHAM | 140.8 | 110.2 | +30.6 |
| LEBL | 253.6 | 225.3 | +28.3 |
| LEMD | 187.2 | 163.4 | +23.8 |
| LTFM | 275.9 | 256.0 | +19.9 |
| EDDM | 166.6 | 147.2 | +19.4 |
| EGLL | 284.1 | 267.4 | +16.7 |
| LFPG | 248.0 | 237.7 | +10.3 |

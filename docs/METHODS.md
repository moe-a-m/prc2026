# Methods and provenance

Every modelling or cleaning method used in the pipeline, with its provenance (CLAUDE.md §1.3):
(a) official documentation, (b) peer-reviewed paper, (c) past PRC repo, (d) dated forum statement
(local, uncommitted export `docs/references/forum_discussion.md` of `#prc-data-competition`; cited by
author and date, item numbers refer to that export), (e) experiment in this repo.
Literature citations marked *(verify)* were written from memory and must be checked against the paper before
the JOAS write-up. Verified bibliography with URLs: `docs/references/literature_review_2026-10-02.md`.

## Final model at a glance (submission v7 = EXP-079, board 279.40)
Task framing: at ranking time the take-off is known, so predicting taxi-out = estimating the airport-recorded
off-block (AOBT). Errors are dominated by label defects (schedule echoes, day-shifted dates) on a small share of
rows; RMSE rewards the conditional mean, so ambiguous rows are hedged, never dropped (M-002).

| Stage | Method | What it does | Hold-out RMSE Jan / Jul 2025 after the stage |
|---|---|---|---|
| 0 | M-001 | month hold-out validation (train 11 months, predict Jan or Jul) | — |
| 1 | M-003 | reference: global median | 610.5 / 753.8 (EXP-001) |
| 2 | M-004…M-011 | LightGBM (L2, raw target) on NM time deltas, calendar, congestion, runway sequence, stand occupancy from ARR rows, label-defect indicators, month-grouped target encodings | 372.8 / 397.3 (EXP-011) |
| 3 | per-airport models (M-014 diagnostic) | one model per airport stops LIRF's echo pattern leaking to other airports | 350.9 / 386.8 (EXP-022) |
| 4 | M-012 | METAR weather (IEM) | 347.4 / 378.1 (EXP-025) |
| 5 | M-019 + seeds | 3-seed LightGBM (EXP-030) and 3-seed CatBoost (EXP-043) on the same inputs, cross-fitted NNLS blend (0.478 / 0.521) | 347.3 / 361.1 (EXP-044) |
| 6 | M-026 | three-regime hedge for NM-unmatched flights ≥ 6 h late at echo-prone airports (26 ranking rows) | 339.3 / 330.2 (EXP-045) |
| 7 | M-018, M-021, M-028 | adsb.lol surface tracks: where the aircraft is seen leaving its own stand, shrink toward that off-block estimate (gated, per-airport offset, cross-fitted) | 337.2 / 328.2 (EXP-050) |
| 7b | M-028 second source | same for aircraft seen at the stand only while moving (first sighting there) | 335.8 / 327.0 (EXP-051) |
| 8 | determinism fix + 5 seeds | tie-inclusive queue counts (identical features on every rebuild), 5 seeds per family (EXP-060–069), same stages 5–7b → final model | 335.9 / 326.7 (EXP-079) |

Board history (`docs/SUBMISSIONS.md`): v1 347.2 (stage 2) → v2 319.9 (4) → v3 299.1 (5, 1-seed CatBoost) →
v4 287.5 (6) → v5 283.2 (7) → v6 279.8 (7b) → v7 279.4 (same recipe, 5 seeds per family, deterministic features). The board moved in the direction of the local hold-outs every time; no choice was made
on board scores.

Tried and rejected (each with its experiment row in `docs/EXPERIMENTS.md`): `MVT − AOBT_3` as the answer (EXP-009),
MLP with entity embeddings alone or blended (EXP-019, EXP-027), residual corrector (EXP-026), same-runway queue +
P10 unimpeded reference (EXP-023), EUROCONTROL airport aggregates as inputs (EXP-024), NM default-taxi features
(EXP-020), linear-leaf trees (EXP-033), NM-proxy offset (EXP-034), stand remoteness (EXP-035), record-precision
markers (EXP-038), split LIRF models (EXP-040), CatBoost lr 0.05 (gain vanished in the blend, EXP-047).
Data sources and licences: `docs/DATA_SOURCES.md`.

## M-001 Month hold-out validation (Jan-2025, Jul-2025)
Train on the other 11 months of 2025, predict the held-out month; report both and combined.
- (d) a participant, 27/09/2026 (item 59): month-based validation on the scored months tracked the board in direction;
  random/day folds misled. a participant's own variant is train-Jan→test-Jul and vice versa; we use the CLAUDE.md §9
  protocol (11 training months) as primary.
- (d) a participant, 28/09/2026 (item 63): a few rows can carry ~30% of squared error — always look at top rows.

## M-002 Flag, don't drop
Suspicious rows get boolean flags in `clean_dep`; no training row is removed.
- (d) a participant, 27/09/2026 (item 59, point 3) and 27/09/2026 23:13 (item 62, point 1): keep contradictory rows and
  hedge rather than commit.
- (e) `reports/checks/p1_defect_near_echo.md`: defective labels are a large share of the error and also occur in
  the scored set by construction (same source), so they must be predicted, not removed.

## M-003 Group-statistic baselines
Global / airport / airport×runway / airport×stand×runway median and mean, with fallback to coarser groups.
- (a) simple statistics, CLAUDE.md §10 P2. Results EXP-001…EXP-008.

## M-004 Take-off minus NM actual off-block (`MVT − AOBT_3`)
- (d) a participant, 17/09/2026 (item 10).
- (e) `reports/checks/p1_aobt3_error.md`, `p1_x_minute_concentration.md`: AOBT_3 is mostly minute-rounded and,
  for many flights, clusters at take-off minus a fixed whole-minute value per airport (e.g. 42% of LTFM rows at
  exactly 20 min), i.e. it is frequently NM-derived rather than an airport off-block. Used as a feature, not as an
  answer. Results EXP-009, EXP-010.

## M-005 Out-of-fold target encoding of (airport, stand, runway) and related keys
Median target per key; training rows use leave-one-month-out statistics, held-out/ranking rows use all
training months.
- (d) a participant, 17/09/2026 18:42 (item 9): stand→runway median taxi time encodes distance in target units.
- Month grouping: CLAUDE.md §9 (any target encoding uses month-grouped folds).

## M-006 Airport and runway congestion counts
Counts of departures/arrivals at the airport and on the same runway in windows around the take-off
(10/30 min before, 10 min after, ±30 min), built from both ARR and DEP rows.
- (b) Idris, Clarke, Bhuva & Kang, "Queuing Model for Taxi-Out Time Estimation", *Air Traffic Control
  Quarterly* 10(1), 1–22, 2002, DOI 10.2514/atcq.10.1.1 — take-off queue size as the main predictor.
- (b) Simaiakis & Balakrishnan, "A Queuing Model of the Airport Departure Process", *Transportation Science*
  50(1), 94–109, 2016, DOI 10.1287/trsc.2015.0603.
- (d) a participant, 17/09/2026 (item 8): airport-hour congestion aggregates hold most of the signal.

## M-007 Queue position from NM off-block
`n_takeoffs_since_aobt3` = departures that took off at the airport between this flight's AOBT_3 and its take-off;
`n_taxiing_at_mvt` = departures with AOBT_3 ≤ t that are not yet airborne. Implemented with cumulative event
counts + ASOF joins.
- (b) Idris et al. 2002 (as M-006): queue length during the taxi.
- (e) measured in EXP-011 (feature importance) and its ablation.

## M-008 Runway departure sequence and wake category
Gap to the previous / next take-off on the same runway, wake category of the previous departure.
- (d) organizer, 17/09/2026 18:03 (item 6); a participant, 17/09/2026 18:34 (items 7–8): separation ladder visible,
  small gain once congestion features exist.

## M-009 Stand occupancy from ARR rows
Time from the latest (and second latest) ARR in-block at the same stand to this take-off; time from the previous
departure from the same stand. An arrival that blocks in at the stand after this flight's off-block bounds the
off-block from above.
- (d) a participant, 22/09/2026 (item 26): last arrival at the same stand as a legitimate operational feature.
- (d) organizer, 19/09/2026 (items 16–18): the model is post-ops; no feature cut-off restriction.

## M-010 Label-defect indicators as features
`d_sched` (take-off − scheduled), `day_shift` (calendar days between scheduled and take-off date), NM-match
status, aircraft-type missing in APDF. These let the model learn when the airport block time is likely an echo
of the schedule.
- (e) `reports/checks/p1_defect_near_echo.md`: at LIRF 18% of departures have |BLOCK − SCHED| ≤ 10 s; the
  >3 h tail is dominated by such near-echoes on long-delayed flights and by block dates stamped one day early.
- (d) a participant, 27/09/2026 (item 57); a participant, 28/09/2026 (item 63): echo of planned time, carrier-driven
  when there is no NM match.

## M-011 LightGBM regression on the raw target (L2)
Gradient-boosted trees, L2 objective on the raw target (seconds); no log transform, no target clipping.
- (c) richardalligier/prc (PRC 2024 winner): LightGBM ensembles *(cite commit in the paper)*.
- RMSE is minimised by the conditional mean, so L2 on the raw scale is the matching loss; hedging on ambiguous
  rows: (d) a participant, 27/09/2026 23:13 (item 62).

## M-012 METAR weather at the take-off (P4, source `iem_metar`)
Latest METAR at or before take-off (age-limited to 120 min, else missing + `wx_stale`) and 3 h aggregates
(min visibility/ceiling/temperature, max wind/gust, any snow/freezing/thunder). Present-weather flags from
IEM's parsed `wxcodes`, matched against WMO Manual on Codes (WMO-No. 306) code table 4678 abbreviations.
Hypotheses (each to be measured by ablation, CLAUDE.md §6):
- de-icing in frozen/freezing precipitation and sub-zero temperatures lengthens the off-block→take-off time where
  de-icing is done after push-back: ICAO Doc 9640, *Manual of Aircraft Ground De-icing/Anti-icing Operations*,
  3rd edition (section to be cited in the paper);
- low-visibility procedures reduce runway throughput: ICAO Doc 9365, *Manual of All-Weather Operations*,
  5th edition (2024);
- (d) a participant, 24/09/2026 (item 34) uses weather (rank 3); a participant, 28/09/2026 (item 63): METAR barely moved
  results at airports without ADS-B coverage.
- Data card: `docs/data_sources/iem_metar.md`.

## M-013 Neural tabular model: MLP with categorical entity embeddings
Same design matrix as the GBM (numeric + OOF target encodings + categoricals). Numeric inputs quantile-normalised
(fit on training rows) with missing indicators; one embedding table per categorical (rare categories pooled);
3 hidden layers with batch-norm, ReLU, dropout; AdamW + one-cycle LR; MSE loss on the raw target / 1000.
- (b) Guo & Berkhahn, "Entity Embeddings of Categorical Variables", arXiv:1604.06737, 2016 (checked 2026-10-03,
  https://arxiv.org/abs/1604.06737).
- (b) Gorishniy, Rubachev, Khrulkov & Babenko, "Revisiting Deep Learning Models for Tabular Data", NeurIPS 2021
  (MLP/ResNet baselines; Appendix B.2 "By default, we used the quantile transformation from the Scikit-learn library";
  checked 2026-10-03, arXiv:2106.11959).
- Purpose: a second, structurally different model family for averaging (a participant, 27/09/2026, item 62).

## M-004b NM default-taxi detection features
Mode of round((MVT − AOBT_3)/60) per airport × runway × month = NM default taxi; distance of each flight from it.
- (e) `reports/checks/p1_x_minute_concentration.md`, `reports/checks/p3_nm_default_value.md`. The check refuted
  the naive reading: MVT − AOBT_3 is *more* accurate at the default minute (RMSE 320 s) than off it (400 s), so the
  feature is kept only if the ablation EXP-020 shows a gain.

## M-014 Calibrated hedge for schedule-echo rows
For flights that took off > 3 h after schedule, per (airport, NM-match) cell with ≥ 30 training rows and an echo
share p ≥ 0.2 (|y − d_sched| ≤ 120 s), replace the prediction by p·d_sched + (1−p)·mean(y | not echo). Cells and
p are estimated on training months only; the threshold rule was fixed before looking at validation results.
- (d) a participant, 27/09/2026 23:13 (item 62, points 1 and 3): keep defective rows and hedge; "nothing beat a
  calibrated hedge" for the no-NM lane.
- (e) `reports/checks/p1_tail_given_dsched_2025.md` (67.5% echo at LIRF-unmatched > 3 h late); EXP-021.
- (e) Diagnostic from the EXP-012 hold-outs: the global GBM transfers LIRF's echo pattern to other airports'
  unmatched late flights (e.g. EDDF-unmatched RMSE 1,348 s vs 297 s for a cell mean) → motivates EXP-022.

## M-015 Same-runway queue counts
Take-offs from the same runway between the flight's proxy off-block (NM AOBT_3; separately the schedule) and its
own take-off; arrivals on the same runway in the same interval (mixed-mode runways).
- (b) Idris et al. 2002 (DOI 10.2514/atcq.10.1.1): take-off queue size is the dominant factor.
- (b) Lee, Malik & Jung, "Taxi-Out Time Prediction for Departures at Charlotte Airport Using Machine Learning
  Techniques", AIAA ATIO 2016, DOI 10.2514/6.2016-3910: departures on the surface by runway.

## M-016 Unimpeded reference time: P10 per stand × runway (out-of-fold)
10th percentile of taxi-out per (airport, stand, runway) and coarser keys, leave-one-month-out like M-005.
- (a) EUROCONTROL, *Additional taxi-out time performance indicator document*, Ed. 01.00, 16 March 2023,
  https://ansperformance.eu/library/ATXOT_indicator_documentation_mar23.pdf — unimpeded reference = P10 per
  stand × runway group over a rolling 12 months.
- (b) Lee et al. 2016 (as M-015): P10 per gate-spot-runway as "unimpeded taxi time" feature.

## M-017 EUROCONTROL airport aggregates as context features
Monthly unimpeded reference and additional taxi-out per flight (airport × month), daily pre-departure delay per
departure and ATFM slot-adherence shares (airport × day), joined on the take-off's UTC month/date.
- (a) EUROCONTROL Additional taxi-out time indicator (2023) — definition of the monthly figures.
- (d) organizer 17/09/2026 (item 3) and 27/09/2026 (item 60): allowed, incl. Jan/Jul 2026 monthly figures.
- (e) `reports/checks/p4_ec_vs_target.md`: 2025 airport-month correlation 0.98 with our target mean; EHAM Jan-2026
  mean 982 s vs 803 s in Jan-2025 (level shift invisible to a model trained on 2025 only). Measured in EXP-024.

## M-018 ADS-B take-off matching and taxi-segment description (adsb.lol)
Segment each aircraft's airport points by ground/airborne state and gaps > 20 min; a take-off is an airborne
segment starting ≤ 1500 ft and climbing ≥ 300 ft, with its adjacent ground segment as the taxi. Departures are matched
one-to-one to take-offs at the same airport within ±180 s (callsign agreement preferred). From the taxi segment:
first ground observation, end of the longest stationary run ≥ 120 s (off-block estimate), points/gaps (coverage),
ground distance after the stand stop, stationary (hold) time. Missing coverage is an explicit state (`adsb_matched`).
- (d) a participant, 18/09/2026 (item 14): off-block recoverable from surface tracks where coverage is good;
  organizer, 19/09/2026 (item 18): allowed. a participant, 27/09/2026 (item 59): movement features transferred
  across years, "where heard" features did not → drift check before keeping.
- (b) Srivastava, "Improving departure taxi time predictions using ASDE-X surveillance data", 30th DASC, 2011,
  DOI 10.1109/DASC.2011.6096185 (surface surveillance → queue position, distance to runway).

## M-019 Cross-fitted non-negative blend
Members' hold-out predictions combined with non-negative least squares (no intercept). Weights fit on one hold-out
month are scored on the other (cross-fit); final weights fit on both.
- (b) Breiman, "Stacked Regressions", *Machine Learning* 24, 49–64, 1996 (non-negative stacking weights) — see
  `docs/references/literature_review_2026-10-02.md` §3.
- (d) a participant, 27/09/2026 (item 62): second tree family, simple average of predictions.

## M-020 Residual corrector on hold-out base predictions (tested, rejected in EXP-026)
Small LightGBM (15 leaves, 300 rounds) on r = y − base prediction with base prediction + defect/context inputs,
cross-fitted between the Jan and Jul hold-outs.
- (d) a participant, 28/09/2026 (item 63) and a participant, 27/09/2026 (item 59 point 4): corrector on OOF base predictions.
- (b) Wolpert, "Stacked generalization", *Neural Networks* 5(2), 1992; Breiman 1996 (literature review §3).
- (e) EXP-026: worse on both months (+8.9 Jan / +5.1 Jul) — residual patterns do not transfer between Jan and Jul.
  A 12-month OOF corrector (as described on forum) was not run (≈5 h CPU for per-airport base models).

## M-021 Off-block from the aircraft leaving its own stand (ADS-B + OSM stand position)
The departure's APDF stand code is matched to an OSM `parking_position` (normalised codes; sub-stand fallback), and
ADS-B ground points within 60 m of it are "at stand". Off-block estimate = first moving point (gs ≥ 1 kt) at the stand,
else the first at-stand observation (lower bound).
- (c/d) Idea from the push-back detector of the `traffic` library (X. Olive; MIT; `traffic.algorithms.ground.pushback`,
  read 2026-10-02): documented parking position + start of movement. Independent SQL implementation, no code copied.
- (e) `reports/checks/p4_adsb_stand_offblock_2025.md`: coverage 22.7% of matched 2025 departures (vs 14.0% for the
  seen-parked rule), 80.7% within 60 s of the target when seen stationary at the stand; poor at EGLL/LEMD.

## M-022 Residual to an NM-based proxy (baseline offset)
Trees learn y − b with b = take-off − AOBT_3, else − EOBT_1, else − schedule (≥ 0), passed as LightGBM `init_score`
and added back to predictions; a constant-leaf tree can then follow b beyond the training range (long delays, echoes).
- (a) LightGBM documentation: `init_score` in `lightgbm.Dataset` (installed 4.7.0 signature checked; `predict()`
  excludes the init score — verified in a toy run).
- General residual/offset modelling (generalised linear models with an offset term); motivated by a published PRC 2026
  write-up (Phoenix-Ops-LTD/prc2026-taxiout, METHOD.md, read 2026-10-02 — idea only, no code; user policy:
  general techniques only). Measured in EXP-034.

## M-023 Linear-leaf gradient boosting (LightGBM `linear_tree`)
Each leaf holds a ridge-regularised linear model of the numeric features on its path (`linear_lambda` = 1, fixed a priori).
- (a) LightGBM Parameters documentation, `linear_tree` (https://lightgbm.readthedocs.io/en/stable/Parameters.html).
- (b) Shi, Li & Li, "Gradient Boosting with Piece-Wise Linear Regression Trees", IJCAI 2019, pp. 3432–3438,
  DOI 10.24963/ijcai.2019/476 (checked 2026-10-03).
- (e) Toy check: with x outside the training range, constant leaves stay at 5.0 (truth 15), linear leaves reach 7.3–7.5.
- Motivated by a published PRC 2026 write-up (radekacar/joyous-rainbow README, read 2026-10-02 — idea only). EXP-033.

## M-024 Stand remoteness from arrival taxi-in
Median ARR taxi-in (0–3600 s) per (airport, stand) over 2025 + 2026 arrivals, joined to departures by stand.
- (e) `reports/checks/p5_arr_stand_taxi_in.md`: covers 100% of ranking departures, incl. all 1,178 EDDM departures at
  stands unseen in 2025 departures; correlation with taxi-out 0.0–0.46 by airport. Arrival labels are intact in the
  ranking set (CLAUDE.md §2), so this is current for 2026 and reads no departure label. Measured in EXP-035.
- (b) Lee, Malik & Jung 2016 (gate–runway distance as a predictor) — stand remoteness as a distance proxy.

## M-025 Record-precision markers
`mvt_sec0` = take-off time on a whole minute; `arr_mvt_sec0_share_60m` = share of minute-rounded arrival records at the
airport within ±60 min. Minute-rounded records mark manually recorded movements, where block-time defects concentrate.
- (e) `reports/checks/p6_rounding_mvt_vs_block.md`: P(block on a whole minute | take-off on a whole minute) ≈ 50% vs
  4.5% at five airports; RMS label +134 s (LFPG) / +159 s (LIRF) on rounded rows; `reports/checks/p6_error_budget_EXP-031.md`:
  minute-rounded-block rows are 6.4% of rows and 22% of hold-out squared error. Label-free. Measured in EXP-038.

## M-026 Three-regime mixture for very late NM-unmatched flights at echo-prone airports
At airports qualifying under M-014 (currently LIRF), NM-unmatched departures ≥ 6 h after schedule follow three label
regimes: schedule echo (y ≈ take-off − schedule), "day-minus" (real off-block written ~24 h early, y ≈ 86,400 + taxi,
only possible when take-off is on a later calendar day than the schedule) and normal. Prediction =
p_echo·d_sched + p_dm·mean(y|dm) + p_normal·mean(y|normal), with shares per (airport, band 6–14 h / ≥ 14 h, later-day)
estimated on training months only (cells < 5 rows fall back to the pooled band).
- (e) Found by the cleaning investigation (`docs/references/cleaning_investigation_2026-10-03.md`,
  `reports/checks/p6_lirf_unmatched_regimes_by_band.md`, `p6_dayshift_precursors.md`); EXP-039.
- (b) Mixture / regime models for corrupted labels: E[y|x] = Σ_k P(k|x) E[y|x,k]; Patrini et al., "Making deep neural
  networks robust to label noise: a loss correction approach", arXiv:1609.03683 (forward modelling of a known
  corruption process, classification analogue).
- Caveat: the 6 h and 14 h band edges were chosen after looking at all 2025 months (incl. the hold-outs); the shares
  are cross-fitted. Gain rests on 21 hold-out rows (17 improve).

## M-027 Separate models for NM-matched and unmatched departures at an echo-prone airport
At LIRF, one LightGBM per (airport, NM-match status) instead of one per airport.
- (e) Cleaning investigation: the single LIRF model transfers the unmatched schedule-echo hedge to matched flights
  (112 negative hold-out predictions; `reports/checks/p6_proxy_clip_rules.md`). Same logic as the per-airport split
  (EXP-022, M-014 diagnostic). Chosen instead of clipping to the NM proxy (user policy: general techniques only).
  Measured in EXP-040 (LIRF rows only, paired with EXP-025).

## M-028 Shrinking predictions toward the ADS-B stand off-block estimate
Post-processing of the final blend for departures seen stationary at their own stand (M-021). est' = est + per-airport
median(y − est) (pooled when < 30 rows); where |est' − pred| ≤ 600 s, pred' = pred + w·(est' − pred) with one
least-squares weight per gap bin (≤ 60, 60–180, 180–600 s), clipped to [0, 1]. Offsets and weights are fit on the
hold-out predictions of the other 2025 month (cross-fit); final values on both months.
- (b) Stacked regression / non-negative combination of predictors: Breiman, "Stacked Regressions", *Machine Learning*
  24, 49–64, 1996 (as M-019); here a two-member combination whose weight depends on the members' agreement.
- (e) `reports/checks/p4_adsblol_vs_v4_holdout.md`: on rows seen stationary at the stand with |est − pred| ≤ 600 s the
  raw estimate has RMSE 101 vs 155 for the v4 hold-out prediction; beyond 600 s the estimate is far off (median abs
  error 3.4 ks — another stop, e.g. the arrival). Gate and bins were fixed from that table before fitting.
  `reports/checks/p4_adsblol_stand_by_airport.md`: per-airport bias stable Jan vs Jul (EGLL ≈ −140 s, LEMD/LIRF ≈ −90 s,
  others −30…+13 s) → per-airport offset. "Last stationary point" variant rejected
  (`reports/checks/p4_adsblol_stand_last_vs_v4.md`: it misses the push-back). Measured in EXP-042 (10 days) and EXP-050
  (all 124 days: −2.0 on both hold-out months; `reports/checks/p4_adsblol_vs_EXP-045_holdout.md`,
  `p4_adsblol_stand_by_airport_EXP-045.md`). Second source not added: flights only "seen parked" (M-018, no OSM
  stand match) have a raw estimate no better than the model even when they agree within 180 s (RMSE 115.5 vs 115.3,
  137.1 vs 133.4; same check). Second source added (EXP-051): aircraft seen within 60 m of its stand but never
  stationary there → first sighting at the stand (M-021 fallback), own per-airport offsets and weights; median abs error
  31 s vs 83 s for the model (`p4_adsblol_moving_at_stand_EXP-045.md`); −1.4 / −1.3 on the hold-outs. Third source not
  added: first ground observation for aircraft never seen at their stand is first seen mid-taxi (median −401 s vs the
  target; worse than the model in every gap bin, `p4_adsblol_first_ground_EXP-051.md`).
- Caveat: the 2025 fit rows are only the extracted Jan/Jul 2025 days; 2026 coverage differs by airport
  (`reports/checks/p4_adsblol_coverage.md`: EGLL Jul-2026 ≈ 43% of departures vs 0.4% Jul-2025; LIRF Jul-2026 none).

## M-029 Level calibration to the EUROCONTROL monthly mean taxi-out (tested, rejected in EXP-052)
Per airport, the 2025 gap between our target mean (y ≤ 2 h) and the EC monthly mean is modelled as c + s·snow share;
a target airport-month's level = EC + gap; normal predictions are shifted toward it with a cross-fitted shrink.
- (a) EUROCONTROL Additional taxi-out time indicator (2023), as M-016/M-017; EC monthly figures in `feat_dep_ec`.
- (d) a participant, 27/09/2026 15:49 (forum export item 58): may the published Jan/Jul-2026 monthly taxi-out figures be
  used as a model input? organizer, 27/09/2026 18:14 (item 60): "I already answered above: yes".
- (e) 2025 gap analysis (this session, query in the EXP-052 code): gap grows with snow at EDDF, EDDM, LFPG, LSZH, LTFM
  (corr 0.88–0.98: EC excludes de-icing there), flat at EGLL, EHAM, LEBL, LEMD, LIRF. EXP-052: no gain on the
  hold-outs (+0.16 / −0.05), unstable shrink → rejected. Code kept (`prc.models.level_calib`) for the record.

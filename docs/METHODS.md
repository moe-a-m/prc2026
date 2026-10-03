# Methods and provenance

Every modelling or cleaning method used in the pipeline, with its provenance (CLAUDE.md §1.3):
(a) official documentation, (b) peer-reviewed paper, (c) past PRC repo, (d) dated forum statement
(local, uncommitted export `docs/references/forum_discussion.md` of `#prc-data-competition`; cited by
author and date, item numbers refer to that export), (e) experiment in this repo.
Literature citations marked *(verify)* were written from memory and must be checked against the paper before
the JOAS write-up. Verified bibliography with URLs: `docs/references/literature_review_2026-10-02.md`.

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
- (b) Guo & Berkhahn, "Entity Embeddings of Categorical Variables", arXiv:1604.06737, 2016 *(verify)*.
- (b) Gorishniy, Rubachev, Khrulkov & Babenko, "Revisiting Deep Learning Models for Tabular Data", NeurIPS 2021
  (MLP/ResNet baselines; quantile-normalised inputs) *(verify)*.
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
- (b) Shi, Li & Li, "Gradient Boosting with Piece-Wise Linear Regression Trees", IJCAI 2019 *(verify)*.
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

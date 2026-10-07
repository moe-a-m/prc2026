# Methods and provenance

Every modelling or cleaning method used in the pipeline, with its provenance (CLAUDE.md §1.3):
(a) official documentation, (b) peer-reviewed paper, (c) past PRC repo, (d) dated forum statement
(local, uncommitted export `docs/references/forum_discussion.md` of `#prc-data-competition`; cited by
author and date, item numbers refer to that export), (e) experiment in this repo.
Literature citations marked *(verify)* were written from memory and must be checked against the paper before
the JOAS write-up. Verified bibliography with URLs: `docs/references/literature_review_2026-10-02.md`.

## Final model at a glance (submission v11 = EXP-118, board 268.25)
Task framing: at ranking time the take-off is known, so predicting taxi-out = estimating the airport-recorded
off-block (AOBT). Errors are dominated by label defects (schedule echoes, day-shifted dates) on a small share of
rows; RMSE rewards the conditional mean, so ambiguous rows are hedged, never dropped (M-002). Three layers: (1) a
per-airport GBM ensemble, (2) defect-aware hedging, (3) post-processing with independent evidence on the off-block
(ADS-B surface tracks, and the NM-association bound to LOBT).

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
| 8 | determinism fix + 5 seeds | tie-inclusive queue counts (identical features on every rebuild), 5 seeds per family (EXP-060–069) | 335.9 / 326.7 (EXP-079) |
| 9 | M-028 third source | aircraft within 150 m of its stand but never within 60 m | 335.5 / 326.3 (EXP-080) |
| 10 | M-030 | training labels > 3 h winsorized at all airports except LIRF (robust fit; LIRF keeps its implicit tail hedge) | 335.4 / 325.4 (EXP-100) |
| 11 | M-031 | projection of each prediction onto take-off − LOBT ± 3,606 s (the NM-association bound; 0 of 2,062,577 matched 2025 departures outside) | 334.5 / 301.0 (EXP-101) |
| 12 | M-033 | recent departures' NM taxi-out proxy (previous 30 min / last 5, airport and runway) as inputs → final model | 334.2 / 300.8 (EXP-118) |

Board history (`docs/SUBMISSIONS.md`): v1 347.2 (stage 2) → v2 319.9 (4) → v3 299.1 (5, 1-seed CatBoost) →
v4 287.5 (6) → v5 283.2 (7) → v6 279.8 (7b) → v7 279.4 (8) → v8 278.5 (9) → v9 276.8 (10) → v10 269.2 (11) →
v11 268.3 (12). The board moved in the direction of the local hold-outs every time; no choice was made on board
scores.

Robustness (§ M-026, M-028, M-031): hedge exposure is one-sided (≈ +12.8 board RMSE if 2026 echo shares sat at the
lower 95% bound, `reports/checks/m026_stability.md`); the ADS-B step varies smoothly with radius and gate and its
gap distributions transfer 2025 → 2026 (`reports/checks/m028_sensitivity.md`); the LOBT bound holds on every 2025
row and is enforced as a data contract (`sql/90_checks/08_lobt_window.sql`). Reproducibility: clean-clone rebuilds
of v7 (byte-identical) and v10 (344,840 / 344,841 identical, one row ±1 s), README § Reproducibility.

Tried and rejected (each with its experiment row in `docs/EXPERIMENTS.md`): `MVT − AOBT_3` as the answer (EXP-009),
MLP with entity embeddings alone or blended (EXP-019, EXP-027), residual corrector (EXP-026), same-runway queue +
P10 unimpeded reference (EXP-023), EUROCONTROL airport aggregates as inputs (EXP-024), NM default-taxi features
(EXP-020), linear-leaf trees (EXP-033), NM-proxy offset (EXP-034), stand remoteness (EXP-035), record-precision
markers (EXP-038), split LIRF models (EXP-040), CatBoost lr 0.05 (gain vanished in the blend, EXP-047), EUROCONTROL
monthly level calibration (EXP-052), robust labels at LIRF (EXP-081–085), LIRF-unmatched echo classifier hedge
(M-032, EXP-102), ADS-B off-block estimates as model inputs (M-034, EXP-119–134: better base models, but the same
information as the M-028 post-step).
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

- Robustness (`reports/checks/m026_stability.md`): 2025 shares (95% Wilson) — band 6–14 h echo 42/43 = 0.977
  [0.879, 0.996]; band ≥ 14 h echo 9/20 = 0.45 [0.26, 0.66], day-minus 0.55; no month contradicts the pattern. The
  exposure is one-sided: with both bands at the lower interval end the 26 hedged ranking rows would add ≈ +12.8 to the
  board RMSE (upper end −0.6). The −11.6 board gain when M-026 was introduced (v4) is evidence that 2026 echo shares
  are high.

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
  Third source added (EXP-080, `near`): aircraft never within 60 m of its stand but within 150 m — 10% of departures
  with a ground segment (`reports/checks/p4_adsblol_stand_gap.md`; 5% have no OSM stand position, 44% are first heard
  > 150 m away); estimate = first movement within 150 m if stationary there, else first sighting within 150 m
  (sql/40_adsb/05). Own offsets/weights; changed rows improve at every airport-month; −0.44 / −0.44 on the hold-outs.
- Caveat: the 2025 fit rows are only the extracted Jan/Jul 2025 days; 2026 coverage differs by airport
  (`reports/checks/p4_adsblol_coverage.md`: EGLL Jul-2026 ≈ 43% of departures vs 0.4% Jul-2025; LIRF Jul-2026 none).

- Robustness (`reports/checks/m028_sensitivity.md`, Modal run m028-sens): hold-out RMSE moves smoothly with the
  near radius (100 / 150 / 200 m: 335.60 / 335.46 / 335.28 Jan; 326.43 / 326.29 / 326.19 Jul) and the gate (300 / 600
  / 900 s: 336.95 / 335.46 / 334.79 Jan) — the chosen values are not a knife-edge optimum; they were fixed before this
  scan and kept (no selection on it). Transfer to 2026 without labels: per source and airport the gap
  (est + offset − base prediction) has similar medians and p10/p90 in 2025 hold-outs and 2026 ranking rows, incl.
  EGLL whose coverage rises from ~2% to ~27% of departures. Weakest transfer: LEMD offsets come from 47–78 rows in
  2025 but apply to ~9,850 ranking rows (27% of LEMD 2026 departures).

## M-029 Level calibration to the EUROCONTROL monthly mean taxi-out (tested, rejected in EXP-052)
Per airport, the 2025 gap between our target mean (y ≤ 2 h) and the EC monthly mean is modelled as c + s·snow share;
a target airport-month's level = EC + gap; normal predictions are shifted toward it with a cross-fitted shrink.
- (a) EUROCONTROL Additional taxi-out time indicator (2023), as M-016/M-017; EC monthly figures in `feat_dep_ec`.
- (d) a participant, 27/09/2026 15:49 (forum export item 58): may the published Jan/Jul-2026 monthly taxi-out figures be
  used as a model input? organizer, 27/09/2026 18:14 (item 60): "I already answered above: yes".
- (e) 2025 gap analysis (this session, query in the EXP-052 code): gap grows with snow at EDDF, EDDM, LFPG, LSZH, LTFM
  (corr 0.88–0.98: EC excludes de-icing there), flat at EGLL, EHAM, LEBL, LEMD, LIRF. EXP-052: no gain on the
  hold-outs (+0.16 / −0.05), unstable shrink → rejected. Code kept (`prc.models.level_calib`) for the record.

## M-030 Robust training labels: fit without (or with capped) labels > 3 h (tested in EXP-081 / EXP-082)
The GBM fit (not the target encodings, not the scoring) uses labels ≤ 3 h only (`fit_y_mode: drop`) or labels
winsorized at 3 h (`clip`); config keys `fit_y_max`, `fit_y_mode` in `prc.models.gbm`. Defect rows are still predicted;
their hedge stays with M-026. Labels are never edited in the database (M-002).
- (b) Huber, "Robust Estimation of a Location Parameter", *Annals of Mathematical Statistics* 35(1), 73–101, 1964,
  doi:10.1214/aoms/1177703732 (verified on projecteuclid.org 2026-10-06)
  (bounding the influence of gross errors on a squared-loss fit).
- (e) `reports/checks/m030_label_tail.md`: 202 of 2,085,047 training departures have y > 3 h (188 at LIRF) and carry
  42% of the squared deviation from the per-airport median — a single such label shifts a 1,000-row leaf by ~80 s.
- Result (EXP-081–085): at LIRF the raw labels must stay — the GBM's implicit hedge of the echo/day-shift tail is
  worth more than the gain on normal LIRF rows, even with M-026 on top. Elsewhere (14 labels > 3 h) clipping helped on
  a single LightGBM seed: Jan −0.27, Jul −1.72 overall (`reports/checks/m030_paired_*.md`).

## M-031 Feasible-interval projection: off-block within ±3,606 s of the NM LOBT (EXP-101, kept)
For a departure with an NM last known off-block time (LOBT), the airport off-block lies within ±3,606 s of it, so the
taxi-out lies in [d_lobt − 3,606, d_lobt + 3,606] (d_lobt = take-off − LOBT). The final prediction is projected onto
this interval (and floored at 0). Rows without LOBT (1.5% of the ranking set) are unchanged.
- (e) Our data, `reports/checks/lobt_window_train.md`, `lobt_window_references.md`, `lobt_window_tails.md`
  (scripts/checks/lobt_window.py): 0 of 2,062,577 matched 2025 departures fall outside ±3,606 s, at every airport; the
  edge is exact (max 3,606 s at 7 of 10 airports; 249 rows in the last 6 s, none beyond). Only the **off-block** is
  bounded and only by **LOBT**: the take-off exceeds ±3,606 s of LOBT for 29,162 rows, and IOBT / EOBT_1 / schedule
  leak (58 / 614 / 107,499 rows). The bound is therefore a property of how airport records were associated with NM
  flights, not an operational regularity.
- (a) Mechanism: AOBT is one of the keys used to associate APDF flight records with NM data (EUROCONTROL
  Specification for Operational ANS Performance Monitoring — Airport Operator Data Flow, Ed. 1.0, 15 Jan 2019, §4,
  p. 27); LOBT is kept current by delay messages, which are mandatory once the departure slips beyond the filed EOBT
  (ICAO Doc 4444 PANS-ATM, 15th Ed. 2007, §4.4.2.1.3: amend or re-file after a 30-min delay for controlled flights;
  IFPS: any EOBT change > 15 min must be notified — EUROCONTROL EOBT/A-CDM service page, read 2026-10-06). The
  organizer's data page states only that movements were left-joined with NM flights (no tolerance published), so the
  ±3,606 s width is measured, not documented.
- (b) Guarantee: Euclidean projection onto a closed convex set returns its closest point (Boyd & Vandenberghe,
  *Convex Optimization*, 2004, §8.1, pp. 397–398; Ex. 8.4); for any target inside the set the projected prediction is
  never farther from it, row by row. Projection onto known constraints is an established forecast post-processing
  step with a guaranteed accuracy gain: Panagiotelis, Gamakumara, Athanasopoulos & Hyndman, "Forecast reconciliation:
  A geometric view with new insights on bias correction", *Int. J. Forecasting* 37(1), 343–359, 2021.
- Assumption: the same association rule holds for the 2026 ranking rows (same organizer pipeline); not checkable
  locally because 2026 departure labels are blank.
- Disclosure: a projection to this window also appears in a competitor's public repository (EnioAguiar/
  prc-taxiout-2026, GPL-3.0, commit 30e23de, `docs/research/2026-09-27-janela-lobt.md`), which prompted us to test it.
  No code or constants were taken from it; the bound, its mechanism and its evaluation above are our own.
- Result (EXP-101, `prc.models.lobt_window`): hold-out Jan 335.43 → 334.48, Jul 325.40 → 300.98; 53 / 170 rows
  changed, each airport-month's changed rows improve. Data contract `sql/90_checks/08_lobt_window.sql` enforces the bound
  on every rebuild; `tests/test_lobt_window.py` checks the never-farther property.

## M-032 Schedule-echo classifier hedge for LIRF NM-unmatched departures 1–6 h late (tested, rejected in EXP-102)
Month-held-out gradient-boosting classifier for p(echo) on label-free inputs; hedge p·d_sched + (1 − p)·mean normal y,
blended with the model by a cross-fitted least-squares weight (`prc.models.echo_clf`).
- (e) `docs/references/cleaning_investigation_2026-10-03.md` §2 (AUC 0.867, −2.2% SE averaged with EXP-031); two-point
  mixture as M-014 / M-026.
- Result: classifier separates well (AUC 0.866 / 0.810) but the current base already hedges these rows; the blend
  weight is not identifiable from 49 January rows (0.677 vs 0.033) and the July gain at a fixed weight sits in 10 rows
  where the base predicts above d_sched. Not used. Off-block before schedule is common (16% of matched 2025
  departures, 681 by > 1 h), so no feasible-set cap applies here (unlike M-031).


## M-033 Recent departures' NM taxi-out proxy (EXP-103–118, kept)
Per departure, over the departures at the same airport (and runway) that took off strictly earlier: mean of their
take-off − NM actual off-block (d_aobt3, 0–3 h) in the previous 30 min and over the last 5 departures, plus counts
(`sql/30_features/10_feat_dep_recent.sql`, table feat_dep_recent). Label-free — the ranking set's departure labels are
blank, so the NM proxy stands in for the recent taxi-out times the literature uses; coverage 99.6% in 2025 and 2026,
median 951 vs 976 s.
- (b) Recent taxi times of other flights as a predictor: "average taxi time of the previous half hour" (Balakrishna,
  Ganesan, Sherry & Levy, "Estimating taxi-out times with a reinforcement learning algorithm", 27th DASC, 2008) and
  "of the previous quarter" (Srivastava, "Improving departure taxi time predictions using ASDE-X surveillance data",
  30th DASC, 2011, doi:10.1109/DASC.2011.6096185), both as tabulated by Wang, Brownlee, Woodward, Weiszer, Mahfouf &
  Chen, "Aircraft taxi time prediction: Feature importance and their implications", *Transp. Res. C* 124, 102892,
  2021 (full text read 2026-10-07, Table 1), whose own features include the average speed of the last 5 / 10
  departures (AvgSpdLast5Dep, AvgSpdLast10Dep, §3.3) — hence our 30-min and last-5 windows.
- Disclosure: a competitor's repository (EnioAguiar/prc-taxiout-2026 @30e23de) reports a gain from neighbouring
  departures' MVT − AOBT_3; our features were defined from the literature above and our own parity constraint.
- Result: single seed (EXP-103/104) non-LIRF y≤3h better in both families; full recipe EXP-118 vs v10 (EXP-101)
  Jan 334.48 → 334.18, Jul 300.98 → 300.76, non-LIRF y≤3h 189.67 → 188.94 / 222.31 → 220.79.

## M-034 ADS-B off-block observations as model inputs (tested, not adopted: EXP-119–134)
Give the GBMs the ADS-B off-block estimates directly (first movement when seen parked, `adsb_first_move_s`; first
movement / first sighting at the own stand, `adsb_stand_move_s`, `adsb_stand_first_s`; near-stand estimate,
`adsb_near_s`) plus their difference to the NM proxy (estimate − d_aobt3), so the model learns when to trust ADS-B over
NM instead of the hand-set 600 s gate of M-028. Reception-dependent features (first ground observation, number of
points, largest gap, taxi distance) are excluded. Missing ADS-B stays missing (native missing-value handling).
- (e) `reports/checks/m034_adsb_vs_nm.md` (Modal run m034-evidence): on 2025 matched departures with a ground
  segment, where NM's AOBT_3 is > 15 min from the airport off-block (the band carrying 19% of v11 hold-out squared
  error) the NM proxy's median error is 1,259 s, the ADS-B first-movement estimate's 45 s (closer in 90% of rows) and
  the stand estimate's 32 s (closer in 95%); 5–15 min band: 416 s vs 39 s / 31 s. The M-028 gate (600 s) excludes most
  of these rows by design.
- (e) Drift, `reports/checks/m034_adsb_feature_drift.md`: movement estimates are stable 2025 → 2026 where 2025 coverage
  is substantial (median first movement when parked: EDDF 615 / 608 s, EDDM 715 / 744, EHAM 779 / 835, LEBL 773 / 829);
  reception features shift (points per track EDDF 30 → 11, LIRF 36 → 14) and are therefore excluded — consistent with
  the forum observation that "how it moved" transfers and "where it was heard" does not (a participant, 27/09/2026).
  Caveat: the adsb.lol archive covers only Jan/Jul days, so ADS-B inputs exist on ~1/6 of 2025 training rows; a
  hold-out month's model learns them from the other extracted month only (pessimistic validation).
- (b) Surveillance-derived inputs for taxi-time prediction: Srivastava, 30th DASC 2011, doi:10.1109/DASC.2011.6096185
  (ASDE-X); Wang et al., *Transp. Res. C* 124, 102892, 2021 (surveillance-derived speed features); Hänggi, Waltert &
  Wilde, "Prediction of Arrival Runway Occupancy Time and Exit Taxiway Using ADS-B Trajectories", *J. Open Aviation
  Science* 4(2), 2026, doi:10.59490/joas.2026.8465 (OpenSky ADS-B trajectories as ML inputs, Zurich). Open ADS-B for
  surface operations: Olive, Waltert & Schultz, "Assessing airport surface traffic performance from open sources of
  aviation data", ATRD Symposium 2025; push-back detection from a parking position and the start of movement: Olive,
  "traffic, a toolbox for processing and analysing air traffic data", *JOSS* 4(39), 1518, 2019,
  doi:10.21105/joss.01518 (as M-021).
- (b) Missing values in tree models: Josse, Chen, Prost, Scornet & Varoquaux, "On the consistency of supervised
  learning with missing values", *Statistical Papers* 65, 2024 (arXiv:1902.06931) — missing-incorporated-in-attributes
  handles informative missingness, which is what LightGBM / CatBoost do natively.
- (b) Drift check before keeping it: adversarial validation (Pan, Pham, Dorairaj, Chen & Lee, AdKDD 2020,
  arXiv:2004.03045).
- Disclosure: a competitor (EnioAguiar/prc-taxiout-2026 @30e23de) reports a gain from own-flight ADS-B events as model
  inputs; our features, their selection and the evidence above are our own.
- Result: the inputs improve every base model (LightGBM seeds −2.4…−3.1 Jan / −1.4…−2.6 Jul; non-LIRF y≤3h −4.6 / −3.9
  at seed 42; EHAM −17 / −18) and the blend before the ADS-B post-step (EXP-132 vs v11's EXP-116: −2.55 / −1.92), but
  they capture the same information as the M-028 post-step, whose gain falls from −3.87 / −3.68 to −1.78 / −1.36. Final
  recipe EXP-134 vs v11: −0.40 / +0.56 — not adopted (both-months rule); blending both pipelines −0.14 / −0.02. The
  M-028 post-step is thus an efficient way to use the ADS-B off-block evidence (no retraining, cross-fitted gate).

# Cleaning / data-prep investigation (P6)

Baseline: EXP-031 Jan+Jul 2025 hold-out predictions (`models/oof/EXP-031_{jan,jul}.parquet`, 344,419 rows,
combined RMSE 355.54 s — `p6_proxy_clip_rules`). All numbers below come from `reports/checks/p6_*` (SQL + output
saved). "% SE" = share of the total EXP-031 Jan+Jul hold-out squared error. Hold-out RMSEs are before the
submission clip at [0, 2 d].

Caveat for every "post-hoc rule" number: these are exploratory evaluations on the existing hold-out predictions,
not logged experiments. The band edges (3 h / 6 h / 14 h) were picked after looking at all 2025 months, incl. the
hold-outs; regime probabilities and means were estimated on the other 11 months. Each recommendation must be
re-run as an EXP with the edges fixed beforehand.

## 1. LIRF NM-unmatched departures

Checks: `p6_lirf_dsched_by_month`, `p6_flightnum_pattern_by_match`, `p6_lirf_unmatched_echo_by_dsched`,
`p6_lirf_unmatched_gt6h_rows`, `p6_lirf_unmatched_block_minus_sched`, `p6_lirf_unmatched_early_block`,
`p6_lirf_unmatched_tz_echo`, `p6_lirf_unmatched_regimes_by_band`, `p6_lirf_regime_hedge_eval`,
`p6_lirf_unmatched_echo_by_marker`, `p6_lirf_echo_classifier_auc`.

- Size: 1,487 rows in 2025 (52–337 per month), 383 in the 2026 ranking set (107 Jan, 276 Jul). Every one has
  `actype_mvt` missing (100%), so a missing aircraft type is equivalent to unmatched at LIRF and adds no information.
- They are late. Median MVT − SCHED is 6,000–6,900 s in every month for unmatched rows, against 1,100–2,000 s for
  matched rows. The median does not move with DST, and only 6 of 64 early-block rows sit at BLOCK = SCHED − Rome UTC
  offset. That rules out a local-time schedule.
- Mangled flight numbers (ICAO prefix followed by a repeat of its last 1–2 letters, e.g. NOSOS739, ITYTY672,
  WZZZ8068) are a LIRF recording convention, not an unmatched marker. LIRF has 2,742 matched and 164 unmatched
  mangled rows in 2025 (426 / 40 in the ranking set). Elsewhere they are almost absent: 14 matched and 3 unmatched.
- There are three label regimes, defined by BLOCK − SCHED (`p6_lirf_unmatched_block_minus_sched`):
  echo |B−S| ≤ 2 min, 722 rows; day-minus B−S ≈ −1 day, 15 rows; normal, the rest.
  Regime shares by lateness band (`p6_lirf_unmatched_regimes_by_band`):

  | band | n 2025 | echo | day-minus | normal | hold-out rows | % SE now |
  |---|---|---|---|---|---|---|
  | < 3 h | 1,244 | 44.9% | 0 | 55.1% | 314 | 4.30 |
  | 3–6 h | 180 | 62.8% | 0.6% | 36.7% | 62 | 6.31 |
  | 6–14 h | 43 | 97.7% | 0 | 2.3% | 14 | 4.91 |
  | ≥ 14 h | 20 | 45% | 55% | 0 | 7 | 8.52 |

  Day-minus rows have y = 86,400 + 1,136 s on average, i.e. the actual off-block written 24 h early.
- **6–14 h and ≥ 14 h bands.** EXP-031 under-predicts both regimes, e.g. y 87 k against a prediction of 53–63 k
  when the echo value would be 58–60 k; the trees cannot extrapolate there. A three-regime hedge,
  p_echo·d_sched + p_dm·mean(y|dm) + p_n·mean(y|normal) with p estimated on the other months, cuts these bands from
  **13.4% → 2.0% SE**: Jan 3.00 → 1.01, Jul 10.43 → 0.99 (`p6_lirf_regime_hedge_eval`). This rests on 21
  hold-out rows. In the 3–6 h band the same hedge is no better (6.32 → 6.68).
- **1–6 h band: a label-free regime classifier works.** Echo share by carrier: ISR 100%, AEZ 84%, NOS 77%,
  WZZ 73%, WMT 48%, RYR 33%, EJU 10%, ITY 3.9%. Mangled numbers are 77% echo, null flight numbers 84%,
  winter 70% vs summer 42%. A leave-one-month-out HistGradientBoosting classifier (d_sched, hour, schedule minute,
  MVT second = 0, carrier, flight-number class, stand) reaches **AUC 0.867**, against 0.661 for d_sched alone.
  Brier score is 0.149 against 0.249 for a constant rate. Using its p_echo as a hedge on hold-out rows that took
  off 1–6 h late gives Jul 9.66 → 7.67% SE and Jan 0.59 → 0.61. Averaging the hedge with EXP-031 gives
  Jul 7.54 and Jan 0.54, about **−2.2% SE**.
- Stability: the echo share of LIRF-unmatched rows (|BLOCK−SCHED| ≤ 60 s) swings by month, from 32% (Jul) to
  76% (Feb, Dec) (`p6_lirf_dsched_by_month`). The swing is seasonal: winter 70% vs summer 42% in the 1–6 h band,
  so season or month must be an input, or the hedge must be estimated per season. 2026 ranking: 383 rows. Their
  carrier and band mix is in `p6_lirf_unmatched_echo_by_marker` (n_rank2026 column): e.g. RYR 60, WMT 50,
  ITY 29, ISR 4. The d_sched band mix is close to 2025's.

## 3. Day-shifted labels (y > 20 h)

Checks: `p6_dayshift_rows_all`, `p6_dayshift_precursors`.

- 2025 has 16 such rows: 13 LIRF-unmatched, 1 LIRF-matched, 1 LFPG-unmatched, 1 LSZH-unmatched. Seven are in the
  hold-outs and carry 28.6% SE.
- **There is a precursor, but only at LIRF:** NM-unmatched and ≥ 14 h after schedule. That cell holds 20 rows, 12
  of them y > 20 h; with SCHED and MVT on different calendar days it is 11 of 17 (64.7%). In every other cell the
  rate is 0 to 0.01%. Not one day-shifted row has its schedule within 22–02 UTC, so "schedule near midnight" is
  not a precursor. The 2026 ranking set has 6 rows in the LIRF-unmatched ≥ 14 h cell.
- The LFPG row (EJU983W, 0.48 h late, y 23.4 h) and the LSZH row (NJE389D, 0.26 h late) have no precursor. Their
  cell is non-LIRF, unmatched, < 3 h late, same day: 2 of 19,771 rows. The LFPG row alone is ≈ 16% of hold-out SE,
  `p6_top_rows_holdout_EXP-031` gives 15.95%; the second LFPG row, EJU42AY, adds 7.53%. **Nothing label-free
  predicts them.** Leave it unmodelled; hedging it would cost
  more on the other 19,769 rows.
- The one LIRF-matched day-shift row (AEZ146R) is an echo of a 24.2 h delay that AOBT_3 also shows: MVT − AOBT_3
  = 1,453 min against y = 1,450 min. EXP-031 predicted 742 min. See item 2.

## 2. Matched departures where the NM proxy is off, and the model departing from a good proxy

Checks: `p6_proxy_off_markers`, `p6_pred_vs_proxy_disagreement`, `p6_pred_proxy_gt1h_nonsuspect`,
`p6_proxy_clip_rules`, `p6_late6h_regimes_by_airport`, `p6_lirf_matched_late6h_rows`, `p6_lirf_matched_mangled`,
`p6_mangled_demangle_vs_callsign`, `p6_matched_block_eq_sched_by_airport`, `p6_lirf_matched_echo_by_nmdelay`,
`p6_lirf_matched_echo_classifier`, `p6_lirf_matched_late_echo_by_mvtsec0`.

- **A label-free "proxy suspect" marker exists.** The base rate of "proxy off by > 1 h" is 0.087%. It rises to:
  - 29.3% when |AOBT_3 − EOBT_1| > 1 h (3,197 rows);
  - 30.7% when AOBT_3 is after take-off (1,012 rows);
  - 27.8% when AOBT_3 is > 1 h before SCHED (1,200 rows);
  - 57.9% when MVT − AOBT_3 > 2 h (19 rows).
- **No sign of a wrong NM join.** An ADES mvt ≠ flt mismatch has a 0.15% proxy-off rate (29,160 rows) and an
  aircraft-type mismatch 2.45%. The callsign agrees with the de-mangled flight number in 3,166 of 3,168 LIRF
  mangled matched rows.
- The proxy-off population itself is small: 3.5% SE (known). The larger problem runs the other way: **the model
  departs from a good proxy.**
  - On matched, non-suspect rows where the prediction is > 60 min from MVT − AOBT_3, 117 hold-out rows carry
    7.61% SE. The raw proxy would carry 4.15% (`p6_pred_vs_proxy_disagreement`).
  - Almost all of this is LIRF-matched flights > 3 h late: 29 rows, 7.0% SE now against 0.44% with the proxy
    (`p6_pred_proxy_gt1h_nonsuspect`).
  - The per-airport LIRF model carries the unmatched echo hedge over to matched late flights (e.g. NOSS95ML:
    prediction 327 min, NM proxy 18 min, y 15 min). It also produces negative predictions: 112 hold-out rows below
    0 (`p6_proxy_clip_rules`).
  - Matched LIRF flights ≥ 6 h late have 1.2% echo and the proxy is within 5 min for 64% of them
    (`p6_late6h_regimes_by_airport`).
  - Mangled-number LIRF matched flights are 10× more often > 3 h late (4.96% vs 0.50%). On them EXP-031 has RMSE
    1,205 s against 589 s for the raw proxy (`p6_lirf_matched_mangled`).
- **Rule R3:** for a matched, non-suspect proxy and d_sched > 3 h, clip the prediction to MVT − AOBT_3 ± 30 min.
  Hold-out RMSE goes Jan 347.72 → 347.66 and **Jul 361.72 → 339.76**, with 48 predictions changed. The gain is
  concentrated: in Jul 80% comes from 5 rows, one of them AEZ146R (4.15% SE). Clipping every non-suspect row
  to ± 30 min is worse (347.18 combined, 1,046 rows changed). Restricting to LIRF gives 343.51 vs 343.31 for all
  airports.
- **A second LIRF defect, not in the known list: schedule echo on matched rows.** LIRF matched departures have
  BLOCK within 60 s of SCHED in 20.5% of rows, against 9.4% with AOBT_3 within 60 s of SCHED. At the other
  airports the BLOCK share is no higher than the AOBT_3 share, or only slightly so (`p6_matched_block_eq_sched_by_airport`).
  These rows carry **7.96% SE** at RMSE 837 s, vs 434 s for the other LIRF matched rows.
  - Echo share by NM delay (AOBT_3 − SCHED): 15.7% when early, 42.9% on time, 31.2% at 2–10 min, 11.2% at
    10–30 min, 7.0% at 30–60 min, 4.5% at 1–3 h, 0% above 3 h (`p6_lirf_matched_echo_by_nmdelay`).
  - A leave-one-month-out classifier on label-free inputs separates echo rows among flights with NM delay
    > 10 min at AUC 0.839. A minute-rounded MVT does not separate them: 9.3% vs 9.2%.
  - The hedge alone is worse than EXP-031. Averaged with EXP-031 it is mixed: Jul 10.28 → 8.88% SE, Jan
    1.58 → 1.66% (`p6_lirf_matched_echo_classifier`). The GBM already uses these inputs, so this stays low priority.

## 4. Regular-row noise and timestamp conventions

Checks: `p6_aobt3_offset_by_airport`, `p6_aobt3_offset_by_airport_month`, `p6_minute_step_sources`,
`p6_holdout_bias_vs_minute_step`.

- AOBT_3 is on a whole minute in 99–100% of matched rows at 9 airports and 83.9% at EHAM. MVT and BLOCK seconds
  come in two conventions: about 8.3% on second 0 at EDDM, EGLL, LFPG, LIRF and LTFM, about 1.7% elsewhere.
  BLOCK at LEBL and LEMD is 8.3% while their MVT is about 1.7%.
- Median (MVT − AOBT_3) − y on regular rows, per airport: LTFM +241, EHAM +97, EDDF +91, EGLL +6, EDDM +1,
  LEMD +3, LFPG −4, LEBL −5, LSZH −27, LIRF −60 s. A constant per-airport shift is absorbed by per-airport trees
  with the nm_proxy offset (M-022), so **de-biasing the input timestamps cannot help the GBM**.
- **Whole-minute monthly steps.** The monthly median proxy error jumps by about 55–60 s between months, e.g.:
  - EGLL: 57, 5, 55, 4, 5, 4, 54, 5, 5, 5, 54, 55;
  - LIRF: about −5 in Jan–Feb and Nov–Dec, −58 to −66 in Mar–Oct (−115 in Jun);
  - EDDM: +57 in Jan–Mar, then about 0;
  - LEBL: −56 in May–Jul;
  - LFPG: −56 in Jul only.

  Partly this is NM's default taxi time changing: the median MVT − AOBT_3 at LTFM moves between 1,200 and
  1,440 s, at EGLL between 1,317 and 1,378 s, at LFPG between 844 and 961 s. It continues in 2026 (LTFM Jan-2026
  1,444, Jul-2026 1,197). Partly it is airport-side: at EDDM MVT − AOBT_3 stays at about 720 s, but y and ARR
  taxi-in both rise about 45 s from April. Nothing label-free tracks the step at every airport: ARR taxi-in co-moves
  at EDDM only.
- Implication: the 2026 months may sit in either minute regime. The model has `month_of_year`, so in production
  Jan/Jul-2026 inherit the Jan/Jul-2025 regime. Leave-one-month-out validation never sees the held-out month and
  **cannot measure this risk**. Size: a 55 s bias on regular rows (RMSE about 200–230 s) costs about 7–9 s RMSE at
  the affected airport. Earlier, `p4_ec_level_bias_holdout` measured hold-out bias of −21…+36 s.
- Minute truncation noise in AOBT_3 (uniform ±30 s) is below the label's own spread: IQR of the proxy error
  is about 240–360 s. Nothing to gain from denoising.

## 5. Drift 2025 → 2026 of label-free defect markers

Check: `p6_defect_marker_drift`, plus ranking counts in `p6_dayshift_precursors`, `p6_lirf_dsched_by_month`,
`p6_nonlirf_unmatched_late_holdout`, `p6_lfpg_runway_by_month`.

- **EHAM Jan-2026 is an outlier month.** Unmatched 4.96% vs 1.59% in Jan-2025; > 3 h late 4.81% vs 1.15%;
  unmatched and > 3 h late 1.713% vs 0.130% (about 278 rows). Jan-2026 also runs above Jan-2025 in > 3 h late
  share at LFPG (2.11% vs 0.83%), LSZH (0.89 vs 0.37), EDDM (0.65 vs 0.28) and LIRF (1.00 vs 0.43).
  Non-LIRF unmatched flights ≥ 3 h late in the ranking set: 593 rows (297 EHAM), against 1,105 in all of 2025.
  In 2025 these rows show no echo (0%). EXP-031 is calibrated on them: hold-out mean prediction 1,236 vs mean y
  1,216, RMSE 701, 0.34% SE. **Expected impact is modest.** Verify that 2026 d_sched values stay inside the
  2025 training range of this cell.
- LIRF unmatched: 0.97% (Jan) and 1.74% (Jul) in 2026, against 0.53% and 2.22% in 2025. The ranking set has 68
  LIRF-unmatched rows 3–14 h late and 6 at ≥ 14 h, so R1 still matters there, and so does the matched-echo
  pattern.
- MVT on second 0, aircraft type missing, AOBT_3 missing (= unmatched share) and mangled share are all stable.
  The share of null flight numbers at LIRF grows: 0.08 / 0.10% in 2025, 0.145 / 0.265% in 2026.
- **LFPG runway use changes.** In Aug–Nov 2025 runways 09R/27L were almost unused (≤ 10 departures a month) and
  27R/09L took over. Jan and Jul 2026 use 09R/27L normally (27L 5,354 / 4,444), with 27R/09L at ≤ 16. Jul-2025 is a
  transition month (27R 3,495), so it is a weak proxy for Jul-2026 at LFPG. Stand × runway encodings for 27R/09L
  matter little in 2026.

## 6. Categorical hygiene

Checks: `p6_runway_values`, `p6_stand_normalisation`, `p6_actype_hygiene`, `p6_actype_mismatch_pairs`,
`p6_flightnum_pattern_by_match`, `p6_mangled_demangle_vs_callsign`, `p6_flt_prefix_coverage`.

- Runways are clean. The only non-runway codes are EHAM 'HEL' (29 train / 11 rank) and LSZH 'H' (387 / 79),
  helicopter departures that could get a flag. Nulls: 3 at EGLL, 1 EHAM, 24 LIRF, 2 LFPG (rank).
- Stands: upper/trim/strip-leading-zeros merges **no codes** at any airport. LEBL has '01'–'04' (325 rows) but no
  '1'–'4' to collide with. There are no placeholder codes ('NA', 'UNK', '0'); nulls are EGLL 6, LFPG 16, LIRF 10.
  **No stand normalisation needed.**
- Aircraft types: every non-null `actype_mvt` matches the ICAO pattern; there are 1,507 train / 388 rank nulls,
  all LIRF-unmatched. Mismatches against NM are mostly variant pairs (B772/B77L 2,858; AT72/AT76 1,665;
  E75S/E170 643; A320/A20N 175). Merging is optional; their error share is small (H: 0.3% SE).
- Flight numbers:
  - `flt_prefix = regexp_extract(flight_mvt, '^[A-Z]{3}')` is **empty for IATA-format numbers** (LX1069, DE4419):
    436,945 matched and 3,869 unmatched train rows (67,927 and 1,284 rank). For matched rows the NM `operator`
    covers it; for unmatched rows the carrier is lost. Their error share is only 0.48% SE (RMSE 448), so the
    expected gain is small. Fix: carrier = NM operator, else the ICAO prefix, else the 2-character IATA prefix.
  - De-mangling (AEZZ131R → AEZ131R) is exact (3,166 of 3,168 match the callsign) but changes nothing today,
    because only the 3-letter prefix is used and mangling keeps it. Keep "mangled" as a LIRF flag: it marks
    matched flights 10× more often > 3 h late and unmatched flights 77% echo.

## Ranked recommendations

Combined exploratory effect of R1 + R2 + R3 on the EXP-031 hold-outs (`p6_combined_posthoc_eval`):
**Jan 347.72 → 339.28, Jul 361.72 → 298.42, combined 355.54 → 317.30 s**. This figure is optimistic: band edges
chosen in hindsight, and the gains are concentrated in a few rows. In Jul the top 5 rows give 64% of R1's gain,
70% of R2's and 80% of R3's.

1. **R1: three-regime hedge for LIRF NM-unmatched departures ≥ 6 h late** (replaces M-014's single "non-echo
   mean" in that range). Bands 6–14 h (echo 97.7%) and ≥ 14 h (echo 45% / day-minus 55%, y = 86,400 + 1,136 s);
   prediction = Σ p_regime · E[y | regime], estimated on training months.
   - Rows: 63 in 2025, 21 hold-out, 26 rank (20 at 6–14 h, 6 at ≥ 14 h; `p6_rule_scope_counts`).
   - Addresses 13.4% SE; measured 13.4% → 2.0%, improving 18 of 21 rows.
   - Expected gain: about −20 s RMSE on the 2025 hold-outs; on 2026 it depends on 26 rows.
   - Validate: new EXP with the band edges fixed now, regime probabilities refit per fold. Also test on Jan/Jul
     the edges 12 h and 16 h as a sensitivity check (not tuning).
   - Provenance: M-014 (a participant forum, calibrated hedge), RMSE → conditional mean (CLAUDE.md §3); the regimes come
     from this check.
2. **R3: keep matched late flights near a trustworthy NM proxy.** Rule: if AOBT_3 is present, |AOBT_3 − EOBT_1|
   ≤ 1 h, AOBT_3 ≤ MVT and d_sched > 3 h, clip the prediction to MVT − AOBT_3 ± 30 min. Training-side alternative:
   fit LIRF matched and LIRF unmatched as separate models, the same logic as EXP-022.
   - Rows: 2,676 hold-out in scope, 48 changed; in scope in 2026: 1,757 Jan / 1,394 Jul (`p6_rule_scope_counts`).
   - Measured: −21.96 s Jul, −0.06 s Jan, −12.2 s combined.
   - Validate as an EXP. Because the gain sits in ≤ 5 rows per month, also report the count of rows improved vs
     worsened.
   - Provenance: M-022 nm_proxy offset; EXP-022 (stop patterns leaking between populations); "proxy suspect" marker
     from `p6_proxy_off_markers`.
3. **R2: label-free echo-regime probability for LIRF unmatched 1–6 h late.** Use a leave-one-month-out classifier
   on carrier, flight-number class (mangled/null), d_sched, hour, schedule minute, MVT second 0, stand and season.
   Either feed the out-of-fold p_echo as a GBM feature or average the calibrated hedge with the model.
   - Rows: 354 hold-out, 322 rank (`p6_lirf_unmatched_echo_by_marker`).
   - Addresses 10.3% SE. AUC 0.867 vs 0.661 for d_sched alone. Hedge averaged: Jul 9.66 → 7.54%, Jan 0.59 → 0.54%.
   - Fragile: 153 rows better, 152 worse. Validate with 3 seeds and report the spread.
   - Provenance: M-014 plus the forum note that unmatched echo behaviour is carrier-specific and stable
     (a participant, quoted in CLAUDE.md §3).
4. **Flags to add, cheap and label-free:**
   - proxy suspect: |AOBT_3 − EOBT_1| > 1 h, AOBT_3 > MVT, AOBT_3 < SCHED − 1 h, or MVT − AOBT_3 > 2 h. 4,832
     rows in 2025, 509 / 550 in Jan / Jul 2026 (`p6_rule_scope_counts`); 29–58% proxy-off vs 0.09% base.
   - LIRF mangled flight number.
   - helicopter runway codes HEL/H.
   - flight-number class.

   Expected gain is small (≤ 1–2 s) but these flags are the inputs R1–R3 need. Validate with one ablation EXP.
5. **Month-regime risk (item 4).** Keep `month_of_year` or not? LOMO cannot answer this. Proposed label-free
   diagnostic: compare the predicted mean per airport for Jan/Jul-2026 with the EUROCONTROL monthly 2026 taxi-out
   aggregates (allowed, M-017), with and without `month_of_year`, and ask the user before acting. Up to 7–9 s RMSE
   at affected airports in a wrong-regime month.
6. **Do not pursue:**
   - stand or runway code normalisation (nothing to merge);
   - timestamp de-biasing (absorbed by per-airport offsets);
   - the LFPG/LSZH day-shift rows (no precursor; 2 of 19,771 rows);
   - local-time echo at LIRF (refuted: 6 of 64 rows);
   - an ADES-mismatch "wrong join" flag (0.15% proxy-off rate);
   - the IATA carrier-key fix (0.48% SE ceiling; optional).
   - The LIRF matched-echo hedge (item 2, 7.96% SE) remains open: AUC 0.84 but mixed hold-out results, so try it
     only as an out-of-fold p_echo feature in the LIRF model, after R1–R3.

## Check files written (reports/checks/, .md + .csv unless noted)

p6_lirf_dsched_by_month, p6_flightnum_pattern_by_match, p6_lirf_unmatched_echo_by_dsched, p6_lirf_unmatched_gt6h_rows,
p6_lirf_unmatched_block_minus_sched, p6_lirf_unmatched_early_block, p6_lirf_unmatched_tz_echo,
p6_lirf_unmatched_regimes_by_band, p6_lirf_regime_hedge_eval, p6_lirf_unmatched_echo_by_marker,
p6_lirf_echo_classifier_auc (.md only), p6_dayshift_rows_all, p6_dayshift_precursors, p6_late6h_regimes_by_airport,
p6_lirf_matched_late6h_rows, p6_proxy_off_markers, p6_pred_vs_proxy_disagreement, p6_pred_proxy_gt1h_nonsuspect,
p6_proxy_clip_rules, p6_lirf_matched_mangled, p6_mangled_demangle_vs_callsign, p6_matched_block_eq_sched_by_airport,
p6_lirf_matched_echo_by_nmdelay, p6_lirf_matched_late_echo_by_mvtsec0, p6_lirf_matched_echo_classifier (.md only),
p6_aobt3_offset_by_airport, p6_aobt3_offset_by_airport_month, p6_minute_step_sources, p6_holdout_bias_vs_minute_step,
p6_defect_marker_drift, p6_nonlirf_unmatched_late_holdout, p6_lfpg_runway_by_month, p6_runway_values,
p6_stand_normalisation, p6_actype_hygiene, p6_actype_mismatch_pairs, p6_flt_prefix_coverage,
p6_combined_posthoc_eval, p6_top_rows_holdout_EXP-031, p6_rule_scope_counts.
Python scripts that produced the classifier and hedge evaluations: scratchpad q9.py, q16.py, q30.py, q31.py (not in the repo).

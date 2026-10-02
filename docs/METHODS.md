# Methods and provenance

Every modelling or cleaning method used in the pipeline, with its provenance (CLAUDE.md §1.3):
(a) official documentation, (b) peer-reviewed paper, (c) past PRC repo, (d) dated forum statement
(local, uncommitted export `docs/references/forum_2026-10-02.md` of `#prc-data-competition`; cited by
author and date, item numbers refer to that export), (e) experiment in this repo.
Literature citations marked *(verify)* were written from memory and must be checked against the paper before
the JOAS write-up.

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
- (b) Idris, Clarke, Bhuva & Kang, "Queuing model for taxi-out time estimation", *Air Traffic Control
  Quarterly* 10(1), 2002 — number of aircraft taxiing as the main taxi-out predictor *(verify)*.
- (b) Simaiakis & Balakrishnan, "A queuing model of the airport departure process", *Transportation Science*
  50(1), 2016 *(verify)*.
- (d) a participant, 17/09/2026 (item 8): airport-hour congestion aggregates hold most of the signal.

## M-007 Queue position from NM off-block
`n_takeoffs_since_aobt3` = departures that took off at the airport between this flight's AOBT_3 and its take-off;
`n_taxiing_at_mvt` = departures with AOBT_3 ≤ t that are not yet airborne. Implemented with cumulative event
counts + ASOF joins.
- (b) Idris et al. 2002 (as M-006) *(verify)*: queue length during the taxi.
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
  de-icing is done after push-back: ICAO Doc 9640, *Manual of Aircraft Ground De-icing/Anti-icing Operations*
  *(verify edition/section)*;
- low-visibility procedures reduce runway throughput: ICAO Doc 9365, *Manual of All-Weather Operations*
  *(verify)*;
- (d) a participant, 24/09/2026 (item 34) uses weather (rank 3); a participant, 28/09/2026 (item 63): METAR barely moved
  results at airports without ADS-B coverage.
- Data card: `docs/data_sources/iem_metar.md`.

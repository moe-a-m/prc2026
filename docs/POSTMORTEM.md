# Post-mortem: motivated-engine vs the top 10 (PRC Data Challenge 2026)

Written 2026-11-09, after the results were presented (14th OpenSky Symposium, 30 Oct 2026). It compares our final
recipe (v11 = EXP-118, `docs/METHODS.md` "Final model at a glance") with the published solutions of the ten
top-ranked teams. Our own numbers come from `reports/experiments/EXP-118.md` and `reports/checks/`; arithmetic for
this document is in `reports/checks/postmortem_error_share.md`. Other teams' numbers are quoted from their
repositories at the commits listed in [Sources](#sources). They are *their* statements, read but not re-run.

## 1. Result and how it was scored

- **Final ranking.** 510 teams registered, 96 sent a final file, and 56 were eligible (final file plus public repo)
  [organizer slides, 30 Oct 2026]. We were **44th of the 56**.
- **Top 10 (final RMSE, s).** charming-eel 176.16, zesty-puzzle 180.18, youthful-giraffe 183.66,
  vigorous-whistle 183.84, gentle-igloo 184.03, jolly-lobster 185.06, strong-moose 186.18, strong-crane 186.56,
  versatile-watermelon 186.87, spirited-tiger 188.22.
- **The final scores are not public-board scores.** The winner's README gives 214.75 on the public Jan/Jul board for
  its final file, against 176.16 in the final table. The final ranking scored the single `_final.parquet` file
  (Jan, Feb, Jun, Jul 2026), which was not on the board.
- **Public board for reference.** Our best was 268.21 (v12). The top-10 teams state between 211.7 and 230.4.
  Some of those are flattered:
  - strong-crane's Jan/Jul rows are a score-weighted ensemble of 64–70 earlier uploads ("calibration on the ranking
    set, not a model", their paper);
  - versatile-watermelon decoded 91 labels by probing the board (not in its final file);
  - vigorous-whistle used nine score-derived Rome values for a while (switched off in its final file).

  Our board numbers were never used for selection (`docs/SUBMISSIONS.md`).

## 2. Like-for-like comparison on the same hold-out rows

Two teams publish hold-out scores on exactly our July-2025 rows (190,713 departures). versatile-watermelon's
Jan + Jul 2025 cross-validation uses the same 153,706 + 190,713 rows.

| Team | Jan-25 | Jul-25 |
|---|---|---|
| **motivated-engine (EXP-118)** | **334.2** | **300.8** |
| versatile-watermelon (9th) | 315.65 | 246.76 |
| strong-crane (8th) | — | 259.9 (259.4 after its LOBT window) |
| vigorous-whistle (4th; its own folds) | 322.06 | 255.99 |

**January is close; July is where we lose 40–55 s.** In January our error is dominated by a few huge labels, as
everyone's is: NM-unmatched rows carry 67% of our January squared error.

strong-crane splits its July hold-out by population and airport (`paper/paper_final_phase.pdf`, Tables 7–8).

| July 2025 | ours | strong-crane | gap |
|---|---|---|---|
| all rows | 300.8 | 259.9 | +40.9 |
| NM-matched (186.8k rows) | 247.5 | 211.1 | **+36.4** |
| NM-unmatched (3.9k rows) | 1,215.3 | 1,076.5 | +138.8 |

Gap by airport: LIRF +121.6, **LSZH +61.5, EDDF +55.2**, EHAM +30.6, LEBL +28.3, LEMD +23.8, LTFM +19.9,
EDDM +19.4, EGLL +16.7, LFPG +10.3. **We are worse at every airport.**

**Decomposition of the July gap.** Bringing only our unmatched rows to strong-crane's level would have gained
10.1 s. Bringing only our matched rows to zesty-puzzle's July matched-row RMSE (200.4) would have gained 36.6 s.
Both together give 252.7, which is inside the top-team range (`postmortem_error_share.md` §2). So in July
**most of the gap is on ordinary NM-matched flights**, and it is largest at EDDF and LSZH. Both airports had good
ADS-B reception in July 2025, so the cause is how we used the tracks, not missing data (lever 3).

## 3. What the top teams did that we did not

Levers are in order of the gains the teams state. "Board" = public-board seconds, "CV" = their local validation.

### Lever 1 — Recording-regime mixture on every row, with the taxi model trained on normal rows as a residual

**What they did.** All ten teams treat each label as one of several recording types:
- a schedule copy (block = SCHED);
- at Rome, the previous day's date (label ≈ 86,400 s + taxi);
- a normal block time; gentle-igloo also adds IOBT, LOBT and EOBT copies.

A classifier gives P(type) for **every row**, and the prediction is the probability-weighted mix of the candidate
values. The taxi regressor is trained **only on normal rows**, on `y − (MVT − AOBT_3)` with the residual clipped
(±5,000–7,200 s). Several weight the classifier by the cost of a wrong call: zesty-puzzle, charming-eel and
gentle-igloo weight by `(spread / 3600)²`.

**Stated gains.**
- zesty-puzzle (board): 546 → 388 from the residual target, 361 from the mixture, 291 from the classifier
  ensemble.
- gentle-igloo (board): −135 from a 2-class mixture.
- versatile-watermelon (CV): −149 from the residual, −74 from the mixture.
- spirited-tiger (local): 400.9 → 389.6 from the mixture alone.

**What we did.**
- A single L2 model on the raw target, with defect *indicators* as features.
- A three-regime hedge (M-026) on only about 26 rows: very late NM-unmatched departures at Rome.
- We tested the residual target (M-022, EXP-034) and rejected it: +27.6 / +48.6 s on normal rows. That test
  differed from theirs in three ways:
  - it trained on all rows, schedule copies included;
  - its baseline fell back to `MVT − SCHED` when AOBT_3 was missing;
  - the residual was not clipped.

  EXP-034 produced predictions such as −20,851 s and +28,707 s on unmatched rows. We rejected the idea when only
  our version of it had failed.

### Lever 2 — Dedicated models for flights without an NM match (above all Rome)

**What they did.** Every top team has a specialist for these rows. Its main inputs are:
- the flight plan recovered from the same flight's NM-matched *arrival* record at its destination (strong-crane,
  zesty-puzzle, youthful-giraffe, jolly-lobster, strong-moose);
- the aircraft's time on the ground since it landed (charming-eel via OPDI, vigorous-whistle via stand
  turnaround);
- each airline's habit of copying the schedule (youthful-giraffe: 10 airlines account for 1,689 of 1,699 late
  placeholders);
- rules that place the off-block *outside* the recovered plan's ±3,606 s window (strong-crane: 0 of 190 such 2025
  labels lie inside it).

**Stated gains.**
- strong-crane (same July rows as ours): unmatched rows 1,931 → 1,090 s, overall 348 → 262.
- jolly-lobster: no-plan specialist −51.6 s, plus −29.9 from its airport routing.
- spirited-tiger: mixture + Rome model 381.4 → 322.3 (local).

**What we did.** The M-026 hedge for flights at least 6 h late; a separate model for Rome's unmatched rows (EXP-040)
was far worse and rejected. We never joined a departure to its own arrival record at its destination, so the
recovered plan was never used.

### Lever 3 — ADS-B: full-year coverage, learned stand map, model inputs or a learned residual stage

**What they did.**
- **Coverage.** adsb.lol for all of 2025, so the ADS-B inputs exist on the whole training set.
- **Matching** in two or three passes:
  - callsign plus a ground-to-air transition near MVT;
  - then a unique take-off transition within ±90–120 s;
  - then the same restricted to the aircraft type.
  - Unmatched rows go through a learned flight-number → callsign map.
- **Stand positions** learned from the data. Either where arriving aircraft park after on-block (charming-eel,
  jolly-lobster, versatile-watermelon) or where departures first sit still (zesty-puzzle, vigorous-whistle: 1,111
  stands). charming-eel: "left the stand" is within 60 s of the label for 77–83% of departures at well-covered
  airports, against about 20% for AOBT_3.
- **Use.** Many clocks per flight (first seen, first move, end of hold, push-back, longest stop), fed either as
  model inputs or to a *learned* residual stage on `y − observed taxi`. The winner has about 190 surface-track
  features.

**Stated gains.**
- Board, ADS-B stage alone: vigorous-whistle −19.0, strong-moose ≈ −16.8, gentle-igloo −15.2, youthful-giraffe
  −14.3, jolly-lobster −13.6 (+ −5.1 re-stack), zesty-puzzle 263.2 → 244.6.
- Two teams measured a fixed rule against a learned stage: gentle-igloo found the fixed physical estimate 18–20 s
  worse, and strong-moose found raw ADS-B as the answer raised day RMSE from 229.5 to 276.1.

**What we did.**
- ADS-B only as a fixed post-step (M-028): shrink toward the off-block estimate, gated at |est − pred| ≤ 600 s.
  Gain −3.9 / −3.7.
- Stand positions from OSM. In July 2025 we matched 94.1% of EDDF and 94.2% of LSZH departures to an ADS-B
  take-off. 81.8% and 77.4% had a ground segment. Yet only 16.7% and 27.3% were placed at their own stand
  (`reports/checks/p4_adsblol_coverage.md`). Those are our two worst airports against strong-crane outside Rome.
- Until the final phase we had adsb.lol only for the Jan/Jul days, about 1/6 of the 2025 training rows. Our
  ADS-B-as-inputs test (M-034, EXP-119–134) ran in that condition. It found the inputs improved every base model
  but did not beat the post-step, and was not adopted.
- The 600 s gate excludes the rows where ADS-B matters most. Our own check (`m034_adsb_vs_nm.md`) showed that where
  AOBT_3 is more than 15 min off, ADS-B is closer in 90–95% of rows (median error 32–45 s vs 1,259 s).

### Lever 4 — Neural and sequence members

**What they did.** TabM, RealMLP and ResNet with numeric embeddings; transformers or attention over the airport's
movement stream; runway GRUs; an open-weights tabular foundation model (Kumo, zesty-puzzle).

**Stated gains.** Typically 1–7 s:
- charming-eel: "neural networks dropped the RMSE by 7 points";
- vigorous-whistle: −3.5 and −3.3;
- jolly-lobster: MLP residuals 0.9991-correlated with its trees, blend gain −0.011.

**What we did.** An entity-embedding MLP (M-013), rejected. Real but secondary.

### Lever 5 — EUROCONTROL daily pre-departure-delay reconciliation and monthly calibration

**What they did.** Most top teams shift delayed flights per airport-day so the totals match EUROCONTROL's published
daily pre-departure delay.

**Stated gains.** 1–3 s (jolly-lobster −2.95, vigorous-whistle −1.33). Monthly level calibration is ≤ 0.6 s or
negative for most; it helped only charming-eel noticeably.

**What we did.** We left these sources out because they carry no open licence (prize-rule reading, `CLAUDE.md` §4).
youthful-giraffe (3rd) used no EUROCONTROL data at all, so **this is not what separates us**. Our M-029 test of
monthly calibration was also negative.

## 4. What we got right

- **LOBT ±3,606 s window (M-031).** Every top team uses the same bound. It was worth −7.5 s on the board for us;
  spirited-tiger reports −36 s, measured together with a CatBoost weight change.
- **Month hold-outs.** youthful-giraffe found week folds chose a stacker that lost on the board. jolly-lobster
  states that day folds leak.
- **Weather.** METAR or ERA5 was near-zero or rejected for youthful-giraffe, charming-eel, spirited-tiger and
  versatile-watermelon, as for us.
- **Reproducibility and traceability.** Our final file rebuilds byte-identically from a clean clone
  (`reports/checks/final_reproduction.md`). The winner warns its result will "not perfectly match".
- **Open-data discipline.** Our cost from it was small (lever 5 is worth 1–3 s).

## 5. Why we missed the big levers

1. **One failed implementation was read as a failed idea.** EXP-034 (residual target) and EXP-119–134 (ADS-B as
   inputs) were each run once, under conditions that handicapped the idea: copy rows in training, an unclipped
   fallback baseline, ADS-B on 1/6 of the training rows. Both were rejected. A rejection should name the condition
   that would reverse it and test that condition.
2. **The error budget pointed at the right rows, but we hedged instead of modelling.** We knew from EXP-011 onward
   that a small share of rows dominates the squared error: NM-unmatched rows were 1.6% of rows but 50.5% of hold-out
   squared error in EXP-118. Our response was hedges on a few dozen rows. The top teams built a classifier and a
   value model for that population.
3. **Post-processing instead of learning.** ADS-B, the hedge and the LOBT window were all hand-gated post-steps with
   cross-fitted constants. Where the top teams used the same evidence, they learned the gate (residual stages,
   stake-weighted classifiers).
4. **Data acquisition came late.** Full-year adsb.lol arrived only in the final phase (485 days), after the model
   design was frozen at v11. We never built a stand map from the tracks, even though ARR on-block times are in the
   ranking data for every arrival.

## 6. If we continue (e.g. for a JOAS paper or a 2027 edition)

Each item below needs its own `docs/METHODS.md` entry citing the team repo as provenance (originality rule: idea
only, our own code) and its own experiment row.

1. **Regime mixture on all rows** (stake-weighted P(copy) classifier) with a value model trained on normal rows on a
   clipped `y − (MVT − AOBT_3)` residual. Re-run EXP-034 under these conditions.
2. **Unmatched-row specialist:** recover the plan from the same flight's arrival record at its destination,
   airline copy-habit rates, turnaround from ADS-B (open data only), and the outside-window rule.
3. **ADS-B stand map learned from arrivals' parked positions**, then several clocks per departure as inputs on
   the full-year archive (re-run M-034), and a learned residual stage in place of the fixed 600 s gate.
4. Only then: neural or sequence members.

## Sources

Organizer:
- [Challenge overview](https://ansperformance.eu/study/data-challenge/dc2026/)
- [Ranking page](https://ansperformance.eu/study/data-challenge/dc2026/ranking.html)
- [Winners page](https://ansperformance.eu/study/data-challenge/dc2026/winners.html)
- [Symposium slides, 30 Oct 2026](https://ansperformance.eu/study/data-challenge/dc2026/media/PRC_Data_Challenge_2026.pdf)
  (all read 2026-11-09)

Team repositories, `github.com/prc-data-challenge-2026/<team>`, read at these commits on 2026-11-09:

| Rank | Team | Commit | Main files read |
|---|---|---|---|
| 1 | charming-eel | 5c05d9ab2df4 | README.md |
| 2 | zesty-puzzle | 71ed855de5e4 | README.md, docs/METHOD.md, docs/upload_log.md, docs/model_card.md |
| 3 | youthful-giraffe | 19ef12499858 | README.md, docs/writeup/SOLUTION.md, docs/writeup/METHOD.md, docs/PUBLIC-SUBMISSIONS.md |
| 4 | vigorous-whistle | 979f74afd8c9 | README.md, docs/final_file/*.md, docs/adsb_*/README.md, docs/stack_resid/README.md |
| 5 | gentle-igloo | b29bd855180f | README.md, docs/development-history.md, docs/negative-results.md, docs/model-design.md |
| 6 | jolly-lobster | 93dab8449703 | README.md, docs/PIPELINE.md, docs/LAB-NOTES.md |
| 7 | strong-moose | 3704271dd685 | README.md, docs/METHOD.md, kutuk/skor_defteri.csv |
| 8 | strong-crane | deba7d3a8cb4 | README.md, paper/paper_final_phase.pdf (Tables 7–8), data/reference_v7f4/report_dev.json |
| 9 | versatile-watermelon | e0f937330bac | README.md, writeup/README.md, docs/model.md, docs/results.md |
| 10 | spirited-tiger | 793b56ad6df4 | README.md, docs/DESIGN.md, notes/levers.md |

The figures used in the arithmetic were checked directly in those files:
- strong-crane July table: their paper, Tables 7–8;
- zesty-puzzle per-month matched RMSE: `docs/METHOD.md` line 345;
- versatile-watermelon: `README.md` line 15;
- vigorous-whistle: `docs/stack_resid/README.md` and `docs/scout/README.md`.

Other figures were extracted by reading agents and are quoted, not re-verified.

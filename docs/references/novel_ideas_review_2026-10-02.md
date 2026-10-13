# Novel angles for PRC Data Challenge 2026 (taxi-out): research report

Date: 2026-10-02. Scope: web research only. Nothing was installed and no file under
the repository was changed. Raw downloads are in `scratchpad/repos/` and `scratchpad/src/`.

**Citation marks.** "VERIFIED" means I downloaded the page or PDF and read the passage quoted.
"UNVERIFIED" means I only saw a search snippet, or the page would not load.

**Excluded because you already have them** (as you listed): per-airport LightGBM, NM time
deltas, congestion windows, runway sequence and wake, stand occupancy from ARR rows,
OOF stand×runway encoding, METAR, the schedule-echo hedge, Jan/Jul month hold-out, the
rejected MLP, residual corrector, EC aggregates, queue counts and P10 reference, OSM
stand-match plus first movement (23% coverage), and NM default-taxi detection features
(no gain).

**Originality and fair play.** Several ideas below come from rival teams' public GPLv3
repositories, published during the competition. Their ideas may be borrowed if we cite them
(repo URL + commit in `docs/METHODS.md`) and write our own code. We must not copy their code.
Learning from rivals' published leaderboard-driven choices during a live competition could be
seen as a fair-play issue (CLAUDE.md §1.9). **Ask the user, and if needed the organizer, before
using any rival-derived idea.** Each such idea is tagged [RIVAL].

---

## 0. One diagnostic to run first (≈1 h): our July is the outlier

Here are the published local and board scores. They are not fully comparable, because each
team validates differently.

| Team (repo) | Local Jan | Local Jul | Board |
|---|---:|---:|---:|
| us | 347.4 | 378.1 | 319.9 |
| zestful-fountain (Phoenix-Ops-LTD/prc2026-taxiout), Jan/Jul hold-out | 344.7 (v5) | 301.7 (v5) | 290.1 (v5) → 273.6 (v12) |
| joyous-rainbow (radekacar/joyous-rainbow), Jan/Jul hold-out | — | — | 324.1 local → 299.2 |
| elegant-alligator (javidmardanov), Jul/Nov tuning | — | 291.5–297.3 | 268.6 |

Our January is comparable to zestful-fountain's (347 vs 345). Our July is about 75 s worse
(378 vs 302). **Almost all of our gap to the top-20 therefore sits in July.**

Joyous-rainbow's three-group decomposition is a cheap way to locate it. Measured in their
final model:

| Group | Share of departures | Share of squared error | RMSE in group |
|---|---:|---:|---:|
| A: no NM match | 1.56% | 49.3% | 1,822 s |
| B: NM AOBT ~25 min late | 1.32% | 15.6% | 1,115 s |
| C: regular | 97.1% | 35.0% | 195 s |

Proposed check: compute the same SSE table for our Jul-2025 out-of-fold (OOF) predictions,
per airport. Joyous-rainbow and zestful-fountain both point at LIRF unmatched rows, where
taxi ≈ take-off − schedule and can reach about 24 h. A model that cannot extrapolate loses
thousands of seconds per row there.

Source: radekacar/joyous-rainbow README, VERIFIED
(https://github.com/radekacar/joyous-rainbow, raw README downloaded). [RIVAL]

---

## 1. Taxi-out / off-block estimation methods, 2022–2026

### 1.1 Linear-leaf gradient boosting to break the tree "ceiling" on extreme rows

**What it is.** In LightGBM, `linear_tree=true` makes each leaf a linear model in that
branch's numerical features instead of a constant. The docs say: "the model at each leaf is
linear instead of constant… categorical features are used for splits as normal but are not
used in the linear models… missing values should not be encoded as 0… it is recommended to
rescale data… works only with cpu, gpu device type and serial tree learner… regression_l1
objective is not supported… significantly increases the memory use."

**Why it fits our error structure.** A tree with constant leaves cannot predict beyond the
leaf means it has seen. Our rows of 2–24 h (schedule-echo and delay-driven) are the 1% that
carries about ⅔ of the squared error.

- Joyous-rainbow: linear leaves took local RMSE from 361.0 to 331.7 and the official score
  from 333.7 to 301.8. Error on long flights fell from 1,666 to 1,181. They call it "larger
  than everything else put together."
- They also found, consistent with RMSE theory, that these all hurt:
  - capping predictions at 1 h: +178 s
  - a per-airport cap: +19.7 s
  - Huber loss: +1.8 s
- An alternative with the same goal is **predicting a residual on a continuous proxy**, so
  the extrapolation is carried by the proxy:
  - zestful-fountain uses y − (MVT − AOBT_3), with a fallback chain LOBT → EOBT → 1000 s.
    For LIRF unmatched rows with no IOBT it uses MVT − SCHED.
  - This took their Jul–Dec hold-out from 342.9 to 268.0 s.
  - Check whether our per-airport models predict y directly. If they do, both changes apply.

**Effort:** 2–4 h. Add a flag, rescale the numerics, check memory with 4 threads and 15 GB on
the largest airport, then run EXP on Jan and Jul.

**CPU:** yes. The docs list CPU support. Memory is the risk, so train per airport.

**Citations:**
- LightGBM Parameters, `linear_tree`: VERIFIED (https://lightgbm.readthedocs.io/en/stable/Parameters.html).
- Underlying method: Shi, Li & Li, "Gradient Boosting with Piece-Wise Linear Regression Trees",
  IJCAI 2019 (https://www.ijcai.org/Proceedings/2019/476), UNVERIFIED (search snippet only).
- Gains: radekacar/joyous-rainbow README, VERIFIED [RIVAL].
- Residual-on-proxy and LIRF fallback: Phoenix-Ops-LTD/prc2026-taxiout METHOD.md, VERIFIED
  (https://github.com/Phoenix-Ops-LTD/prc2026-taxiout) [RIVAL].

### 1.2 EUROCONTROL Innovation Hub's generalisable GBDT (SIDs 2025)

**What it is.** Swatowska & Gabagnou (EUROCONTROL Innovation Hub) trained CatBoost with MAE
loss on 4.1 M flights (2022–2024) at 6 airports. Inputs:
- AODB/APDF records
- METAR from SADIS
- BADA aircraft data: wing area, MTOW, length, engine count
- a **de-/anti-icing status** feature (None / Stand / Remote)
- a **scheduled airport works** indicator from EUROCONTROL Airport Corner

Results: MAE fell 30–44% against Standard Taxi Times at regional airports, but only 1–6% at
major airports. In their benchmark CatBoost beat linear models and random forest
(MAE 2.73 vs 2.92 min; RMSE 4.05 vs 4.21 min).

**Why it matters for us.** It confirms that physical and operational features give only small
gains at hubs, consistent with our ~2/3-of-error-in-1%-of-rows structure. Two new feature
ideas come out of it:
- **Aircraft size.** We can get it openly from the FAA Aircraft Characteristics Database (§5)
  instead of BADA.
- **De-icing location.** A proxy is possible: "freezing METAR day × airport with remote
  de-icing pads". Note that Frankfurt and Munich publish de-icing plans; licences are unchecked.

MAE loss is wrong for our metric and should not be copied.

**Effort:** 2 h for aircraft-size features. **CPU:** yes.

**Citation:** SIDs 2025 paper 119, VERIFIED
(https://www.sesarju.eu/sites/default/files/documents/sid/2025/papers/SIDs_2025_paper_119-final%20v2.pdf;
PDF downloaded, Table I, Table III and the abstract read).

### 1.3 Graph neural networks and spatio-temporal attention on the surface network

**What it is.**
- SESAR ID 2021 paper 78, "Variable Taxi-Out Time Prediction Using GNNs", and the later
  J. Air Transportation paper "Graph Neural Networks with Spatiotemporal Flow Features for
  Aircraft Taxi-Out-Time Prediction" (doi 10.2514/1.D0369):
  - Each taxi route is a sub-graph of the airport node-link model.
  - Flow features on the edges are built from route information and movement start times.
  - Transformer layers sit on top.
  - Taxi-out is split into gate→queue time plus queue time.
- Aerospace 2024 MT-DSTGAN: a multi-task dynamic spatio-temporal graph attention network.
- Reported: 40–60% lower error than FAA and EUROCONTROL standard methods. Those baselines are
  weak, and GBM matched the GNN in the same paper.

**Why it probably does not fit us.** These models need the taxi route of every flight, which
we only have for about 23% of 2025 departures via ADS-B. Our error is dominated by label
artefacts, not surface physics, and a GNN would not touch group A or B.

The cheap transferable idea is **"edge flow" congestion**: count aircraft whose straight-line
stand→runway path crosses a shared taxiway segment in the window. It could be built from
apt.dat or OSM graphs plus the APDF stand and runway, with no ADS-B. Whether it adds anything
beyond our congestion windows is doubtful: joyous-rainbow found four congestion variants all
within −0.8 to +1.8 s.

**Effort:** 15–30 h for a GNN, not recommended; 6–8 h for edge-flow features.
**CPU:** GNN training on about 2 M rows is slow on 4 threads.

**Citations:**
- SIDs 2021 paper 78 (https://www.sesarju.eu/sites/default/files/documents/sid/2021/papers/SIDs_2021_paper_78.pdf): UNVERIFIED.
- doi 10.2514/1.D0369: UNVERIFIED.
- MT-DSTGAN, Aerospace 2024 (https://doaj.org/article/52000c32bd5a4e2b97fbf281a61caeaf): UNVERIFIED.

### 1.4 Queue-informed taxi-out from open ADS-B (Olive, Waltert, Schultz 2025)

**What it is.** ADS-B positions are mapped to timed sequences of taxiway segments, from which
the authors compute saturation rates, taxi-out distributions *as a function of departure-queue
size*, and flow-density relationships. The case study is LSZH, selected days in 2024.

**Use for us.** It gives provenance for a "queue size at estimated off-block" feature. That
variant was already rejected (same-runway queue counts), so it is low priority. It is a good
methods citation for the paper.

**Citation:** UniBw LVK page, VERIFIED (https://www.unibw.de/lvk-en/publications/2025_zhr_surface).

---

## 2. Regression with corrupted labels when the test labels are equally corrupted

The key principle: under RMSE the optimal prediction is E[recorded y | x]. When labels come
from a mixture of regimes (true taxi, schedule echo, day shift, NM lag), the target is

**E[y|x] = Σ_k P(k|x) · E[y | x, k]**

The two parts can be learned separately. You already do a calibrated hedge for the echo
regime. The items below are what is new beyond that.

### 2.1 Explicit multi-regime mixture with an extrapolating component per regime

**What it is.** Replace the single hedge with three things:
1. A **regime classifier** P(k|x) over {normal, schedule-echo, day-shift, NM-late}. Its
   labels are defined on training data from target-derived rules: BLOCK = SCHED, |BLOCK −
   (MVT − 86400)| small, and so on.
2. One regressor per regime, each with a functional form that extrapolates:
   - echo: E[y] ≈ MVT − SCHED, exactly, plus a small correction;
   - day-shift: about ±86400 plus normal taxi;
   - NM-late: AOBT_3 − 25 min type offset;
   - normal: GBM.
3. The combination by the formula above, with probabilities **shrunk** (multiplied by λ < 1,
   chosen OOF).

Published evidence for group A (no NM record):
- **Joyous-rainbow:**
  - classifier AUC 0.956, probability shrunk by 0.8;
  - mixture: group RMSE 1,860 vs 1,908 for a curve alone;
  - all three combined: 1,822;
  - echo share at LIRF unmatched rows: 51.4%;
  - E[y | MVT − SCHED] for these rows is "flat for small delays, then rising roughly
    one-to-one once the delay exceeds a few hours". They fitted a per-airport cubic plus a
    hinge at 3 h.
- **Merry-mushroom** (TAUIL-Abd-Elilah): a **Rome specialist that models taxi / (MVT − SCHED)
  as the target**, a ratio, "allowing extrapolation on rare long records". It also uses a
  classifier for whether "Rome and Istanbul records use the scheduled timestamp" with a fixed
  half-probability correction.
- **Zestful-fountain:** a five-seed bag of the small LIRF missing-IOBT specialist improved
  specialist RMSE in all four tested months, for example 3618.6 → 3488.5 in January.
  Three "mixture-of-baselines classifiers" were rejected there, so gains are not guaranteed.

**Why it fits.** Group A plus group B is about 3% of rows and about 65% of SSE. Every second
of RMSE gain on 1,822 s rows is worth roughly 25 times the same gain on regular rows.

**Effort:** 4–6 h. Regime labels in SQL, one LightGBM classifier, three closed-form or small
regressors, OOF λ. **CPU:** trivial (small subsets).

**Method citations:**
- Patrini et al., "Making deep neural networks robust to label noise: a loss correction
  approach", arXiv 1609.03683. VERIFIED abstract (https://export.arxiv.org/abs/1609.03683).
  This is the classification analogue: a known corruption transition is modelled in the
  forward direction, not inverted.
- Competition evidence: joyous-rainbow README, VERIFIED; merry-mushroom README, VERIFIED
  (https://github.com/TAUIL-Abd-Elilah/prc-data-challenge-2026); zestful-fountain METHOD.md,
  VERIFIED. All [RIVAL].

### 2.2 Prior-shift (label-shift) adaptation of regime probabilities to 2026

**What it is.** The regime prior P(k) may differ between 2025 and 2026. Joyous-rainbow
observed that the official score was consistently 25–31 s better than local, and attribute
this to "the 2026 data contain fewer extreme records". If the classifier's P(k|x) is
calibrated on 2025, the EM procedure of Saerens, Latinne & Decaestecker (2002) re-estimates
P_2026(k) from the *unlabelled* 2026 feature distribution:
- iterate: posterior ∝ P(k|x) · P_2026(k) / P_2025(k);
- re-estimate P_2026(k) as the mean posterior.

This needs no ranking labels and no leaderboard feedback, so it is compatible with fair play.
Group-B rows have ranking-visible markers (AOBT_3 vs LOBT/EOBT gaps), and group A is visible
(FLIGHT_ID null), so the shift can be partly measured directly.

**Why it fits.** The hedge weight is the single most leveraged parameter in our error budget.
A wrong prior on the 2026 echo share directly mis-scales the largest errors.

**Effort:** 2–3 h if a regime classifier exists. **CPU:** trivial.

**Risk.** EM prior estimation assumes P(x|k) is stable. Validate by simulating a shift:
calibrate on 10 months, estimate the prior on a held-out month, and compare with the true
regime share.

**Citation:** Saerens, Latinne, Decaestecker, "Adjusting the outputs of a classifier to new
a priori probabilities: a simple procedure", Neural Computation 14(1), 2002, PubMed 11747533.
UNVERIFIED: the page needed cookies; citation from memory. Verify before use.

### 2.3 Distributional GBM (mixture densities) as an alternative to hand-built regimes

**What it is.** LightGBMLSS (v0.6.1, Apache-2.0) fits all parameters of a conditional
distribution, including "Mixture-Densities", "Zero-Adjusted and Zero-Inflated Distributions"
and "Normalizing Flows". The mean of a fitted 2–3 component mixture is then the prediction.
NGBoost (arXiv 1910.03225) is the natural-gradient counterpart.

**Why it may help.** A mixture captures bimodal regimes without hand rules.
**Why it may not.** Our regimes are near-deterministic functions of known columns, so
hand-built rules (2.1) are likely sharper and far cheaper. LightGBMLSS pulls in PyTorch and
is slow on 2 M rows with 4 CPU threads.

**Effort:** 6–10 h. **CPU:** feasible only per airport or on group A/B subsets. A new
dependency would need a `docs/DEPENDENCIES.md` entry. **Rank: low.**

**Citations:** LightGBMLSS PyPI metadata, VERIFIED (https://pypi.org/pypi/lightgbmlss/json);
NGBoost arXiv abstract, VERIFIED (https://export.arxiv.org/abs/1910.03225).

### 2.4 What not to do, with evidence

Joyous-rainbow's measured negatives:
- robust Huber regression for group A: +16 s;
- blending toward a typical value: +6.4 s;
- a two-stage tail classifier with low confidence (mean probability 0.43): +0.7 s;
- clipping at 1 h: +178 s.

These match the theory that RMSE needs the conditional mean of the *recorded* label.
Down-weighting or denoising labels (classic noisy-label methods that target the *true*
label) is the wrong objective here.

Elegant-alligator's V4 "rare tail" change improved local (259.98 → 258.01) but worsened
official (271.04 → 271.51). Tail-specific tweaks below about 2 s local do not transfer;
joyous-rainbow independently reports the same "~2 s noise floor".

Sources: radekacar README VERIFIED; javidmardanov docs/autoresearch_attempts.md VERIFIED. [RIVAL]

---

## 3. ADS-B ground processing

### 3.1 What the `traffic` library provides (v2.13 docs, VERIFIED)

Page: https://traffic-viz.github.io/api_reference/traffic.algorithms.ground.html
(downloaded and read).

| Class or function | What it does |
|---|---|
| `movement.StartMoving(speed_threshold=2, time_threshold='30s', filter_dict={'compute_gs': 3}, resample_rule='5s')` | "Returns the part of the trajectory after the aircraft starts moving." Docs: "extensively tested on aircraft taxiing before take-off". |
| `parking_position.ParkingPositionGeometricIntersection(airport, buffer_size=1e-05, parking_positions=None)` | Intersects the trajectory with buffered OSM parking-position LineStrings. Docs recommend `.max()` to keep the longest-duration segment. |
| `pushback.ParkingAreaBasedPushback(airport, stand_areas=None)` | Uses start of movement, intersection with an apron area, and "the moment the aircraft suddenly changes direction in the computed track angle". |
| `pushback.ParkingPositionBasedPushback(airport, filter_dict=…, track_threshold=90, parking_positions=None)` | Same idea, anchored on the parking position. Both pushback classes warn of "poor performance when trajectory point on ground are lacking". |
| `runway.RunwayAlignment(airport, rwy_width_m=60.0, …)` | Finds trajectory segments aligned with runways. |
| `graphs.AirportGraph` | Builds a graph from OSM, with `map_flight` (most probable path along edges) and `make_parts`. |
| `kalman_taxiway.KalmanTaxiway` | A Kalman filter that snaps the trajectory to taxiways. |

**New relative to what you have (stand match + first movement).** A **track-reversal
pushback detector** (`ParkingPositionBasedPushback`, 90° track threshold) does not need the
aircraft to be seen *stationary* at the stand. It only needs a few points during the
push-and-turn. That could raise coverage above 23% for aircraft first heard mid-pushback.

Our "first movement" is likely biased late for aircraft first heard after pushback. A cheap
safeguard is a **censoring flag**: "first position already > 40 m from stand centroid or
already moving." The off-block estimate then becomes an *upper bound*, and the model can
learn from it differently.

**Effort:** 4–6 h, re-implemented in our own code (GPL-compatible re-implementation of the
idea, cite the docs). **CPU:** yes, per-flight geometry. **Expected gain:** small. Coverage is
the limit, and 2025 coverage is thinner than 2026, so this carries drift risk.

### 3.2 Aircraft-ready (transponder-on) milestone, Schultz, Rosenow & Olive (2022)

**What it is.** In JATM 99, 102164, the authors take "the time of receipt of the first ADS-B
message during departure to be the Aircraft Ready Time (ARDT)". Off-block is when the distance
from the first transmitted position "is getting greater than 40 m".

At EGKK they measured AOBT − ARDT: "after 2 min 67% of all flights have already reached the
AOBT milestone, 90% … less than 5 min". Message cadence: 20% within 5 s, 66% within 10 s,
92% within 20 s.

**Use for us.** First-heard-on-ground time is a second, independent off-block bound. It is
also available for aircraft that were never seen parked but were heard on the apron. It is a
feature, not a replacement. Treat receiver-coverage drift (2025 vs 2026) as a first-class
missing state, as CLAUDE.md requires.

**Citation:** VERIFIED. PDF downloaded and read, §4 and §6.2
(https://unibw.de/lvk/publications/pdf/2022_jatm_data-driven_airport_management.pdf).

### 3.3 HexAeroPy (EUROCONTROL PRU, MIT licence)

"Determine used airports, runways, taxiways and stands based on flight trajectory
coordinates." It uses hexagonal-grid metadata hosted on Zenodo (record 10651018). Version
1.0.4 on PyPI; the README lists airport and runway detection.

**Use for us.** Mainly a cross-check of APDF runway and stand against ADS-B. Low value, since
APDF already gives both. **Citation:** VERIFIED (https://pypi.org/pypi/hexaeropy/json).

### 3.4 Accuracy against A-CDM AOBT

I found no 2022–2026 paper that quantifies ADS-B off-block accuracy against A-CDM AOBT at
European hubs. The closest is the ARDT→AOBT distribution in 3.2. **Our own measurement**
(81% within 60 s on matched rows) is therefore itself publishable in JOAS.

The 13th OpenSky Symposium (JOAS) has ground-trajectory papers: map-matching of ground
trajectories (Schlosser et al.; JOAS review page VERIFIED,
https://journals.open.tudelft.nl/joas/article/view/8046) and arrival runway occupancy at LSZH
(Hänggi, Wilde, Waltert). The latter I could not open: UNVERIFIED,
https://journals.open.tudelft.nl/joas/article/view/8465.

---

## 4. Published PRC 2026 participant code (ideas only, all [RIVAL])

All READMEs below were downloaded from raw.githubusercontent.com and read: VERIFIED.

| Repo | Board (as stated) | Ideas not already in our list |
|---|---|---|
| https://github.com/Phoenix-Ops-LTD/prc2026-taxiout (zestful-fountain) | 273.56, rank 12/131 on 2026-09-13 | see 4.1 |
| https://github.com/javidmardanov/PRC-Data-Challenge-2026 (elegant-alligator) | 268.56, rank 14/147 on 2026-09-15 | see 4.2 |
| https://github.com/radekacar/joyous-rainbow | 299.23 | see 4.3 |
| https://github.com/TAUIL-Abd-Elilah/prc-data-challenge-2026 (merry-mushroom) | 288.52 | see 4.4 |
| https://github.com/satam2/knowledgeable-helicopter | not stated | separate direct model for **negative proxies** (MVT − AOBT_3 < 0); residual learner fitted only on 0–7200 s proxies |
| https://github.com/ahmetabdullahgultekin/prc-taxiout-2026 | none | P10 reference + residual (you already rejected P10); OurAirports runway bearing |
| victoralcadi, LeeMarshall1113, AbdullahKhan-x | none | skeletons or no method content |

### 4.1 Zestful-fountain (Phoenix-Ops-LTD)

1. **Residual on a continuous NM baseline** (AOBT_3 → LOBT → EOBT → 1000 s), with a LIRF
   unmatched / missing-IOBT fallback to MVT − SCHED. Jul–Dec hold-out: 342.9 → 268.0.
2. A **five-seed specialist** for LIRF with IOBT missing.
3. **Recurring service-name categories:** normalised movement/NM service strings (flight
   numbers as recurring categories) plus airport interactions. LightGBM component Jan/Jul:
   332.67 → 326.35; Feb/Aug: 272.27 → 267.59.
4. **Arrival-completed features:** taxi-in mean and standard deviation over 15/30/60 min;
   same-stand previous arrival's age, taxi-in, aircraft and carrier agreement.
   Local 321.0 → 318.5.
5. **"NM-neighbor" features:** for airport, runway and stand groups, count, mean, std,
   own-minus-mean, latest value and age of the target-free proxy MVT − AOBT_3 (0–7200 s)
   over *strictly earlier* same-month departures.
6. **"Following" features:** the same over *strictly later* windows (15/60 min) plus the
   nearest later departure. Local 313.75 → 312.97; official +1.42.
7. **NM clock overlay:** if AOBT_3 − LOBT > 7200 s, predict max(0, MVT − LOBT).
   31 rows; local +0.57 s, official +0.20 s.
8. **Planned vs actual NM flight-duration differences** and ratios (93-feature model):
   local 323.4 → 321.6.

### 4.2 Elegant-alligator (javidmardanov)

1. A **LOBT-residual expert** with airport-specific blend coefficients shrunk toward the
   global one (1,000 pseudo-rows).
2. **Timing bounds:** clip to (MVT − LOBT) ± 3606 s where LOBT is present.
3. A **winter-only LIRF flight-identity correction.**
4. A "missing-timestamp mixture of experts."
5. Airport-hour level forecasts with TimesFM-3. **Not usable:** the weights licence restricts
   use, and they flag prize clearance as unresolved.
6. Validation tip: re-weight local errors to the ranking set's airport / season /
   missing-AOBT mix.

Official: V3 271.04 → V6 268.56.

### 4.3 Joyous-rainbow (radekacar)

1. `linear_tree`: official +31.4 s (see 1.1).
2. The group-A curve + trees + mixture ensemble (see 2.1).
3. **Visibility alone matters.** METAR as a whole showed no change, but losing the
   visibility column cost 4.5 s.
4. **Local-to-board offset of 25–31 s; changes below ~2 s local did not transfer.**

### 4.4 Merry-mushroom (TAUIL-Abd-Elilah)

1. **Ratio target** taxi / (MVT − SCHED) for the Rome specialist.
2. A LOBT expert applied only when AOBT_3 is invalid or differs from LOBT by > 1 h.
3. **Nested-calibration non-negative expert weights.**
4. **"Number of other aircraft still taxiing at the estimated off-block time".**
5. Uses NOAA **GHCNh** (they state CC0). This contradicts our ledger's "NOAA ISD: do not use";
   GHCNh is a different product. Licence not verified by me.

---

## 5. Additional open data sources not in your list

| Source | Licence (evidence) | Possible use | Verdict |
|---|---|---|---|
| `holidays` Python package (v0.105) | MIT (PyPI metadata VERIFIED, https://pypi.org/pypi/holidays/json) | Public holidays for all 7 countries incl. UK and TR; day-before/after flags | Cheap (1 h); expected gain small (calendar is already partly learned from day-of-year) |
| OpenHolidays API (openpotato/openholidaysapi.data) | **ODbL-1.0** (GitHub API VERIFIED); site lists DE, FR, IT, NL, ES, CH school + public holidays from 2020 (VERIFIED, https://www.openholidaysapi.org/en/); UK and TR not listed | School-holiday flags. July 2026 vs July 2025 holiday-start alignment affects leisure peaks and bag/pax-driven off-block delays | 1–2 h; ODbL share-alike obligations like adsb.lol |
| FAA Aircraft Characteristics Database (Oct 2024 release) | US federal work, presumably public domain; licence text not checked → UNVERIFIED (page VERIFIED, https://www.faa.gov/airports/engineering/aircraft_char_database) | Wingspan, length, MTOW, ADG per ICAO type. Open replacement for BADA size features (1.2); helps rows with rare types | 2 h |
| Open-Meteo historical API | CC BY 4.0 per a rival's doc; not opened → UNVERIFIED (https://open-meteo.com/en/license) | Gap-fill for METAR instead of ERA5/CDS (no account needed) | Only if METAR gaps are material |
| NOAA GHCNh (hourly) | Merry-mushroom states CC0; UNVERIFIED | Alternative METAR-derived archive | Check licence; IEM already covers this |
| Airport de-icing plans and annual reports (Fraport, Munich) | Licence unknown → UNVERIFIED (links in victoralcadi docs/papers-and-data.md) | Provenance for *which* airports de-ice at remote pads (de-icing inside the taxi-out window), i.e. METHODS citations, not data | Use as references only |
| EUROCONTROL Airport Corner works data (used in SIDs 2025) | Not openly licensed as far as I found → UNVERIFIED | Runway/taxiway works indicator | Probably not eligible |
| Runway configuration | — | No open log found. Derive it from APDF itself (share of DEP/ARR per runway in a sliding window, PRU "peak service rate" practice) | Already partly in our congestion features |
| NOTAM archives | No open-licensed historical archive found | — | Not available |
| Airline schedules | No open-licensed source found | — | Not available |

---

## 6. Ranked top-5 by expected RMSE gain per hour of work

Expected gains are on our Jan/Jul-2025 local RMSE and are rough. They are inferred from other
teams' reports, and the local noise floor is about 2 s.

| Rank | Idea | Section | Effort | Expected gain | Gain/hour |
|---|---|---|---:|---|---|
| 1 | **Extrapolating models for long rows:** LightGBM `linear_tree` and/or residual-on-proxy target (AOBT_3 → LOBT → SCHED fallback). Skip if we already predict a residual with linear leaves. | 1.1 | 2–4 h | 5–30 s; joyous-rainbow +31 s official; zestful's residual-on-proxy was its biggest single step | highest |
| 2 | **Group-A / group-B regime mixture with closed-form extrapolating components:** ratio target y/(MVT − SCHED), cubic + 3 h hinge, OOF shrink λ, 5-seed bagging of the specialist. Starts from the §0 SSE decomposition, which should explain our July gap. | 0, 2.1 | 1 h diagnostic + 4–6 h | 3–15 s, concentrated in July | high |
| 3 | **Recurring flight-service (flight-number) categories** with airport interaction, OOF-encoded or CatBoost ordered target statistics | 4.1 #3 | 2 h | 2–6 s; zestful +6.3 s on one component | high |
| 4 | **LOBT-based expert for rows where AOBT_3 is invalid or > 1 h from LOBT,** plus (MVT − LOBT) ± 1 h bounds and the AOBT_3 − LOBT > 2 h overlay | 4.1 #7, 4.2 #1–2, 4.4 #2 | 2–3 h | 1–3 s; elegant-alligator +2.5 s official, zestful +0.2 s | medium-high |
| 5 | **Cross-flight NM-proxy regime features:** count, mean, std and own-minus-mean of MVT − AOBT_3 over *past and future* windows by airport, runway and stand. Also arrival taxi-in rolling stats and same-stand previous-arrival taxi-in. These differ from the rejected default-taxi *detection* features: they measure the local regime (de-icing, flow restrictions, NM lag clusters). Joyous-rainbow measured group B's hour-to-hour correlation at 0.556. | 4.1 #4–6, 4.3 | 3–4 h | 1–3 s; zestful +0.8 local / +1.4 official, arrival features +2.5 local | medium |

**Runners-up:**
- Prior-shift EM for 2026 regime shares (2.2), 2–3 h. Potentially large, but unproven.
- Visibility-only weather check (4.3 #3), 1 h.
- School holidays (5), 1–2 h.
- ADS-B pushback track-reversal and ARDT features (3.1, 3.2), 4–6 h. Coverage-limited.

**Not recommended under our constraints:**
- GNN / transformer surface models (1.3).
- LightGBMLSS mixture densities (2.3).
- TimesFM (licence).
- Clipping or Huber-type robustness (2.4).

**Before implementing any [RIVAL] item:** get the user's go-ahead (fair-play question),
record provenance (repo URL + commit) in `docs/METHODS.md`, and write the code independently.

# Check: p6_lirf_regime_hedge_eval

Exploratory post-hoc evaluation (not an experiment) of a three-regime hedge for LIRF NM-unmatched departures on the EXP-031 Jan/Jul 2025 hold-outs. Regime probabilities and regime means estimated on the 11 other 2025 months; prediction = p_echo*d_sched + p_dayminus*mean(y|dayminus) + p_normal*mean(y|normal). Squared error expressed as % of the total EXP-031 hold-out squared error (Jan+Jul). Caveat: the band edges (3/6/14 h) were chosen after viewing all 2025 months incl. the hold-outs. Script: scratchpad q9.py (regime SQL in p6_lirf_unmatched_regimes_by_band).

| fold   | band    |   n_train |   p_echo |   p_dayminus |   n_hold |   se_exp031_pct_total |   se_rule_pct_total |   se_blend50_pct_total |
|:-------|:--------|----------:|---------:|-------------:|---------:|----------------------:|--------------------:|-----------------------:|
| jan    | 1 3-6h  |       177 |    0.627 |        0.006 |        3 |                  0.1  |                0.28 |                   0.18 |
| jan    | 2 6-14h |        40 |    0.975 |        0     |        3 |                  0.34 |                0.01 |                   0.1  |
| jan    | 3 >=14h |        18 |    0.444 |        0.556 |        2 |                  2.66 |                1    |                   1.33 |
| jul    | 1 3-6h  |       121 |    0.694 |        0.008 |       59 |                  6.22 |                6.4  |                   5.74 |
| jul    | 2 6-14h |        32 |    0.969 |        0     |       11 |                  4.57 |                0.03 |                   0.99 |
| jul    | 3 >=14h |        15 |    0.533 |        0.467 |        5 |                  5.86 |                0.96 |                   2.29 |

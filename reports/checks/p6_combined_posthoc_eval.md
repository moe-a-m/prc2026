# Check: p6_combined_posthoc_eval

Exploratory (not an EXP): rules R1-R3 applied to EXP-031 Jan/Jul 2025 hold-out predictions. All probabilities/means/classifiers are fit on the 11 other 2025 months. R1: LIRF NM-unmatched, d_sched >= 6 h: p_echo*d_sched + p_dayminus*mean(y|dayminus) + p_normal*mean(y|normal) in bands [6,14) h and >= 14 h. R2: LIRF NM-unmatched, 1-6 h: average of EXP-031 and p_echo*d_sched + (1-p_echo)*mean(y|not echo), p_echo from a HistGradientBoostingClassifier (d_sched, hour, schedule minute, MVT sec==0, carrier prefix, flight-number class, stand). R3: NM-matched, proxy not suspect (AOBT_3 present, |AOBT_3-EOBT_1|<=1 h, AOBT_3 <= MVT), d_sched > 3 h: clip prediction to MVT-AOBT_3 ± 1800 s. Band edges were chosen after viewing all 2025 months (optimistic). Script: scratchpad q31.py.

| fold   |      n |   rmse_exp031 |   rmse_rules |
|:-------|-------:|--------------:|-------------:|
| jan    | 153706 |        347.72 |       339.28 |
| jul    | 190713 |        361.72 |       298.42 |
| all    | 344419 |        355.54 |       317.3  |

| fold   | rule                                    |      n |   sse_exp031 |   sse_rules |
|:-------|:----------------------------------------|-------:|-------------:|------------:|
| jan    | R1 LIRF-unm >=6h regime hedge           |      5 |    1.302e+09 |   4.372e+08 |
| jan    | R2 LIRF-unm 1-6h classifier hedge (avg) |     49 |    2.561e+08 |   2.369e+08 |
| jan    | R3 matched >3h clip to proxy ±30min     |   1044 |    9.977e+07 |   9.296e+07 |
| jan    | unchanged                               | 152608 |    1.693e+10 |   1.693e+10 |
| jul    | R1 LIRF-unm >=6h regime hedge           |     16 |    4.538e+09 |   4.311e+08 |
| jul    | R2 LIRF-unm 1-6h classifier hedge (avg) |    305 |    4.207e+09 |   3.281e+09 |
| jul    | R3 matched >3h clip to proxy ±30min     |   1632 |    3.443e+09 |   5.064e+08 |
| jul    | unchanged                               | 188760 |    1.276e+10 |   1.276e+10 |

## Concentration of the gain (squared-error reduction per row)

| fold   | rule                                    |    n |   n_improved |   n_worse |   total_gain |   top5_share_of_gain | airports                                          |
|:-------|:----------------------------------------|-----:|-------------:|----------:|-------------:|---------------------:|:--------------------------------------------------|
| jan    | R1 LIRF-unm >=6h regime hedge           |    5 |            4 |         1 |    8.652e+08 |                1     | LIRF                                              |
| jan    | R2 LIRF-unm 1-6h classifier hedge (avg) |   49 |           24 |        25 |    1.925e+07 |                1.819 | LIRF                                              |
| jan    | R3 matched >3h clip to proxy ±30min     | 1044 |            1 |         1 |    6.805e+06 |                1.008 | EDDF,EDDM,EGLL,EHAM,LEBL,LEMD,LFPG,LIRF,LSZH,LTFM |
| jul    | R1 LIRF-unm >=6h regime hedge           |   16 |           14 |         2 |    4.107e+09 |                0.64  | LIRF                                              |
| jul    | R2 LIRF-unm 1-6h classifier hedge (avg) |  305 |          153 |       152 |    9.257e+08 |                0.704 | LIRF                                              |
| jul    | R3 matched >3h clip to proxy ±30min     | 1632 |           42 |         4 |    2.937e+09 |                0.803 | EDDF,EDDM,EGLL,EHAM,LEBL,LEMD,LFPG,LIRF,LSZH,LTFM |

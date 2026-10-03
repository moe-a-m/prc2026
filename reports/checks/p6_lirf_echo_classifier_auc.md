# Check: p6_lirf_echo_classifier_auc

Leave-one-month-out HistGradientBoostingClassifier (sklearn, depth 3, 100 iter) predicting echo (|y-d_sched|<=120 s) for LIRF NM-unmatched 2025 departures 1-6 h late (n=1312, echo rate 0.476). Inputs: d_sched, take-off hour, schedule minute, MVT second==0, carrier prefix, flight-number class, numeric stand.

- AUC (month-held-out) = 0.867
- AUC of d_sched alone = 0.661
- Brier = 0.1493 vs constant-rate Brier = 0.2494

## Hedge with classifier probability on the EXP-031 hold-out rows of this population

hedge = p_echo*d_sched + (1-p_echo)*mean(y | not echo, other months). % of total EXP-031 Jan+Jul hold-out squared error.

| fold   |   n | method               |   pct_total_sq_err |
|:-------|----:|:---------------------|-------------------:|
| jan    |  49 | EXP-031              |               0.59 |
| jan    |  49 | classifier hedge     |               0.61 |
| jan    |  49 | mean(EXP-031, hedge) |               0.54 |
| jul    | 305 | EXP-031              |               9.66 |
| jul    | 305 | classifier hedge     |               7.67 |
| jul    | 305 | mean(EXP-031, hedge) |               7.54 |

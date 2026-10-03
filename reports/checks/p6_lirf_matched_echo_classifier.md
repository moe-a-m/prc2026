# Check: p6_lirf_matched_echo_classifier

LIRF NM-matched 2025 departures with NM delay > 10 min (n=71864, echo rate 0.092). Leave-one-month-out HistGradientBoostingClassifier (depth 4, 200 iter) on nm_delay, d_sched, MVT-AOBT_3, MVT second==0, mangled flight number, NM operator, stand, take-off hour, runway.

- AUC (month-held-out) = 0.839; AUC of nm_delay alone = 0.622

Hedge = p*d_sched + (1-p)*(MVT-AOBT_3 + median non-echo residual of other months), on EXP-031 hold-out rows of this population; % of total EXP-031 Jan+Jul squared error.

| fold   |    n | method               |   pct_total_sq_err |
|:-------|-----:|:---------------------|-------------------:|
| jan    | 3561 | EXP-031              |              1.582 |
| jan    | 3561 | classifier hedge     |              2.271 |
| jan    | 3561 | mean(EXP-031, hedge) |              1.662 |
| jul    | 9514 | EXP-031              |             10.275 |
| jul    | 9514 | classifier hedge     |             12.311 |
| jul    | 9514 | mean(EXP-031, hedge) |              8.881 |

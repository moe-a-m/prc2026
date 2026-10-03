# Check: p6_error_budget_EXP-031

Squared-error budget of EXP-031 on the Jan+Jul 2025 hold-outs by data-quality category (categories overlap; 'regular' = none of A-F). Script: scripts/explore/p6_error_budget.py.

| category                             |      n |   pct_rows |   pct_sq_err |   rmse |
|:-------------------------------------|-------:|-----------:|-------------:|-------:|
| A unmatched NM                       |   5366 |       1.56 |         51.7 |   2047 |
| B echo: |BLOCK-SCHED|<=10s & late>1h |    344 |       0.1  |         13.4 |   4113 |
| C day-shift: y>20h                   |      7 |       0    |         28.6 |  42178 |
| D y in (3h,20h]                      |     53 |       0.02 |         14.3 |  10824 |
| E matched, NM proxy off by >1h       |    473 |       0.14 |          3.5 |   1790 |
| F label <= 0                         |     83 |       0.02 |          0.1 |    699 |
| G ADES mvt!=flt (wrong NM join?)     |   4832 |       1.4  |          0.9 |    281 |
| H aircraft type mvt!=flt             |   1234 |       0.36 |          0.3 |    311 |
| I minute-rounded block               |  22119 |       6.42 |         22   |    657 |
| regular (none of A-F)                | 338428 |      98.26 |         39.5 |    226 |

## % of total squared error by airport × category

| airport   |   A_unmatched | C_dayshift   |   E_proxy_off |   other |
|:----------|--------------:|:-------------|--------------:|--------:|
| EDDF      |           0.1 | <NA>         |           0.1 |     2.6 |
| EDDM      |           0.2 | <NA>         |           0.1 |     1.6 |
| EGLL      |           1.4 | <NA>         |           0.4 |     4.6 |
| EHAM      |           0.6 | <NA>         |           0.1 |     2.7 |
| LEBL      |           0.1 | <NA>         |           0   |     3.1 |
| LEMD      |           0   | <NA>         |           0   |     2.4 |
| LFPG      |          24.1 | <NA>         |           0.4 |     5   |
| LIRF      |          24   | 4.2          |           1.7 |    11.3 |
| LSZH      |           0.6 | <NA>         |           0.3 |     1.4 |
| LTFM      |           0.4 | <NA>         |           0.3 |     5.9 |

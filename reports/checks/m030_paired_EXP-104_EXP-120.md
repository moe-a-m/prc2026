# Check: m030_paired_EXP-104_EXP-120

Hold-out RMSE by group, EXP-104 = reference (M-030, docs/METHODS.md). Script: scripts/checks/m030_paired.py.

| fold   | group               |   EXP-104 |   EXP-120 |
|:-------|:--------------------|----------:|----------:|
| jan    | LIRF matched y≤3h   |    291.12 |    289.22 |
| jan    | LIRF unmatched y≤3h |   2636.81 |   2552.96 |
| jan    | LIRF y>3h           |  17340.9  |  19538.1  |
| jan    | all                 |    356.51 |    359.54 |
| jan    | non-LIRF y>3h       |  58767.2  |  58836.8  |
| jan    | non-LIRF y≤3h       |    200.92 |    196.99 |
| jul    | LIRF matched y≤3h   |    461.75 |    465.97 |
| jul    | LIRF unmatched y≤3h |   3452.33 |   3371.66 |
| jul    | LIRF y>3h           |  14486.3  |  13988.7  |
| jul    | all                 |    367.45 |    359.14 |
| jul    | non-LIRF y>3h       |   8479.54 |   8203.84 |
| jul    | non-LIRF y≤3h       |    226.72 |    222.03 |

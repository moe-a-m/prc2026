# Check: m030_paired_EXP-091_EXP-104

Hold-out RMSE by group, EXP-091 = reference (M-030, docs/METHODS.md). Script: scripts/checks/m030_paired.py.

| fold   | group               |   EXP-091 |   EXP-104 |
|:-------|:--------------------|----------:|----------:|
| jan    | LIRF matched y≤3h   |    290.43 |    291.12 |
| jan    | LIRF unmatched y≤3h |   2540.85 |   2636.81 |
| jan    | LIRF y>3h           |  17520.7  |  17340.9  |
| jan    | all                 |    357.2  |    356.51 |
| jan    | non-LIRF y>3h       |  58771.1  |  58767.2  |
| jan    | non-LIRF y≤3h       |    201.98 |    200.92 |
| jul    | LIRF matched y≤3h   |    464.03 |    461.75 |
| jul    | LIRF unmatched y≤3h |   3343.47 |   3452.33 |
| jul    | LIRF y>3h           |  14524.3  |  14486.3  |
| jul    | all                 |    367.74 |    367.45 |
| jul    | non-LIRF y>3h       |   8550.61 |   8479.54 |
| jul    | non-LIRF y≤3h       |    228.83 |    226.72 |

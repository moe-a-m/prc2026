# Check: m030_paired_EXP-118_EXP-134

Hold-out RMSE by group, EXP-118 = reference (M-030, docs/METHODS.md). Script: scripts/checks/m030_paired.py.

| fold   | group               |   EXP-118 |   EXP-134 |
|:-------|:--------------------|----------:|----------:|
| jan    | LIRF matched y≤3h   |    288.12 |    287.73 |
| jan    | LIRF unmatched y≤3h |   2354.23 |   2369.58 |
| jan    | LIRF y>3h           |   8302.74 |   8326.4  |
| jan    | all                 |    334.18 |    333.78 |
| jan    | non-LIRF y>3h       |  58798.8  |  58822.2  |
| jan    | non-LIRF y≤3h       |    188.94 |    187.94 |
| jul    | LIRF matched y≤3h   |    502.84 |    505.71 |
| jul    | LIRF unmatched y≤3h |   3689.11 |   3703.56 |
| jul    | LIRF y>3h           |   4253.99 |   4283.27 |
| jul    | all                 |    300.76 |    301.32 |
| jul    | non-LIRF y>3h       |   6102.47 |   6097.22 |
| jul    | non-LIRF y≤3h       |    220.79 |    220.5  |

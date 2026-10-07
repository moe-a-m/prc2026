# Check: m030_paired_EXP-101_EXP-118

Hold-out RMSE by group, EXP-101 = reference (M-030, docs/METHODS.md). Script: scripts/checks/m030_paired.py.

| fold   | group               |   EXP-101 |   EXP-118 |
|:-------|:--------------------|----------:|----------:|
| jan    | LIRF matched y≤3h   |    288.81 |    288.12 |
| jan    | LIRF unmatched y≤3h |   2385.54 |   2354.23 |
| jan    | LIRF y>3h           |   8297.94 |   8302.74 |
| jan    | all                 |    334.48 |    334.18 |
| jan    | non-LIRF y>3h       |  58739.6  |  58798.8  |
| jan    | non-LIRF y≤3h       |    189.67 |    188.94 |
| jul    | LIRF matched y≤3h   |    500.02 |    502.84 |
| jul    | LIRF unmatched y≤3h |   3657.59 |   3689.11 |
| jul    | LIRF y>3h           |   4277.17 |   4253.99 |
| jul    | all                 |    300.98 |    300.76 |
| jul    | non-LIRF y>3h       |   6286.54 |   6102.47 |
| jul    | non-LIRF y≤3h       |    222.31 |    220.79 |

# Check: m030_paired_EXP-103_EXP-119

Hold-out RMSE by group, EXP-103 = reference (M-030, docs/METHODS.md). Script: scripts/checks/m030_paired.py.

| fold   | group               |   EXP-103 |   EXP-119 |
|:-------|:--------------------|----------:|----------:|
| jan    | LIRF matched y≤3h   |    313.82 |    311.43 |
| jan    | LIRF unmatched y≤3h |   2416.7  |   2364.88 |
| jan    | LIRF y>3h           |  10389.2  |  10177    |
| jan    | all                 |    348.04 |    344.99 |
| jan    | non-LIRF y>3h       |  58862.7  |  58863.8  |
| jan    | non-LIRF y≤3h       |    206.14 |    201.58 |
| jul    | LIRF matched y≤3h   |    614.91 |    614.91 |
| jul    | LIRF unmatched y≤3h |   3905.31 |   3905.31 |
| jul    | LIRF y>3h           |  12478.1  |  12478.1  |
| jul    | all                 |    377.08 |    374.91 |
| jul    | non-LIRF y>3h       |   8591.88 |   8667.15 |
| jul    | non-LIRF y≤3h       |    232.67 |    228.79 |

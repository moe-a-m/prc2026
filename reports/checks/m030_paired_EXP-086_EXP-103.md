# Check: m030_paired_EXP-086_EXP-103

Hold-out RMSE by group, EXP-086 = reference (M-030, docs/METHODS.md). Script: scripts/checks/m030_paired.py.

| fold   | group               |   EXP-086 |   EXP-103 |
|:-------|:--------------------|----------:|----------:|
| jan    | LIRF matched y≤3h   |    311.71 |    313.82 |
| jan    | LIRF unmatched y≤3h |   2443.04 |   2416.7  |
| jan    | LIRF y>3h           |   9937.43 |  10389.2  |
| jan    | all                 |    346.99 |    348.04 |
| jan    | non-LIRF y>3h       |  58694.8  |  58862.7  |
| jan    | non-LIRF y≤3h       |    206.47 |    206.14 |
| jul    | LIRF matched y≤3h   |    627.25 |    614.91 |
| jul    | LIRF unmatched y≤3h |   3785.38 |   3905.31 |
| jul    | LIRF y>3h           |  12432    |  12478.1  |
| jul    | all                 |    377.37 |    377.08 |
| jul    | non-LIRF y>3h       |   8670.59 |   8591.88 |
| jul    | non-LIRF y≤3h       |    234.3  |    232.67 |

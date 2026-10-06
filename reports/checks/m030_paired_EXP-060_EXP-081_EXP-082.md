# Check: m030_paired_EXP-060_EXP-081_EXP-082

Hold-out RMSE by group, EXP-060 = reference (M-030, docs/METHODS.md). Script: scripts/checks/m030_paired.py.

| fold   | group               |   EXP-060 |   EXP-081 |   EXP-082 |
|:-------|:--------------------|----------:|----------:|----------:|
| jan    | LIRF matched y≤3h   |    311.71 |    292.41 |    297.19 |
| jan    | LIRF unmatched y≤3h |   2443.04 |   1806.03 |   2099.93 |
| jan    | LIRF y>3h           |   9937.43 |  41994.6  |  37910.2  |
| jan    | all                 |    347.26 |    441.15 |    424.47 |
| jan    | non-LIRF y>3h       |  58695.6  |  58695.9  |  58694.8  |
| jan    | non-LIRF y≤3h       |    206.96 |    206.94 |    206.47 |
| jul    | LIRF matched y≤3h   |    627.25 |    480.68 |    478.41 |
| jul    | LIRF unmatched y≤3h |   3785.38 |   2387.86 |   2837.75 |
| jul    | LIRF y>3h           |  12432    |  33502.9  |  30627.4  |
| jul    | all                 |    378.91 |    595.88 |    559.51 |
| jul    | non-LIRF y>3h       |   8553.36 |   8871.66 |   8670.59 |
| jul    | non-LIRF y≤3h       |    237.06 |    234.19 |    234.3  |

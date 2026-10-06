# Check: m030_paired_EXP-083_EXP-084_EXP-085

Hold-out RMSE by group, EXP-083 = reference (M-030, docs/METHODS.md). Script: scripts/checks/m030_paired.py.

| fold   | group               |   EXP-083 |   EXP-084 |   EXP-085 |
|:-------|:--------------------|----------:|----------:|----------:|
| jan    | LIRF matched y≤3h   |    311.71 |    292.41 |    297.19 |
| jan    | LIRF unmatched y≤3h |   2443.04 |   1806.03 |   2099.93 |
| jan    | LIRF y>3h           |   8337.75 |  10030.4  |   8992.96 |
| jan    | all                 |    345.34 |    344.79 |    344.1  |
| jan    | non-LIRF y>3h       |  58695.6  |  58695.9  |  58694.8  |
| jan    | non-LIRF y≤3h       |    206.96 |    206.94 |    206.47 |
| jul    | LIRF matched y≤3h   |    627.25 |    480.68 |    478.41 |
| jul    | LIRF unmatched y≤3h |   3785.38 |   2387.86 |   2837.75 |
| jul    | LIRF y>3h           |   6482.91 |  14523.6  |  12888.6  |
| jul    | all                 |    340.36 |    361.16 |    350.45 |
| jul    | non-LIRF y>3h       |   8553.36 |   8871.66 |   8670.59 |
| jul    | non-LIRF y≤3h       |    237.06 |    234.19 |    234.3  |

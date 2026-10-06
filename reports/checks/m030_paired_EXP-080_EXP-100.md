# Check: m030_paired_EXP-080_EXP-100

Hold-out RMSE by group, EXP-080 = reference (M-030, docs/METHODS.md). Script: scripts/checks/m030_paired.py.

| fold   | group               |   EXP-080 |   EXP-100 |
|:-------|:--------------------|----------:|----------:|
| jan    | LIRF matched y≤3h   |    288.78 |    288.86 |
| jan    | LIRF unmatched y≤3h |   2386.16 |   2385.54 |
| jan    | LIRF y>3h           |   8298.16 |   8297.94 |
| jan    | all                 |    335.46 |    335.43 |
| jan    | non-LIRF y>3h       |  58740.5  |  58739.6  |
| jan    | non-LIRF y≤3h       |    191.53 |    191.48 |
| jul    | LIRF matched y≤3h   |    551.32 |    553.58 |
| jul    | LIRF unmatched y≤3h |   3653.99 |   3659.76 |
| jul    | LIRF y>3h           |   7711.38 |   7659.79 |
| jul    | all                 |    326.29 |    325.4  |
| jul    | non-LIRF y>3h       |   8491.2  |   8634.3  |
| jul    | non-LIRF y≤3h       |    224.87 |    223.21 |

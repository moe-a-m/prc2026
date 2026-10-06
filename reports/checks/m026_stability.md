# Check: m026_stability

M-026 regime shares (airports ['LIRF'], NM-unmatched, bands [(21600, 50400), (50400, None)]).

## Pooled 2025 shares with 95% Wilson intervals

| airport   |   band | regime    |   n |   k |   share |   ci_low |   ci_high |
|:----------|-------:|:----------|----:|----:|--------:|---------:|----------:|
| LIRF      |      0 | echo      |  43 |  42 |   0.977 |    0.879 |     0.996 |
| LIRF      |      0 | day_minus |  43 |   0 |   0     |    0     |     0.082 |
| LIRF      |      0 | normal    |  43 |   1 |   0.023 |    0.004 |     0.121 |
| LIRF      |      1 | echo      |  20 |   9 |   0.45  |    0.258 |     0.658 |
| LIRF      |      1 | day_minus |  20 |  11 |   0.55  |    0.342 |     0.742 |
| LIRF      |      1 | normal    |  20 |   0 |   0     |    0     |     0.161 |

## Per month

| airport   |   band | ym      |   n |   echo |   dm |   normal |
|:----------|-------:|:--------|----:|-------:|-----:|---------:|
| LIRF      |      0 | 2025-01 |   3 |      3 |    0 |        0 |
| LIRF      |      0 | 2025-02 |   2 |      2 |    0 |        0 |
| LIRF      |      0 | 2025-04 |   2 |      2 |    0 |        0 |
| LIRF      |      0 | 2025-05 |   1 |      1 |    0 |        0 |
| LIRF      |      0 | 2025-06 |   5 |      5 |    0 |        0 |
| LIRF      |      0 | 2025-07 |  11 |     11 |    0 |        0 |
| LIRF      |      0 | 2025-08 |   8 |      7 |    0 |        1 |
| LIRF      |      0 | 2025-09 |   5 |      5 |    0 |        0 |
| LIRF      |      0 | 2025-10 |   1 |      1 |    0 |        0 |
| LIRF      |      0 | 2025-11 |   2 |      2 |    0 |        0 |
| LIRF      |      0 | 2025-12 |   3 |      3 |    0 |        0 |
| LIRF      |      1 | 2025-01 |   2 |      1 |    1 |        0 |
| LIRF      |      1 | 2025-02 |   1 |      1 |    0 |        0 |
| LIRF      |      1 | 2025-03 |   1 |      0 |    1 |        0 |
| LIRF      |      1 | 2025-04 |   1 |      1 |    0 |        0 |
| LIRF      |      1 | 2025-06 |   1 |      0 |    1 |        0 |
| LIRF      |      1 | 2025-07 |   5 |      1 |    4 |        0 |
| LIRF      |      1 | 2025-08 |   2 |      2 |    0 |        0 |
| LIRF      |      1 | 2025-09 |   4 |      3 |    1 |        0 |
| LIRF      |      1 | 2025-11 |   2 |      0 |    2 |        0 |
| LIRF      |      1 | 2025-12 |   1 |      0 |    1 |        0 |

## Ranking rows hedged: 26 (bands: {0: 20, 1: 6})

Expected extra squared error on these rows if the 2026 echo share differs from 2025 by the shift (other regimes rescaled), and the implied board RMSE change at board 278.54 over 344841 rows:

| echo_share_shift                                          |   delta_sse |   board_rmse_delta |
|:----------------------------------------------------------|------------:|-------------------:|
| -0.3                                                      |  7892254027 |             38.432 |
| -0.2                                                      |  5261502685 |             26.16  |
| -0.1                                                      |  2630751342 |             13.373 |
| 0.0                                                       |           0 |              0     |
| 0.1                                                       |  -520251941 |             -2.721 |
| 0.2                                                       |  -456565421 |             -2.387 |
| 0.3                                                       |  -392878901 |             -2.053 |
| both bands at the Wilson lower end {0: -0.098, 1: -0.192} |  2518270987 |             12.814 |
| both bands at the Wilson upper end {0: 0.019, 1: 0.208}   |  -111618315 |             -0.582 |

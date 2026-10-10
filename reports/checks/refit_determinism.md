# Base-model refit determinism

Base-model refit determinism (2026-10-10). repro-final-1 (clean clone of e8a3773) reproduced the final file except
48,731 EHAM rows; its model inputs were identical (db_determinism.md). Each final-fit member (EXP-103–112, Modal runs
fin-*, CatBoost on 4 CPUs) was refit on a fresh 2-CPU container (EXP-151–160, runs det-*-2cpu) and compared per
airport with the original prediction of the ranking set.

## Per member

| family   |   seed | final fit   | refit   | status   |   rows |   rows differing |   max |d| (s) |   rms d (s) |
|:---------|-------:|:------------|:--------|:---------|-------:|-----------------:|--------------:|------------:|
| lgb      |     42 | EXP-103     | EXP-151 | ok       | 670790 |                0 |             0 |           0 |
| cat      |     42 | EXP-104     | EXP-152 | ok       | 670790 |                0 |             0 |           0 |
| lgb      |      7 | EXP-105     | EXP-153 | ok       | 670790 |                0 |             0 |           0 |
| lgb      |     99 | EXP-106     | EXP-154 | ok       | 670790 |                0 |             0 |           0 |
| lgb      |     11 | EXP-107     | EXP-155 | ok       | 670790 |                0 |             0 |           0 |
| lgb      |     23 | EXP-108     | EXP-156 | ok       | 670790 |                0 |             0 |           0 |
| cat      |      7 | EXP-109     | EXP-157 | ok       | 670790 |                0 |             0 |           0 |
| cat      |     99 | EXP-110     | EXP-158 | ok       | 670790 |                0 |             0 |           0 |
| cat      |     11 | EXP-111     | EXP-159 | ok       | 670790 |                0 |             0 |           0 |
| cat      |     23 | EXP-112     | EXP-160 | ok       | 670790 |                0 |             0 |           0 |

## Airports with differing rows

none

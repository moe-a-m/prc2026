# Final-file clean-clone reproduction

Clean-clone reproduction of the final file, member by member (2026-10-11). repro-final-2 (Modal, clean clone of
56c5e76, 2 CPUs, `scripts/modal/reproduce.sh`) ran verify-raw → ingest → clean → features → train → predict →
submit-check from the raw files and kept every member's ranking prediction. Each stage EXP-103–118 is compared per
airport with the original (final fits EXP-103–112 of 2026-10-08, post-chain EXP-113–118 of build-final-1).

## Run log

```
commit 56c5e76, status: 0 changed files
avx avx2 avx512_bitalg avx512_vbmi2 avx512_vnni avx512_vpopcntdq avx512bw avx512cd avx512dq avx512f avx512vbmi avx512vl fma sse4_1 sse4_2 sse4a 
elapsed 20276 s
2bb107fcb72e0ad0d922d5f35cb8a8279b984caf0835a2d5b5b8d3bc8c00d7fa  submissions/motivated-engine_final.parquet
```

## Per stage

| stage   | step                    | status   |   rows |   rows differing |   max |d| (s) |   rms d (s) |
|:--------|:------------------------|:---------|-------:|-----------------:|--------------:|------------:|
| EXP-103 | lgb s42                 | ok       | 670790 |                0 |             0 |           0 |
| EXP-104 | cat s42                 | ok       | 670790 |                0 |             0 |           0 |
| EXP-105 | lgb s7                  | ok       | 670790 |                0 |             0 |           0 |
| EXP-106 | lgb s99                 | ok       | 670790 |                0 |             0 |           0 |
| EXP-107 | lgb s11                 | ok       | 670790 |                0 |             0 |           0 |
| EXP-108 | lgb s23                 | ok       | 670790 |                0 |             0 |           0 |
| EXP-109 | cat s7                  | ok       | 670790 |                0 |             0 |           0 |
| EXP-110 | cat s99                 | ok       | 670790 |                0 |             0 |           0 |
| EXP-111 | cat s11                 | ok       | 670790 |                0 |             0 |           0 |
| EXP-112 | cat s23                 | ok       | 670790 |                0 |             0 |           0 |
| EXP-113 | LightGBM 5-seed average | ok       | 670790 |                0 |             0 |           0 |
| EXP-114 | CatBoost 5-seed average | ok       | 670790 |                0 |             0 |           0 |
| EXP-115 | blend                   | ok       | 670790 |                0 |             0 |           0 |
| EXP-116 | three-regime hedge      | ok       | 670790 |                0 |             0 |           0 |
| EXP-117 | ADS-B step              | ok       | 670790 |                0 |             0 |           0 |
| EXP-118 | LOBT window             | ok       | 670790 |                0 |             0 |           0 |

## Airports with differing rows

none

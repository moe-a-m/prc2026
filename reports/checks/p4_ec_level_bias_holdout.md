# Check: p4_ec_level_bias_holdout

Run at 2026-10-02T16:54:31+00:00 (UTC), duckdb 1.5.6.

Computed in Python from models/oof/EXP-022_{jan,jul}.parquet joined to feat_dep_ec (rows y ≤ 2 h): per airport-month mean-prediction bias ranges −21…+36 s; bias² is 0.14% (Jan) / 0.30% (Jul) of hold-out MSE. A EUROCONTROL-informed level recalibration can therefore gain at most ≈0.5 RMSE on 2025 hold-outs; not pursued.

```sql
SELECT 'see note' AS info
```

1 rows

| info     |
|:---------|
| see note |

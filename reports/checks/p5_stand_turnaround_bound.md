# Is the last ARR in-block at the same stand a hard upper bound on taxi-out? (2026-10-08)

Hypothesis: when the latest ARR in-block at the departure's stand comes after the previous departure from that stand (`gap_arr_stand_1 < gap_prev_dep_stand`), that arrival is the departure's own inbound, so off-block ≥ in-block, i.e. y ≤ gap_arr_stand_1. If it held, it could be a projection rule like M-031.

Training rows (2025, `feat_dep`, ds='train', stand not null). n_own = rows meeting the condition; viol_own = rows with y > gap_arr_stand_1; viol_own600 = y > gap_arr_stand_1 + 600 s; *_um = NM-unmatched subset.

```sql
with d as (select airport, y, gap_arr_stand_1 g1, gap_prev_dep_stand gd, f_no_nm_match um from feat_dep where ds='train' and y is not null and stand is not null)
select airport, count(*) n,
  count(*) filter (where g1 is not null and (gd is null or g1<gd)) n_own,
  count(*) filter (where g1 is not null and (gd is null or g1<gd) and y>g1) viol_own,
  count(*) filter (where g1 is not null and (gd is null or g1<gd) and y>g1+600) viol_own600,
  count(*) filter (where um and g1 is not null and (gd is null or g1<gd)) n_own_um,
  count(*) filter (where um and g1 is not null and (gd is null or g1<gd) and y>g1) viol_own_um
from d group by all order by airport
```

```
  airport       n   n_own  viol_own  viol_own600  n_own_um  viol_own_um
0    EDDF  230141  183139     25672        11866      1589          166
1    EDDM  167334  140062     14830         4683       826           85
2    EGLL  239542  188725     62644        41590      1114          348
3    EHAM  247951  212463     18761         6673      3429          227
4    LEBL  179705  166790     10751         6199      1705          145
5    LEMD  212242  197023      8256         5585       867           31
6    LFPG  239538  208599     16915         9393      3347          260
7    LIRF  160694  149961      7024         6208      1360          507
8    LSZH  134907  113990     10773         3709      1650          147
9    LTFM  272965  244007     27826        15783      3223          472
```

Verdict: not a hard bound. Off-block precedes the last stand arrival in 4–33% of qualifying rows (EGLL 33%, LIRF 5%), also by more than 10 min (2–22%). Stand records are not exclusive (towing, shared or reassigned stands). No projection rule built; the information stays a model input (M-009).

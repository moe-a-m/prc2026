# Snow / freezing days in the full-year hold-outs (final recipe, variant A)

Prompted by a forum question (10/10/2026 07:05: "February brings de-icing and snow
days. For flights without an NM off-block time on those days, did anything beat the base model?"). Descriptive check
only, no model change. Weather flags from stg_metar (M-012: wx_snow = SN|SG|PL, wx_freezing = FZ in IEM wxcodes):

  wx3h      snow or freezing reported in the 3 h before take-off (feat_dep_wx.wx3h_snow / wx3h_freezing)
  wx_day    no such report in those 3 h, but one at the airport on the same UTC day
  dry       no snow/freezing report at the airport that UTC day

NM off-block status (M-004, feat_dep.d_aobt3, feat_dep_nm.aobt3_at_default):
  no_aobt3        AOBT_3_flt missing
  aobt3_default   MVT − AOBT_3 on the NM default taxi minute (little off-block information)
  aobt3_info      AOBT_3 present and off the default

Scope: hold-out months Nov–Mar 2025 (the snow season; nearly all wx rows fall there). bias = mean(pred − y).

  PRC_HOLDOUTS=all python scripts/checks/winter_snow_days.py      -> reports/checks/winter_snow_days.md

- data: 0fa06e7739b1, git: f3211d6-dirty
- rows: 789896 (Nov–Mar hold-outs)

## Days with any snow/freezing report, per airport and hold-out month

| airport   |   nov |   dec |   jan |   feb |   mar |
|:----------|------:|------:|------:|------:|------:|
| EDDF      |     2 |     2 |     8 |     4 |     0 |
| EDDM      |    13 |    16 |    12 |     9 |     4 |
| EGLL      |     1 |     1 |     4 |     0 |     0 |
| EHAM      |     4 |     2 |    12 |     6 |     4 |
| LEMD      |     0 |     1 |     1 |     0 |     2 |
| LFPG      |     4 |     1 |     8 |     3 |     0 |
| LSZH      |     9 |     7 |     8 |     4 |     0 |
| LTFM      |     0 |     4 |     0 |    13 |     2 |

## Nov–Mar, all airports: weather × NM status

|                             |      n |   rmse |    bias |   mean_y |   share_sq_err_% |
|:----------------------------|-------:|-------:|--------:|---------:|-----------------:|
| ('wx3h', 'no_aobt3')        |    732 | 1988.8 | -1017.5 |   2636.7 |              6.3 |
| ('wx3h', 'aobt3_default')   |   3613 |  365.5 |   -66.7 |   1004.5 |              1   |
| ('wx3h', 'aobt3_info')      |  18145 |  461.5 |   -87.3 |   1424.3 |              8.4 |
| ('wx_day', 'no_aobt3')      |    708 |  501.9 |    -8.9 |    945.5 |              0.4 |
| ('wx_day', 'aobt3_default') |  13513 |  132   |    -2.9 |    793.7 |              0.5 |
| ('wx_day', 'aobt3_info')    |  46171 |  182   |    -3   |    977.9 |              3.3 |
| ('dry', 'no_aobt3')         |   5192 | 1674   |   -59.8 |   1407.6 |             31.5 |
| ('dry', 'aobt3_default')    | 151048 |  167.6 |    -0.3 |    916.9 |              9.2 |
| ('dry', 'aobt3_info')       | 550774 |  181.7 |    -1.7 |    998.3 |             39.4 |

## February only: weather × NM status

|                             |     n |   rmse |    bias |   mean_y |   share_sq_err_% |
|:----------------------------|------:|-------:|--------:|---------:|-----------------:|
| ('wx3h', 'no_aobt3')        |   282 | 2981.4 | -2300.7 |   4100.2 |             22.3 |
| ('wx3h', 'aobt3_default')   |  1267 |  566.2 |  -193.1 |   1360.7 |              3.6 |
| ('wx3h', 'aobt3_info')      |  6374 |  663.4 |  -226.4 |   1595.6 |             25   |
| ('wx_day', 'no_aobt3')      |    99 |  354.5 |    25.5 |    752.1 |              0.1 |
| ('wx_day', 'aobt3_default') |  2889 |  136.9 |    -5.8 |    786.8 |              0.5 |
| ('wx_day', 'aobt3_info')    |  9082 |  172.1 |    -4.4 |    925.9 |              2.4 |
| ('dry', 'no_aobt3')         |   728 | 1386.8 |  -113.8 |   1496.8 |             12.5 |
| ('dry', 'aobt3_default')    | 24589 |  161.8 |    -0.6 |    881.5 |              5.7 |
| ('dry', 'aobt3_info')       | 98421 |  178.3 |    -4.2 |    990.6 |             27.9 |

## Nov–Mar, airports with snow/freezing days: airport × weather × (AOBT_3 missing?)

|                           |     n |   rmse |    bias |   mean_y |   share_sq_err_% |
|:--------------------------|------:|-------:|--------:|---------:|-----------------:|
| ('EDDF', 'wx3h', False)   |  1832 |  260.3 |   -34   |   1148.1 |              0.3 |
| ('EDDF', 'wx3h', True)    |    32 |  407.1 |   -75.5 |   1145.3 |              0   |
| ('EDDF', 'wx_day', False) |  6458 |  156.2 |     0.1 |    914.2 |              0.4 |
| ('EDDF', 'wx_day', True)  |   103 |  289   |    -5.7 |   1013.3 |              0   |
| ('EDDF', 'dry', False)    | 74877 |  136.1 |    -5.1 |    857.9 |              3.8 |
| ('EDDF', 'dry', True)     |   375 |  357.6 |   -11.2 |    947.2 |              0.1 |
| ('EDDM', 'wx3h', False)   |  5213 |  235.1 |   -16   |   1271.3 |              0.8 |
| ('EDDM', 'wx3h', True)    |   121 |  941.7 |  -476.7 |   1951.2 |              0.3 |
| ('EDDM', 'wx_day', False) | 15808 |  107.3 |    -4.2 |    849.1 |              0.5 |
| ('EDDM', 'wx_day', True)  |    75 |  333.5 |    47.5 |    972.5 |              0   |
| ('EDDM', 'dry', False)    | 37448 |   97.6 |    -8   |    789.2 |              1   |
| ('EDDM', 'dry', True)     |    92 |  276.2 |    52.8 |    797.2 |              0   |
| ('EGLL', 'wx3h', False)   |   586 |  358.5 |    58.6 |   1594   |              0.2 |
| ('EGLL', 'wx3h', True)    |    44 |  869.3 |   599.5 |   1520.2 |              0.1 |
| ('EGLL', 'wx_day', False) |  3110 |  270.1 |    11.7 |   1456.6 |              0.6 |
| ('EGLL', 'wx_day', True)  |    46 |  641.9 |   156.5 |   1349.7 |              0.1 |
| ('EGLL', 'dry', False)    | 91916 |  196.1 |     1   |   1342.1 |              9.6 |
| ('EGLL', 'dry', True)     |   348 |  684.8 |    16.9 |   1544.9 |              0.4 |
| ('EHAM', 'wx3h', False)   |  3908 |  208.1 |   -12.2 |   1074.7 |              0.5 |
| ('EHAM', 'wx3h', True)    |   133 |  780.5 |  -248.4 |   1329.4 |              0.2 |
| ('EHAM', 'wx_day', False) | 12415 |  141.7 |    -5.1 |    838.8 |              0.7 |
| ('EHAM', 'wx_day', True)  |   182 |  460.2 |   -74   |    669.6 |              0.1 |
| ('EHAM', 'dry', False)    | 77551 |  120.1 |    -4.4 |    790.5 |              3   |
| ('EHAM', 'dry', True)     |  1037 |  415.4 |    -6.3 |    539.1 |              0.5 |
| ('LEMD', 'wx3h', False)   |   145 |  168.8 |   -27.7 |   1026.5 |              0   |
| ('LEMD', 'wx_day', False) |  2042 |  155.2 |    -2.9 |    995   |              0.1 |
| ('LEMD', 'wx_day', True)  |     4 |   63.4 |    62.1 |    972.2 |              0   |
| ('LEMD', 'dry', False)    | 82472 |  151.2 |    -0.7 |   1002.2 |              5.1 |
| ('LEMD', 'dry', True)     |   187 |  264.4 |     1   |   1075.4 |              0   |
| ('LFPG', 'wx3h', False)   |  2042 |  470.3 |    -2.4 |   1851.9 |              1.2 |
| ('LFPG', 'wx3h', True)    |   108 | 1148   |  -226.1 |   2406.4 |              0.4 |
| ('LFPG', 'wx_day', False) |  7479 |  259.3 |     7.8 |   1158.2 |              1.4 |
| ('LFPG', 'wx_day', True)  |   140 |  508.7 |    -8.7 |   1307.9 |              0.1 |
| ('LFPG', 'dry', False)    | 81820 |  200.6 |     5.5 |    991.9 |              8.9 |
| ('LFPG', 'dry', True)     |   882 | 3453.3 |  -151.6 |   1347.8 |             28.5 |
| ('LSZH', 'wx3h', False)   |  2423 |  235.3 |   -17.1 |   1073.4 |              0.4 |
| ('LSZH', 'wx3h', True)    |    43 |  913.5 |  -286   |   1090.4 |              0.1 |
| ('LSZH', 'wx_day', False) |  6826 |  137   |    -6.2 |    758.6 |              0.3 |
| ('LSZH', 'wx_day', True)  |    93 |  819   |   -42.6 |    575.3 |              0.2 |
| ('LSZH', 'dry', False)    | 40005 |  130.5 |    -7   |    734.9 |              1.8 |
| ('LSZH', 'dry', True)     |   505 |  827.8 |   -17.2 |    560   |              0.9 |
| ('LTFM', 'wx3h', False)   |  5609 |  743.5 |  -287.9 |   1618.4 |              8.4 |
| ('LTFM', 'wx3h', True)    |   251 | 3149.8 | -2555   |   4409.8 |              6.8 |
| ('LTFM', 'wx_day', False) |  5546 |  220.1 |   -17.1 |   1033.8 |              0.7 |
| ('LTFM', 'wx_day', True)  |    65 |  284.2 |    30.1 |   1040.8 |              0   |
| ('LTFM', 'dry', False)    | 92707 |  207.6 |     3   |   1032.7 |             10.8 |
| ('LTFM', 'dry', True)     |  1115 |  385.5 |   -12.4 |   1038.1 |              0.4 |

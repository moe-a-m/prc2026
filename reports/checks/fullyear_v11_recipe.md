# Full-year hold-out check of the v11 recipe

Base: PRC_HOLDOUTS=all hold-out predictions of the v11 base models, 5-seed averages EXP-145 (LightGBM, EXP-135–139)
and EXP-146 (CatBoost, EXP-140–144). Two ways to apply the post-steps, reported per month and for Jan/Jul, Feb/Jun,
the other eight months and all twelve:

  A  frozen v11 parameters, as in the submission: blend weights from EXP-115, M-026 regime table fit on the training
     months without the hold-out month (as `hedge eval3`), ADS-B parameters from EXP-117, LOBT projection (M-031).
     The EXP-115 / EXP-117 parameters were fit on Jan + Jul 2025, so A is in-sample for those two months only.
  B  leave-one-month-out cross-fit chain EXP-147 (blend) → EXP-148 (hedge) → EXP-149 (ADS-B) → EXP-150 (LOBT).

  PRC_HOLDOUTS=all python scripts/checks/fullyear_summary.py      -> reports/checks/fullyear_v11_recipe.md

- data: 0fa06e7739b1, git: 70159d1-dirty

## RMSE per hold-out month and month group (s)

| months   |                n |   A frozen v11 parameters |   B leave-one-month-out refit |
|:---------|-----------------:|--------------------------:|------------------------------:|
| jan      | 153706           |                    334.35 |                        334.17 |
| feb      | 143731           |                    279.46 |                        279.55 |
| mar      | 164450           |                    183.9  |                        183.61 |
| apr      | 175288           |                    193.12 |                        193.43 |
| may      | 185202           |                    284.42 |                        284.13 |
| jun      | 183142           |                    297.61 |                        297.14 |
| jul      | 190713           |                    292.46 |                        290.64 |
| aug      | 191181           |                    249.07 |                        249.15 |
| sep      | 183951           |                    236.49 |                        236.54 |
| oct      | 185674           |                    207.66 |                        207.4  |
| nov      | 162332           |                    190.77 |                        190.33 |
| dec      | 165677           |                    194.85 |                        194.68 |
| Jan/Jul  | 344419           |                    311.85 |                        310.82 |
| Feb/Jun  | 326873           |                    289.77 |                        289.54 |
| other 8  |      1.41376e+06 |                    221.61 |                        221.5  |
| all 12   |      2.08505e+06 |                    250.06 |                        249.73 |

## Chain stages, variant B (RMSE, s)

|         |   EXP-145 |   EXP-146 |   EXP-147 |   EXP-148 |   EXP-149 |   EXP-150 |
|:--------|----------:|----------:|----------:|----------:|----------:|----------:|
| jan     |    346.5  |    356.2  |    348.45 |    339.07 |    335.17 |    334.17 |
| feb     |    328.89 |    332.1  |    329.05 |    284.93 |    280.76 |    279.55 |
| mar     |    207.54 |    204.77 |    202.77 |    193.83 |    187.09 |    183.61 |
| apr     |    200.85 |    199.37 |    196.59 |    198.78 |    193.54 |    193.43 |
| may     |    295.82 |    289.5  |    289.35 |    289.23 |    284.5  |    284.13 |
| jun     |    318.38 |    310.43 |    308.58 |    302.39 |    297.55 |    297.14 |
| jul     |    376.78 |    362.78 |    349.89 |    330.11 |    326.43 |    290.64 |
| aug     |    293.18 |    247.27 |    260.05 |    254.3  |    249.59 |    249.15 |
| sep     |    284.39 |    276.42 |    274.7  |    244.16 |    237.22 |    236.54 |
| oct     |    224.81 |    218.51 |    216.67 |    216.03 |    207.99 |    207.4  |
| nov     |    220.62 |    254.24 |    238.48 |    200.2  |    190.4  |    190.33 |
| dec     |    231.2  |    211.89 |    212.21 |    205.64 |    194.85 |    194.68 |
| Jan/Jul |    363.58 |    359.86 |    349.25 |    334.14 |    330.36 |    310.82 |
| Feb/Jun |    323.05 |    320.14 |    317.74 |    294.84 |    290.29 |    289.54 |
| other 8 |    249.23 |    240.73 |    239.75 |    228.95 |    222.17 |    221.5  |
| all 12  |    283.39 |    277.04 |    273.77 |    260.02 |    254.37 |    249.73 |

## Per airport, variant A (RMSE, s)

|      |   Jan/Jul |   Feb/Jun |   other 8 |   all 12 |
|:-----|----------:|----------:|----------:|---------:|
| EDDF |     171.7 |     148.5 |     143.6 |    149.2 |
| EDDM |     151.2 |     129.4 |     127.1 |    131.6 |
| EGLL |     253.1 |     208.5 |     204.3 |    213.9 |
| EHAM |     162.8 |     129.9 |     123.5 |    131.8 |
| LEBL |     208.6 |     148.8 |     178.3 |    179.3 |
| LEMD |     170.9 |     154.2 |     160   |    161   |
| LFPG |     565.3 |     223.1 |     219   |    305.2 |
| LIRF |     600.2 |     702.5 |     449.7 |    523.8 |
| LSZH |     182.9 |     192.7 |     319.8 |    284   |
| LTFM |     248.6 |     417.5 |     212.8 |    260.5 |

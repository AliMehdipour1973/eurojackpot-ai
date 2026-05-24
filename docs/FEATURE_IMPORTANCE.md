# Feature Importance — Phase 4

**Generated:** 2026-05-24 13:56:02 UTC  
**Training draws:** 435  
**Classifiers:** 50 main (binary per number) + 12 euro (binary per number), averaged importance  
**XGBoost:** n_estimators=100, max_depth=4, learning_rate=0.1

---

## Coverage Summary

| Threshold | Features Required |
|-----------|-------------------|
| 80% cumulative importance | 21 |
| 90% cumulative importance | 25 |

---

## Full Ranked Table (60 features)

| Rank | Feature | Avg Importance | Share | Cumulative | Category | Keep 80% | Keep 90% |
|------|---------|----------------|-------|------------|----------|----------|----------|
| 1 | `trend_score_2` | 0.049115 | 4.91% | 4.91% | trend | Yes | Yes |
| 2 | `trend_score_4` | 0.048233 | 4.82% | 9.73% | trend | Yes | Yes |
| 3 | `trend_score_1` | 0.047096 | 4.71% | 14.44% | trend | Yes | Yes |
| 4 | `freq_main_6` | 0.045530 | 4.55% | 19.00% | frequency | Yes | Yes |
| 5 | `freq_main_1` | 0.044899 | 4.49% | 23.49% | frequency | Yes | Yes |
| 6 | `trend_score_10` | 0.044878 | 4.49% | 27.98% | trend | Yes | Yes |
| 7 | `freq_main_2` | 0.044701 | 4.47% | 32.45% | frequency | Yes | Yes |
| 8 | `freq_main_9` | 0.043807 | 4.38% | 36.83% | frequency | Yes | Yes |
| 9 | `trend_score_7` | 0.043624 | 4.36% | 41.19% | trend | Yes | Yes |
| 10 | `freq_main_3` | 0.042947 | 4.29% | 45.48% | frequency | Yes | Yes |
| 11 | `freq_main_8` | 0.042560 | 4.26% | 49.74% | frequency | Yes | Yes |
| 12 | `freq_main_4` | 0.041984 | 4.20% | 53.94% | frequency | Yes | Yes |
| 13 | `freq_main_13` | 0.038685 | 3.87% | 57.81% | frequency | Yes | Yes |
| 14 | `freq_main_5` | 0.037210 | 3.72% | 61.53% | frequency | Yes | Yes |
| 15 | `freq_main_7` | 0.035228 | 3.52% | 65.05% | frequency | Yes | Yes |
| 16 | `freq_main_10` | 0.033825 | 3.38% | 68.43% | frequency | Yes | Yes |
| 17 | `freq_main_14` | 0.030600 | 3.06% | 71.49% | frequency | Yes | Yes |
| 18 | `freq_main_11` | 0.028430 | 2.84% | 74.34% | frequency | Yes | Yes |
| 19 | `freq_main_12` | 0.028386 | 2.84% | 77.17% | frequency | Yes | Yes |
| 20 | `freq_main_15` | 0.027983 | 2.80% | 79.97% | frequency | Yes | Yes |
| 21 | `freq_main_16` | 0.026824 | 2.68% | 82.65% | frequency | Yes | Yes |
| 22 | `freq_main_17` | 0.023199 | 2.32% | 84.97% | frequency | No | Yes |
| 23 | `freq_main_20` | 0.020947 | 2.09% | 87.07% | frequency | No | Yes |
| 24 | `trend_score_3` | 0.019545 | 1.95% | 89.02% | trend | No | Yes |
| 25 | `freq_main_19` | 0.017334 | 1.73% | 90.76% | frequency | No | Yes |
| 26 | `freq_main_18` | 0.016801 | 1.68% | 92.44% | frequency | No | No |
| 27 | `freq_main_21` | 0.013032 | 1.30% | 93.74% | frequency | No | No |
| 28 | `freq_main_28` | 0.011725 | 1.17% | 94.91% | frequency | No | No |
| 29 | `freq_main_25` | 0.009972 | 1.00% | 95.91% | frequency | No | No |
| 30 | `freq_main_26` | 0.007935 | 0.79% | 96.70% | frequency | No | No |
| 31 | `freq_main_23` | 0.006962 | 0.70% | 97.40% | frequency | No | No |
| 32 | `trend_score_5` | 0.005927 | 0.59% | 97.99% | trend | No | No |
| 33 | `freq_main_27` | 0.005775 | 0.58% | 98.57% | frequency | No | No |
| 34 | `freq_main_22` | 0.004813 | 0.48% | 99.05% | frequency | No | No |
| 35 | `freq_main_31` | 0.004796 | 0.48% | 99.53% | frequency | No | No |
| 36 | `freq_main_24` | 0.003583 | 0.36% | 99.89% | frequency | No | No |
| 37 | `freq_main_35` | 0.000995 | 0.10% | 99.99% | frequency | No | No |
| 38 | `trend_score_9` | 0.000113 | 0.01% | 100.00% | trend | No | No |
| 39 | `freq_main_30` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 40 | `freq_main_29` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 41 | `freq_main_32` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 42 | `freq_main_33` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 43 | `freq_main_34` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 44 | `freq_main_36` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 45 | `freq_main_44` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 46 | `freq_main_43` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 47 | `freq_main_42` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 48 | `freq_main_41` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 49 | `freq_main_40` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 50 | `freq_main_39` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 51 | `freq_main_38` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 52 | `freq_main_37` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 53 | `freq_main_49` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 54 | `freq_main_50` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 55 | `freq_main_47` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 56 | `freq_main_48` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 57 | `freq_main_46` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 58 | `freq_main_45` | 0.000000 | 0.00% | 100.00% | frequency | No | No |
| 59 | `trend_score_6` | 0.000000 | 0.00% | 100.00% | trend | No | No |
| 60 | `trend_score_8` | 0.000000 | 0.00% | 100.00% | trend | No | No |

---

## Top Features (80% coverage)

- `trend_score_2`
- `trend_score_4`
- `trend_score_1`
- `freq_main_6`
- `freq_main_1`
- `trend_score_10`
- `freq_main_2`
- `freq_main_9`
- `trend_score_7`
- `freq_main_3`
- `freq_main_8`
- `freq_main_4`
- `freq_main_13`
- `freq_main_5`
- `freq_main_7`
- `freq_main_10`
- `freq_main_14`
- `freq_main_11`
- `freq_main_12`
- `freq_main_15`
- `freq_main_16`

---

## Bottom Features (candidates for removal)

- `freq_main_17`
- `freq_main_20`
- `trend_score_3`
- `freq_main_19`
- `freq_main_18`
- `freq_main_21`
- `freq_main_28`
- `freq_main_25`
- `freq_main_26`
- `freq_main_23`
- `trend_score_5`
- `freq_main_27`
- `freq_main_22`
- `freq_main_31`
- `freq_main_24`
- `freq_main_35`
- `trend_score_9`
- `freq_main_30`
- `freq_main_29`
- `freq_main_32`
- `freq_main_33`
- `freq_main_34`
- `freq_main_36`
- `freq_main_44`
- `freq_main_43`
- `freq_main_42`
- `freq_main_41`
- `freq_main_40`
- `freq_main_39`
- `freq_main_38`
- `freq_main_37`
- `freq_main_49`
- `freq_main_50`
- `freq_main_47`
- `freq_main_48`
- `freq_main_46`
- `freq_main_45`
- `trend_score_6`
- `trend_score_8`

---

## Recommendation for Phase 5

For Phase 5, keep the **21 features** that cover 80% of cumulative importance:

`trend_score_2`, `trend_score_4`, `trend_score_1`, `freq_main_6`, `freq_main_1`, `trend_score_10`, `freq_main_2`, `freq_main_9`, `trend_score_7`, `freq_main_3`, `freq_main_8`, `freq_main_4`, `freq_main_13`, `freq_main_5`, `freq_main_7`, `freq_main_10`, `freq_main_14`, `freq_main_11`, `freq_main_12`, `freq_main_15`, `freq_main_16`

- Frequency features retained: 16
- Trend features retained: 5

Consider dropping **39** low-importance features (below 80% threshold):

`freq_main_17`, `freq_main_20`, `trend_score_3`, `freq_main_19`, `freq_main_18`, `freq_main_21`, `freq_main_28`, `freq_main_25`, `freq_main_26`, `freq_main_23`, `trend_score_5`, `freq_main_27`, `freq_main_22`, `freq_main_31`, `freq_main_24`, `freq_main_35`, `trend_score_9`, `freq_main_30`, `freq_main_29`, `freq_main_32`, `freq_main_33`, `freq_main_34`, `freq_main_36`, `freq_main_44`, `freq_main_43`, `freq_main_42`, `freq_main_41`, `freq_main_40`, `freq_main_39`, `freq_main_38`, `freq_main_37`, `freq_main_49`, `freq_main_50`, `freq_main_47`, `freq_main_48`, `freq_main_46`, `freq_main_45`, `trend_score_6`, `trend_score_8`

Use the 90% set (25 features) if you want a slightly larger feature set with marginal extra coverage.

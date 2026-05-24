# Algorithm Comparison — Phase 5

**Generated:** 2026-05-24 14:36:59 UTC  
**Features used:** 21 (Phase 4 selection)  
**Walk-forward windows:** 5 (same as Phase 3)  
**Random baseline hit_total_3+:** 3.20%

---

## Comparison Table

| Algorithm | hit_main_2+ | hit_main_3+ | hit_total_3+ | vs Random |
|-----------|-------------|-------------|--------------|-----------|
| Random | 7.10% | 0.34% | 3.20% | baseline |
| XGBoost | 7.23% | 0.43% | 4.68% | +46.49% |
| RandomForest | 8.09% | 0.00% | 2.98% | -6.78% |
| LogisticRegression | 11.06% | 0.00% | 2.98% | -6.78% |
| ExtraTrees | 5.96% | 0.00% | 2.55% | -20.10% |
| LightGBM | 4.26% | 0.43% | 2.13% | -33.41% |
| GradientBoosting | 7.23% | 0.00% | 1.70% | -46.73% |

*Ranked by improvement on hit_total_3+ vs random (excluding Random row).*

---

## Winner

**XGBoost** — best hit_total_3+ improvement vs random: **+46.49%**

| Metric | Value |
|--------|-------|
| hit_rate_main_2_plus | 7.2340% |
| hit_rate_main_3_plus | 0.4255% |
| hit_rate_total_3_plus | 4.6809% |
| Predictions | 235 |

---

## Key Findings

- Compared 6 approaches: Random baseline, XGBoost (Phase 3, 60 features), and 5 models on 21 features.
- XGBoost results were loaded from `backtest.backtest_xgboost` without re-training.
- New models used only the 21 features from `docs/FEATURE_IMPORTANCE.md`.
- Algorithms ranked by `hit_rate_total_3_plus` improvement over random (3.20%).

---

## Honest Assessment

All improvements over random are small in absolute terms. Lottery draws remain highly random; no algorithm guarantees better outcomes. XGBoost shows the largest lift (+46.49% on hit_total_3_plus), but this must be validated on future draws before any claim of edge.

---

## Selected Features (21)

`trend_score_2`, `trend_score_4`, `trend_score_1`, `freq_main_6`, `freq_main_1`, `trend_score_10`, `freq_main_2`, `freq_main_9`, `trend_score_7`, `freq_main_3`, `freq_main_8`, `freq_main_4`, `freq_main_13`, `freq_main_5`, `freq_main_7`, `freq_main_10`, `freq_main_14`, `freq_main_11`, `freq_main_12`, `freq_main_15`, `freq_main_16`

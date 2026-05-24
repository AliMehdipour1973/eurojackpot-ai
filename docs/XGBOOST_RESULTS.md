# XGBoost Walk-Forward Results

**Generated:** 2026-05-24 12:33:17 UTC  
**Pipeline run ID:** `fcee7081-b239-454f-ac3c-99a257edc217`  
**Model:** `xgboost` `v1.0`  
**Total predictions:** 235

---

## Comparison vs Random Baseline

| Metric | Random Baseline | XGBoost | Improvement |
|--------|----------------|---------|-------------|
| hit_rate_main_2_plus | 7.1034% | 7.2340% | +1.84% |
| hit_rate_main_3_plus | 0.3448% | 0.4255% | +23.41% |
| hit_rate_total_3_plus | 3.1954% | 4.6809% | +46.49% |
| avg_main_hits | — | 0.5191 | — |
| avg_euro_hits | — | 0.3702 | — |

---

## Walk-Forward Windows

| Window | Train Index | Validate Index |
|--------|-------------|----------------|
| 1 | 0..199 | 200..249 |
| 2 | 50..249 | 250..299 |
| 3 | 100..299 | 300..349 |
| 4 | 150..349 | 350..399 |
| 5 | 200..399 | 400..434 |

---

## Notes

- 50 main-number classifiers + 12 euro-number classifiers (binary one-vs-rest).
- Features: `freq_main_1..50` + draw-level averaged `trend_score_1..10`.
- Top-5 / top-2 numbers selected by predicted probability on each validation draw.

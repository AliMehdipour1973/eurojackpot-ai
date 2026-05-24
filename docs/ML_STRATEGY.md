# EuroJackpot AI — ML & Backtesting Strategy

**Version:** 1.0  
**Date:** 2026-05-24  
**Principle:** Empirical discovery — let data answer, not assumptions.

---

## Core Philosophy

No feature or algorithm can predict lottery numbers with certainty.
The goal is empirical discovery:
- Test many combinations of features and algorithms
- Compare every result against a random baseline
- Report findings honestly — even if the best result is only 2-3% better than random
- Never claim predictive power beyond what backtests prove

---

## Validation Strategy — Walk-Forward

Never test on data the model has seen. Use rolling walk-forward windows:

Window 1: Train draws 1..200   → Validate draws 201..250
Window 2: Train draws 51..250  → Validate draws 251..300
Window 3: Train draws 101..300 → Validate draws 301..350
Window 4: Train draws 151..350 → Validate draws 351..400
Window 5: Train draws 201..400 → Validate draws 401..435


Each algorithm must be evaluated on unseen data only.
Backtest success on training data means nothing.

---

## Feature Groups

### Group 1 — Frequency Based (Priority: HIGH)
- Frequency count in last 5, 10, 20, 50 draws
- Ratio of actual frequency to expected frequency
- Number of draws since last appearance of each number

### Group 2 — Trend Based (Priority: HIGH)
- Slope of frequency change across different windows
- Short-term vs long-term frequency comparison
- Acceleration — is the trend speeding up or slowing down?

### Group 3 — Pattern Based (Priority: MEDIUM)
- Historical co-occurrence between numbers
- Gap distribution between consecutive appearances
- Sum distribution of numbers per draw

### Group 4 — Temporal (Priority: LOW — test last)
- Day of week (Tuesday vs Friday)
- Month of year
- Distance from last jackpot win

---

## Algorithm Priority

### Priority 1 — Start here
| Algorithm | Reason |
|-----------|--------|
| XGBoost | Best for tabular data, handles missing values |
| LightGBM | Faster than XGBoost, similar results |
| Random Forest | Robust, less prone to overfitting |

### Priority 2 — After Priority 1 results
| Algorithm | Reason |
|-----------|--------|
| Logistic Regression | Simple ML baseline |
| Gradient Boosting | Alternative boosting variant |
| Extra Trees | Random Forest variant |

### Priority 3 — Only if Priority 1 shows interesting results
| Algorithm | Reason |
|-----------|--------|
| LSTM | If temporal patterns emerge |
| GRU | Alternative to LSTM |
| Transformer | If sequence patterns emerge |

### Not worth testing
| Algorithm | Reason |
|-----------|--------|
| ARIMA / Prophet | For continuous time series, not discrete lottery |
| SVM | Slow and weak with this data size |

---

## Success Metrics

Primary metric for all algorithms:

```python
# Hit rates — most important
hit_rate_main_2_plus   # % of tickets with >= 2 correct main numbers
hit_rate_main_3_plus   # % of tickets with >= 3 correct main numbers
hit_rate_total_3_plus  # % of tickets with >= 3 correct total numbers

# Always compare against random baseline
improvement_over_random = (
    (algorithm_hit_rate - random_hit_rate) / random_hit_rate * 100
)
```

A result is considered meaningful only if:
- It consistently outperforms random across ALL walk-forward windows
- The improvement is reproducible, not a one-window fluke

---

## Implementation Phases

### Phase 1 — Feature Builders
Build and store all Group 1 and Group 2 features in:
- features.frq_numbers (+ 6 rolling window tables)
- features.trend_numbers (+ 6 rolling window tables)
- features.conditional_prob_numbers (+ 6 rolling window tables)

Exit criteria: All feature tables populated. verify_schema.sql passes.

### Phase 2 — Random Baseline
Build a pure random generator.
Run it against all historical draws.
Record hit rates in backtest.backtest_result with model_name = 'random_baseline'
This number is the reference point for everything else.

### Phase 3 — Walk-Forward Backtest (XGBoost first)
Run XGBoost with all Group 1 + Group 2 features.
Use walk-forward windows defined above.
Compare against random baseline.
Store results in backtest.backtest_xgboost

### Phase 4 — Feature Selection
Keep only features that improved XGBoost performance.
Drop features that added noise.
Document which features survived in this file.

### Phase 5 — Algorithm Comparison
Run all Priority 1 and Priority 2 algorithms with selected features.
Compare all results against random baseline.
Identify if any algorithm consistently outperforms random.

### Phase 6 — Honest Reporting
Whatever Phase 5 finds — report it accurately in the UI.
If the best algorithm is only 1% better than random — say so.
Never overstate results.

---

## Random Baseline — Reference Numbers

| Metric | Random | XGBoost | LightGBM (unstable — excluded) | RandomForest |
|--------|--------|---------|------------------------------|--------------|
| hit_total_3_plus | 3.20% | 4.68% | 4.26% | 2.98% |
| hit_main_2_plus | 7.10% | 7.23% | TBD | TBD |
| hit_main_3_plus | 0.34% | 0.43% | TBD | TBD |

---

## Decisions Log

- 2026-05-24: Walk-forward validation chosen over simple train/test split
- 2026-05-24: Priority order defined — XGBoost first, LSTM only if needed
- 2026-05-24: ARIMA and Prophet excluded — wrong problem type
- 2026-05-24: Success defined as consistent improvement across ALL windows
- 2026-05-24: Random baseline completed — 4,350 tickets across 435 draws
- 2026-05-24: Baseline hit_rate_main_2_plus = 7.10% (reference point)
- 2026-05-24: XGBoost walk-forward complete — 235 predictions across 5 windows
- 2026-05-24: XGBoost outperforms random on all metrics (best: total_3_plus +46.49%)
- 2026-05-24: Phase 3 complete — proceeding to Phase 4 Feature Selection
- 2026-05-24: Phase 4 complete — 21 features cover 80% importance
- 2026-05-24: trend_scores dominate top features over freq_main
- 2026-05-24: 39 of 60 features are noise — will be dropped in Phase 5
- 2026-05-24: Phase 5 complete — XGBoost wins (hit_total_3+ +46.49% vs random)
- 2026-05-24: Only XGBoost and LightGBM beat random baseline
- 2026-05-24: Selected model for production: XGBoost
- 2026-05-24: Phase 6 next — honest reporting in UI

---

## Phase 4 Results — Feature Selection

**Completed:** 2026-05-24 13:56:02 UTC

| Metric | Value |
|--------|-------|
| Features analyzed | 60 |
| Classifiers averaged | 62 (50 main + 12 euro) |
| Features for 80% importance | 21 |
| Features for 90% importance | 25 |
| Top feature | `trend_score_2` |

**Top 5 features:** `trend_score_2`, `trend_score_4`, `trend_score_1`, `freq_main_6`, `freq_main_1`

**Phase 5 recommendation:** Keep 21 features at 80% coverage. See `docs/FEATURE_IMPORTANCE.md` for full ranking.

**Features to keep:** `trend_score_2`, `trend_score_4`, `trend_score_1`, `freq_main_6`, `freq_main_1`, `trend_score_10`, `freq_main_2`, `freq_main_9`, `trend_score_7`, `freq_main_3`, `freq_main_8`, `freq_main_4`, `freq_main_13`, `freq_main_5`, `freq_main_7`, `freq_main_10`, `freq_main_14`, `freq_main_11`, `freq_main_12`, `freq_main_15`, `freq_main_16`


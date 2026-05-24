# Random Baseline Results

**Generated:** 2026-05-24 12:14:26 UTC  
**Pipeline run ID:** `5a278727-59ff-40cc-ab27-bb0d0a34d3e4`  
**Model:** `random_baseline` `v1.0`  
**Historical draws:** 435  
**Simulations per draw:** 10  
**Total tickets:** 4350

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total tickets generated | 4,350 |
| hit_rate_main_2_plus | 7.1034% |
| hit_rate_main_3_plus | 0.3448% |
| hit_rate_total_3_plus | 3.1954% |
| avg_main_hits | 0.5028 |
| avg_euro_hits | 0.3299 |

---

## Notes

- Pure random ticket generation: 5 unique main numbers (1–50) + 2 unique euro numbers (1–12).
- Each ticket is compared against the actual draw for that date.
- This baseline is the reference point for all future model comparisons (see `docs/ML_STRATEGY.md`).

# EuroJackpot AI — Project Status

**Last Updated:** 2026-05-24  
**Overall Status:** 🟡 In Progress — Foundation Phase

---

## Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| Neon PostgreSQL | ✅ Done | eurojackpot-ai project, Frankfurt |
| Render Backend | ⬜ Not started | After schema applied |
| Vercel Frontend | ⬜ Not started | After API ready |
| Redis | ⬜ Not started | After backend ready |

---

## Database Schema

| File | Status | Notes |
|------|--------|-------|
| 01_core_schema.sql | ✅ Applied to Neon | core.draws + core.draw_details |
| 02_frequency_tables.sql | ✅ Applied to Neon | FK updated to core.draws |
| 03_conditional_prob.sql | ✅ Applied to Neon | FK updated to core.draws |
| 04_trend_tables.sql | ✅ Applied to Neon | FK updated to core.draws |
| 05_ml_features.sql | ✅ Applied to Neon | FK updated to core.draws |
| 06_backtest_schema.sql | ✅ Applied to Neon | FK updated to core.draws |
| Applied to Neon | ✅ Done | 68 tables across 3 schemas |

---

## Data Pipeline

| Component | Status | Notes |
|-----------|--------|-------|
| Scraper (WestLotto) | ✅ Done | Single Neon DB, two upserts |
| Historical data import | ✅ Done | 435 draws (2022-03-25 to 2026-05-22) |
| Feature builders | ✅ Done | frq_numbers + trend_numbers + ml_features populated |

---

## ML Pipeline

| Component | Status | Notes |
|-----------|--------|-------|
| Random Baseline | ✅ Done | 4,350 tickets, hit_total_3+ = 3.20% |
| XGBoost Backtest | ✅ Done | +46.49% vs random |
| Feature Selection | ✅ Done | 21 of 60 features kept |
| Algorithm Comparison | ✅ Done | XGBoost winner |

---

## Backend API

| Endpoint | Status | Notes |
|----------|--------|-------|
| GET /api/v1/health | ✅ Done | database connected, 435 draws |
| GET /api/v1/draws | ✅ Done | pagination, date filter |
| GET /api/v1/draws/{draw_date} | ✅ Done | with prize details |
| GET /api/v1/statistics/frequency | ✅ Done | 7 window sizes |
| POST /api/v1/generator/generate | ✅ Done | XGBoost + random modes |

---

## Frontend

| Page | Status | Notes |
|------|--------|-------|
| / (home) | ⬜ Not started | |
| /draws | ⬜ Not started | |
| /statistics | ⬜ Not started | |

---

## Decisions Log
See docs/DECISIONS.md for all architecture decisions.

---

## Next Action
→ Build Next.js frontend — draws page and statistics dashboard

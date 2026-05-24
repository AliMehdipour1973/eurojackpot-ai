# EuroJackpot AI — Decision Log

## Decision 1 — Database
Single Neon database. All schemas (core, features, backtest, app) in one database.

## Decision 2 — Core Schema
Two tables: core.draws (8 columns, source of truth) + core.draw_details (26 columns, prize/winner data).
FK: core.draw_details → core.draws ON DELETE CASCADE.

## Decision 3 — Folder Structure
sql/ at repo root (not inside apps/api/).
scraper/ at repo root as standalone module.
MVP-only pages in web: draws/ and statistics/ only.

## Decision 4 — Scraper
Single database target (eurojackpot_ai on Neon).
Two upserts per draw: core.draws then core.draw_details.

## Decision 5 — ML Strategy
Empirical discovery approach. Walk-forward validation.
XGBoost first. Random baseline as reference.
Full strategy documented in docs/ML_STRATEGY.md

## Decision 6 — Production Model
XGBoost with 21 selected features.
Outperforms random by +46.49% on hit_total_3_plus (consistent across runs).
LightGBM excluded as backup — unstable results across runs 
(4.26% vs 2.13% in two identical runs on same data).
All other algorithms perform worse than random.
Final: XGBoost is the sole production model.
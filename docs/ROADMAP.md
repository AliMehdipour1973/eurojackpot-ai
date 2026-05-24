# EuroJackpot AI — Complete & Detailed Web Application Roadmap

**Project Title:** EuroJackpot AI — Randomness-Aware Lottery Probability Platform  
**Document Version:** 1.0  
**Prepared for:** Ali  
**Prepared by:** ChatGPT — Senior Project Advisor  
**Core Principle:** *There is no 100% in lottery systems.*  
**Positioning:** Probability education, randomness analysis, responsible number generation, historical analytics, simulation, and transparent backtesting — **not guaranteed winning numbers**.

---

## 0. Executive Summary

EuroJackpot AI should **not** be built as a “winning number predictor.” If the EuroJackpot draw process is fair, each valid combination is fundamentally random and independent of previous draws. Therefore, the product must never claim it can predict the next draw or increase the mathematical probability of hitting the jackpot.

The right product is an **intelligent lottery probability assistant**:

- It helps users understand randomness.
- It analyzes historical draws without implying future certainty.
- It generates number combinations using transparent, responsible, non-misleading methods.
- It explains that all valid combinations have the same base chance.
- It audits every model or strategy against real historical outcomes.
- It shows when a strategy fails.
- It prevents “dream selling,” hype, and false certainty.
- It can learn which strategies are misleading, redundant, or statistically weak.

The MatchMind principle transfers directly:

> **No hype. No false certainty. No guaranteed outcomes. Show the data, show the limits, show the reality.**

---

## 1. Project Goal

### 1.1 Primary Goal

Build a web application that helps users explore EuroJackpot draws through:

1. Historical draw analysis.
2. Frequency and trend visualization.
3. Randomness-aware number generation.
4. Probability education.
5. Backtesting of strategies.
6. Responsible play warnings.
7. AI-assisted explanations.
8. Transparent audit of generated combinations versus actual results.

### 1.2 What the Project Must Not Do

EuroJackpot AI must never claim:

- “These are the winning numbers.”
- “AI predicts the next draw.”
- “This increases your jackpot probability.”
- “Guaranteed winning combination.”
- “Hot numbers will win.”
- “Cold numbers are due.”
- “The system has cracked the lottery.”
- “100% strategy.”
- “Best numbers to play.”

### 1.3 Correct Product Statement

> EuroJackpot AI helps users understand lottery randomness, analyze historical draw patterns, simulate strategies, and generate transparent number combinations — without promising or implying future winning results.

### 1.4 Locked Product Integrity Principle

> **Every valid EuroJackpot combination has the same base mathematical chance in a fair draw. Any historical pattern analysis must be framed as descriptive, not predictive.**

---

## 2. Target Users

### 2.1 Target Users

- Probability-curious lottery players.
- Data-driven users interested in randomness.
- Users who want to avoid human-biased number selection.
- Users who want to understand odds and simulations.
- Content creators explaining probability and lottery randomness.
- Users who want transparent number generation without fake claims.

### 2.2 Non-Target Users

- People seeking guaranteed winning numbers.
- Gambling addicts or users chasing losses.
- Users expecting “AI jackpot prediction.”
- Tipster-style lottery audiences.
- Users who want emotional hype rather than probability education.

---

## 3. Product Principles

### 3.1 No 100% Principle

There is no 100% in EuroJackpot. The product must explicitly communicate that even the most sophisticated analysis cannot guarantee future draw outcomes.

### 3.2 Randomness First

The app must respect the randomness of lottery draws. Historical data can describe the past, but it must not be marketed as a deterministic signal for the future.

### 3.3 Transparency Over Conversion

The app must not exaggerate to increase usage, purchases, subscriptions, or engagement.

### 3.4 Backtest Everything

Every number strategy must be evaluated against historical draws. If it performs no better than random, the app must say so.

### 3.5 Explain, Do Not Manipulate

The app should teach users probability, not push them toward more purchases.

### 3.6 Responsible Play

The app must include responsible play language and never encourage chasing losses, buying more tickets, or treating lottery participation as investment.

---

## 4. Product Scope

### 4.1 Core User-Facing Features

1. **Historical Draw Explorer**
   - Draw date.
   - Main numbers.
   - Euro numbers.
   - Sorted draw display.
   - Search and filters by date range.
   - Visual history timeline.

2. **Frequency Dashboard**
   - Main number frequency.
   - Euro number frequency.
   - Rolling frequency windows: 5, 7, 10, 20, 30, 50 draws.
   - Clear disclaimer: frequency is descriptive, not predictive.

3. **Trend Dashboard**
   - Trend scores per number.
   - Rolling trend comparison.
   - Hot/cold labels only if heavily disclaimed.
   - Prefer “recent frequency movement” over “hot/cold.”

4. **Conditional Pair Explorer**
   - Historical co-occurrence / conditional relations.
   - Base number → next number patterns.
   - Warning: co-occurrence does not imply future causation.

5. **Number Combination Generator**
   - Pure random generator.
   - Balanced random generator.
   - Low-human-bias generator.
   - Avoid birthday-heavy patterns.
   - Avoid sequential patterns.
   - Avoid too many user-popular patterns.
   - Explicit note: this does not increase jackpot probability.

6. **Simulation Engine**
   - Simulate many generated combinations against historical draws.
   - Show expected hit distribution.
   - Show how rare major hits are.
   - Show “random baseline” comparison.

7. **Backtesting Lab**
   - Test strategies over historical draws.
   - Compare against random strategies.
   - Show hit counts, average hits, best/worst runs.
   - Never present backtest success as future guarantee.

8. **AI Explanation Layer**
   - Explain what a strategy does.
   - Explain why the product does not predict.
   - Explain results from backtests.
   - Answer probability questions.
   - Refuse guaranteed-number requests.

9. **Responsible Play Panel**
   - Budget reminders.
   - “Lottery is entertainment, not investment.”
   - No prompts to buy more tickets.
   - Optional self-limit reminders.

10. **Transparency / Methodology Page**
    - How random generation works.
    - How backtests work.
    - Why historical patterns do not guarantee future outcomes.
    - What the AI can and cannot do.

---

## 5. Technical Architecture

### 5.1 Recommended Stack

| Layer | Recommended Technology | Reason |
|---|---|---|
| Frontend | Next.js 16 + React + TypeScript | Modern SSR/SEO, dashboard UI, Vercel deployment |
| UI Components | Tailwind CSS + shadcn/ui | Fast, clean, consistent interface |
| Backend API | FastAPI + Python 3.12 | Excellent for data, ML, and async APIs |
| Database | PostgreSQL | Strong relational integrity and analytical queries |
| Cache / jobs | Redis | Caching, idempotency, rate limit, background job queues |
| ML / analytics | Python, pandas, NumPy, scikit-learn | Statistical analysis and feature pipelines |
| Backtesting | Python services + PostgreSQL backtest schema | Reproducible experiment history |
| AI advisor | Anthropic Claude API | Explanation, strategy review, user education |
| Deployment frontend | Vercel | Best fit for Next.js |
| Deployment backend | Render / Fly.io / Railway initially; AWS later if needed | Simple deployment for MVP |
| Artifact storage | S3-compatible object storage | Store reports, backtest outputs, exports |
| Monitoring | Sentry + structured logs | Production issue visibility |
| CI/CD | GitHub Actions | Tests, lint, schema verification |

### 5.2 High-Level System Flow

```text
Historical Draw Source
    ↓
Ingestion Pipeline
    ↓
core.main_table_new
    ↓
Feature Builder
    ↓
features.frq_numbers
features.conditional_prob_numbers
features.trend_numbers
features.ml_features
    ↓
Strategy / Generator / Simulation Engine
    ↓
Backtesting Engine
    ↓
backtest.backtest_result
backtest.agent_learning_history
backtest.feedback_history
    ↓
AI Explanation Layer
    ↓
User UI
```

---

## 6. Repository Folder Structure

```text
eurojackpot-ai/
├── apps/
│   ├── api/
│   │   ├── src/
│   │   │   ├── api/
│   │   │   │   ├── v1/
│   │   │   │   │   ├── endpoints/
│   │   │   │   │   │   ├── health.py
│   │   │   │   │   │   ├── draws.py
│   │   │   │   │   │   ├── statistics.py
│   │   │   │   │   │   ├── generator.py
│   │   │   │   │   │   ├── simulation.py
│   │   │   │   │   │   ├── backtest.py
│   │   │   │   │   │   ├── advisor.py
│   │   │   │   │   │   ├── responsible_play.py
│   │   │   │   │   │   └── admin.py
│   │   │   │   │   └── router.py
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   ├── logging.py
│   │   │   │   ├── security.py
│   │   │   │   ├── cache.py
│   │   │   │   └── rate_limit.py
│   │   │   ├── db/
│   │   │   │   ├── connection.py
│   │   │   │   ├── draw_storage.py
│   │   │   │   ├── feature_storage.py
│   │   │   │   ├── backtest_storage.py
│   │   │   │   ├── advisor_storage.py
│   │   │   │   └── audit_storage.py
│   │   │   ├── ingestion/
│   │   │   │   ├── draw_importer.py
│   │   │   │   ├── validation.py
│   │   │   │   ├── scheduler.py
│   │   │   │   └── source_clients.py
│   │   │   ├── features/
│   │   │   │   ├── frequency_builder.py
│   │   │   │   ├── conditional_builder.py
│   │   │   │   ├── trend_builder.py
│   │   │   │   └── ml_feature_builder.py
│   │   │   ├── lottery/
│   │   │   │   ├── rules.py
│   │   │   │   ├── probability.py
│   │   │   │   ├── combination_generator.py
│   │   │   │   ├── strategy_engine.py
│   │   │   │   ├── simulation_engine.py
│   │   │   │   └── validation.py
│   │   │   ├── ml/
│   │   │   │   ├── baselines.py
│   │   │   │   ├── ranking_model.py
│   │   │   │   ├── meta_learner.py
│   │   │   │   ├── evaluation.py
│   │   │   │   └── experiment_runner.py
│   │   │   ├── advisor/
│   │   │   │   ├── prompts.py
│   │   │   │   ├── claude_client.py
│   │   │   │   ├── safety.py
│   │   │   │   ├── strategy_reviewer.py
│   │   │   │   └── explanation_service.py
│   │   │   └── main.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── e2e/
│   │   ├── sql/
│   │   │   ├── 01_main_table_new.sql
│   │   │   ├── 02_frequency_tables.sql
│   │   │   ├── 03_conditional_prob.sql
│   │   │   ├── 04_trend_tables.sql
│   │   │   ├── 05_ml_features.sql
│   │   │   ├── 06_backtest_schema.sql
│   │   │   └── verify_schema.sql
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── web/
│       ├── app/
│       │   ├── page.tsx
│       │   ├── draws/
│       │   ├── statistics/
│       │   ├── generator/
│       │   ├── simulator/
│       │   ├── backtests/
│       │   ├── methodology/
│       │   ├── responsible-play/
│       │   ├── admin/
│       │   └── api/
│       ├── components/
│       │   ├── layout/
│       │   ├── draws/
│       │   ├── charts/
│       │   ├── generator/
│       │   ├── simulator/
│       │   ├── backtest/
│       │   ├── advisor/
│       │   └── responsible-play/
│       ├── lib/
│       │   ├── api.ts
│       │   ├── types.ts
│       │   ├── copy-rules.ts
│       │   └── formatting.ts
│       ├── public/
│       ├── package.json
│       └── next.config.ts
├── docs/
│   ├── EUROJACKPOT_ROADMAP.md
│   ├── PRODUCT_INTEGRITY_CHARTER.md
│   ├── CLAUDE.md
│   ├── API_SPEC.md
│   ├── DATABASE_SCHEMA.md
│   ├── METHODOLOGY.md
│   ├── RESPONSIBLE_PLAY.md
│   ├── SECURITY_BASELINE.md
│   ├── UI_INFORMATION_ARCHITECTURE.md
│   ├── MODELING_DECISION.md
│   ├── BACKTESTING_POLICY.md
│   ├── CHANGELOG.md
│   └── archive/
├── scripts/
│   ├── apply_schema.py
│   ├── verify_schema.py
│   ├── import_draws.py
│   ├── rebuild_features.py
│   ├── run_backtest.py
│   └── export_reports.py
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── schema-verify.yml
│       └── deploy.yml
├── docker-compose.yml
├── README.md
└── .env.example
```

---

## 7. Programming Languages by Component

| Component | Language | Notes |
|---|---|---|
| Frontend app | TypeScript | Next.js, React, strict type safety |
| UI styling | CSS / Tailwind | Utility-first design |
| Backend API | Python | FastAPI |
| Feature engineering | Python + SQL | Deterministic builders |
| Simulation | Python | NumPy-based |
| Backtesting | Python + SQL | Reproducible evaluation |
| Database | SQL / PostgreSQL | Schemas, constraints, indexes |
| CI scripts | YAML + Bash/Python | GitHub Actions |
| Claude prompts | Markdown + Python string templates | Versioned prompts |
| Documentation | Markdown | Required for governance |

---

## 8. Database Schema

The project already has a strong PostgreSQL foundation in the uploaded SQL files. The schema should be kept modular:

```text
core       = historical draw source of truth
features   = engineered features
backtest   = strategy/model evaluation and learning history
app        = users, sessions, subscriptions, settings
advisor    = Claude prompts/responses and explanation logs
audit      = operational and AI action audit logs
```

### 8.1 Existing Core Schema

#### `core.main_table_new`

Single source of truth for historical EuroJackpot draws.

| Column | Type | Purpose |
|---|---|---|
| `draw_date` | INTEGER PK | Date key in YYYYMMDD format |
| `n1`–`n5` | SMALLINT | Sorted main numbers |
| `e1`–`e2` | SMALLINT | Sorted Euro numbers |
| `created_at` | TIMESTAMPTZ | Insert timestamp |
| `updated_at` | TIMESTAMPTZ | Update timestamp |

Key constraints:
- `draw_date` between 20000101 and 20991231.
- Main numbers sorted: `n1 < n2 < n3 < n4 < n5`.
- Euro numbers sorted: `e1 < e2`.
- Main numbers between 1 and 50.
- Euro numbers between 1 and 12.

### 8.2 Existing Feature Schema

#### `features.frq_numbers`

Base rolling-frequency table for main numbers.

| Column | Purpose |
|---|---|
| `draw_date` | Draw date |
| `number` | Main number |
| `frequency_count` | Count in window |
| `window_size` | Rolling window size |

Derived tables are created for:
- 5 draws
- 7 draws
- 10 draws
- 20 draws
- 30 draws
- 50 draws

Expected tables:
```text
features.frq_numbers_5draws
features.frq_numbers_7draws
features.frq_numbers_10draws
features.frq_numbers_20draws
features.frq_numbers_30draws
features.frq_numbers_50draws
```

#### `features.conditional_prob_numbers`

Historical ordered number-pair relation table.

| Column | Purpose |
|---|---|
| `draw_date` | Draw date |
| `base_number` | Base number |
| `next_number` | Related next number |
| `conditional_probability` | Historical conditional probability |
| `window_size` | Rolling window size |

Important warning:
This table is for descriptive historical analysis only. It must not be presented as a future predictor.

#### `features.trend_numbers`

Trend-score table for each number and draw date.

| Column | Purpose |
|---|---|
| `draw_date` | Draw date |
| `number` | Main number |
| `trend_score_1`–`trend_score_10` | Complementary trend features |

Derived rolling-window tables are expected for:
- 5, 7, 10, 20, 30, 50 draws.

#### `features.ml_features`

Unified model-ready feature matrix keyed by `draw_date`.

Current structure:
- `draw_date`
- `label`
- `label_main_2`
- `label_main_3`
- `label_main_4`
- `label_main_5`
- `label_euro_1`
- `label_euro_2`
- `meta_main_1` to `meta_main_50`
- `meta_euro_1` to `meta_euro_12`
- timestamps

Important design note:
This table should be used for strategy evaluation, ranking, simulation, and model experiments — not for claiming deterministic prediction.

### 8.3 Existing Backtest Schema

#### `backtest.backtest_result`

Stores predicted combinations and actual outcomes.

Important columns:
- `draw_date`
- `prediction_for_draw_date`
- `model_name`
- `model_version`
- `pipeline_run_id`
- train/validation windows
- `predicted_main_numbers`
- `predicted_euro_numbers`
- `actual_main_numbers`
- `actual_euro_numbers`
- `hit_main_count`
- `hit_euro_count`
- `total_hit_count`
- `score_numeric`
- `rank_in_run`
- `probability_payload`
- `metrics_payload`

Important constraints:
- 5 main numbers.
- 2 Euro numbers.
- main values 1–50.
- Euro values 1–12.
- arrays unique.
- arrays sorted ascending.

#### `backtest.meta_learner_weights_history`

Tracks meta-learner weights over time.

#### `backtest.agent_learning_history`

Tracks agent/strategy learning states, actions, and reward scores.

#### `backtest.feedback_history`

Stores structured feedback from backtests or advisor review.

### 8.4 Required Additional Tables

The existing schema is good for data and backtests, but the web app needs more tables.

#### `app.users`

```sql
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    full_name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `app.saved_combinations`

```sql
CREATE TABLE IF NOT EXISTS app.saved_combinations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES app.users(id) ON DELETE CASCADE,
    main_numbers SMALLINT[] NOT NULL,
    euro_numbers SMALLINT[] NOT NULL,
    generator_method TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `app.generation_history`

```sql
CREATE TABLE IF NOT EXISTS app.generation_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES app.users(id) ON DELETE SET NULL,
    session_id TEXT,
    generator_method TEXT NOT NULL,
    main_numbers SMALLINT[] NOT NULL,
    euro_numbers SMALLINT[] NOT NULL,
    explanation_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `advisor.ai_explanations`

```sql
CREATE SCHEMA IF NOT EXISTS advisor;

CREATE TABLE IF NOT EXISTS advisor.ai_explanations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES app.users(id) ON DELETE SET NULL,
    explanation_type TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    model_name TEXT NOT NULL,
    response_json JSONB NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    cost_usd NUMERIC(10, 6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `audit.audit_log`

```sql
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.audit_log (
    id BIGSERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    outcome TEXT NOT NULL,
    details_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `responsible_play.user_limits`

```sql
CREATE SCHEMA IF NOT EXISTS responsible_play;

CREATE TABLE IF NOT EXISTS responsible_play.user_limits (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES app.users(id) ON DELETE CASCADE,
    weekly_ticket_budget_cents INTEGER,
    reminder_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 9. Data Ingestion

### 9.1 Draw Import Sources

The project needs a reliable source for historical EuroJackpot draws. The source must be documented and reproducible.

Supported ingestion modes:
1. CSV upload.
2. Admin manual import.
3. Scheduled fetch from an approved data source.
4. JSON import from trusted source.

### 9.2 Ingestion Rules

- Always sort main numbers before insert.
- Always sort Euro numbers before insert.
- Reject duplicates by `draw_date`.
- Reject invalid ranges.
- Reject malformed dates.
- Log every import.
- Never silently overwrite a draw without an audit record.

### 9.3 Ingestion API

```text
POST /api/v1/admin/draws/import
GET  /api/v1/admin/draws/import/status
GET  /api/v1/draws
GET  /api/v1/draws/{draw_date}
```

### 9.4 Exit Criteria

- Historical draws imported.
- Schema verification passes.
- Duplicate protection works.
- Invalid numbers rejected.
- Admin can rebuild features from imported draws.

---

## 10. Feature Engineering

### 10.1 Feature Families

1. Frequency features.
2. Conditional probability features.
3. Trend score features.
4. Main-number meta features.
5. Euro-number meta features.
6. Human-bias features.
7. Combination-structure features.

### 10.2 Human-Bias Features

These are especially valuable because the app can help users avoid common human patterns.

Examples:
- birthday-heavy score: many numbers ≤ 31.
- sequence score: adjacent numbers.
- symmetry score.
- repeated decade pattern.
- all low / all high pattern.
- too-balanced pattern.
- too-obvious pattern.

Important:
These features may reduce overlap with human-chosen combinations if a win occurs, but they do **not** increase the base probability of winning.

### 10.3 Feature Builder API

```text
POST /api/v1/admin/features/rebuild
GET  /api/v1/admin/features/status
GET  /api/v1/statistics/frequency
GET  /api/v1/statistics/trends
GET  /api/v1/statistics/conditional
```

---

## 11. Number Generation Strategies

### 11.1 Strategy 1 — Pure Random

Uses secure random generation:
- 5 unique sorted main numbers from 1–50.
- 2 unique sorted Euro numbers from 1–12.

This is the default and most honest generator.

### 11.2 Strategy 2 — Balanced Random

Generates random combinations with structure constraints:
- not all low numbers.
- not all high numbers.
- not too sequential.
- mix of odd/even.
- mix of decades.

Warning:
Balanced does not mean more likely to win. It only avoids unusual-looking combinations.

### 11.3 Strategy 3 — Low-Human-Bias Random

Avoids patterns humans commonly choose:
- birthday-heavy numbers.
- simple sequences.
- repeated visual patterns.
- common “lucky” layouts.

Correct framing:
This does not improve jackpot odds. It may reduce the chance of sharing a prize if the combination wins.

### 11.4 Strategy 4 — Historical-Pattern Explorer

Uses descriptive historical stats as a weighting input.

This must be marked as experimental and educational.

### 11.5 Strategy 5 — Ensemble Generator

Combines:
- pure random,
- low-human-bias random,
- balanced random,
- historical descriptive weighting.

Output must include:
- generation method,
- explanation,
- disclaimer,
- randomness score,
- human-bias score.

---

## 12. Backtesting and Evaluation

### 12.1 Backtest Goal

Backtesting is not proof of future success. It is a way to test whether strategies behaved differently from random over historical data.

### 12.2 Required Metrics

- average main hits.
- average Euro hits.
- total hit distribution.
- maximum hit count.
- strategy vs random baseline.
- variance.
- number of zero-hit draws.
- number of 2+ main hits.
- number of 3+ main hits.
- jackpot-equivalent historical hits, if any.
- false-confidence score.

### 12.3 Backtest API

```text
POST /api/v1/backtests/run
GET  /api/v1/backtests
GET  /api/v1/backtests/{id}
GET  /api/v1/backtests/{id}/report
```

### 12.4 Backtest UI

Pages:
- `/backtests`
- `/backtests/[id]`
- `/simulator`
- `/methodology/backtesting`

### 12.5 Exit Criteria

- At least one random baseline is always included.
- No strategy report can be shown without random comparison.
- UI clearly says: historical performance does not imply future performance.
- Results saved in `backtest.backtest_result`.

---

## 13. AI Layer

### 13.1 Claude Role

Claude should act as:
- probability educator,
- explanation writer,
- strategy reviewer,
- responsible-play guard,
- backtest interpreter.

Claude must not act as:
- winning-number predictor,
- gambling tipster,
- certainty generator.

### 13.2 Allowed Claude Tasks

- Explain a generated combination.
- Explain why no system can guarantee lottery outcomes.
- Summarize historical frequency.
- Interpret backtest results.
- Warn about randomness.
- Suggest a safer framing for UI copy.
- Detect misleading product claims.
- Refuse “guaranteed winning numbers.”

### 13.3 Banned Claude Outputs

Claude must never output:
- “These numbers will win.”
- “This is the best combination.”
- “This improves your chance of jackpot.”
- “AI prediction for next draw.”
- “Guaranteed result.”
- “Use this strategy to win.”

### 13.4 AI Explanation API

```text
POST /api/v1/advisor/explain-combination
POST /api/v1/advisor/explain-backtest
POST /api/v1/advisor/ask
GET  /api/v1/advisor/history
```

### 13.5 Prompt Safety

All Claude prompts must include:

```text
You are not allowed to claim that future lottery draws can be predicted.
You must explain randomness and uncertainty.
You must not recommend buying tickets.
You must not imply guaranteed winnings.
You must not use words like guaranteed, sure win, best numbers, jackpot predictor.
```

---

## 14. User Interface Roadmap

### 14.1 Main Pages

| Page | Purpose |
|---|---|
| `/` | Landing page |
| `/draws` | Historical draw explorer |
| `/statistics` | Frequency and trend dashboard |
| `/generator` | Number generation |
| `/simulator` | Simulation engine |
| `/backtests` | Strategy backtests |
| `/methodology` | Explanation of methods |
| `/responsible-play` | Responsible play page |
| `/account` | User profile |
| `/admin` | Admin dashboard |

### 14.2 Landing Page Sections

1. Hero: “Understand lottery randomness — without false certainty.”
2. Product preview: generated combination + explanation.
3. What the app does.
4. What the app does not do.
5. Historical analysis preview.
6. Backtesting preview.
7. Responsible play commitment.
8. Call to action.

### 14.3 UI Copy Examples

Correct:
- “Generate a transparent random combination.”
- “Explore historical frequency.”
- “Backtest a strategy against past draws.”
- “This does not predict the next draw.”

Incorrect:
- “Get the best numbers.”
- “Increase your chance to win.”
- “AI-powered winning numbers.”
- “Smart jackpot prediction.”

---

## 15. Security Requirements

### 15.1 Baseline Security

- No secrets in repo.
- `.env` gitignored.
- Strong auth for admin routes.
- Rate limiting on generator and advisor endpoints.
- CORS restricted.
- Input validation with Pydantic.
- SQL parameterization only.
- Audit all admin actions.
- Store Claude cost logs.
- Never expose API keys to frontend.

### 15.2 Prompt Injection Protection

Sanitize:
- user notes,
- generated labels,
- strategy descriptions,
- saved combination notes,
- imported text,
- feedback.

### 15.3 Abuse Protection

Limit:
- combinations generated per minute,
- advisor calls per user,
- backtests per day,
- simulation size for free users.

---

## 16. Responsible Play Framework

### 16.1 Required Messages

Every generator and strategy page must include:

> This tool does not predict winning numbers. Lottery draws are random. Play only for entertainment and never spend more than you can afford to lose.

### 16.2 User Safeguards

- Optional budget reminder.
- Soft warning after many generations.
- No “try again to win” language.
- No loss-chasing language.
- No gamified pressure.
- No countdown pressure.

### 16.3 Forbidden UX Patterns

- “Generate until you find lucky numbers.”
- “Boost your odds.”
- “Premium strategy has better chance.”
- “Unlock winning AI.”
- “Last chance to win.”

---

## 17. Documentation Files Required

Create these `.md` files:

```text
docs/
├── EUROJACKPOT_ROADMAP.md
├── PRODUCT_INTEGRITY_CHARTER.md
├── CLAUDE.md
├── API_SPEC.md
├── DATABASE_SCHEMA.md
├── METHODOLOGY.md
├── BACKTESTING_POLICY.md
├── RESPONSIBLE_PLAY.md
├── SECURITY_BASELINE.md
├── PROMPT_SAFETY_POLICY.md
├── UI_INFORMATION_ARCHITECTURE.md
├── MODELING_DECISION.md
├── DATA_INGESTION_GUIDE.md
├── DEPLOYMENT_GUIDE.md
├── OPERATIONS_RUNBOOK.md
├── CHANGELOG.md
└── archive/
```

### 17.1 `PRODUCT_INTEGRITY_CHARTER.md`

Must include:
- no guaranteed numbers,
- no prediction claims,
- historical data is descriptive,
- backtesting is not future proof,
- responsible play commitment,
- banned vocabulary.

### 17.2 `METHODOLOGY.md`

Must explain:
- base lottery probability,
- random combination generation,
- frequency analysis,
- trend analysis,
- conditional probability,
- why patterns do not guarantee future outcomes.

### 17.3 `BACKTESTING_POLICY.md`

Must explain:
- backtest windows,
- random baseline,
- evaluation metrics,
- no future guarantees,
- strategy archiving rules.

### 17.4 `PROMPT_SAFETY_POLICY.md`

Must define:
- Claude role,
- forbidden claims,
- refusal patterns,
- prompt injection handling,
- cost controls.

---

## 18. Claude Skill File

Recommended path:

```text
.claude/skills/eurojackpot/SKILL.md
```

Full content is provided in the companion file:
`eurojackpot_claude_skill.md`

Summary:
- Claude must act as a senior project advisor.
- Claude must protect the product from false certainty.
- Claude must never create winning-number claims.
- Claude must enforce responsible play.
- Claude must treat backtests as historical evidence only.
- Claude must always include disclaimers in user-facing copy.

---

## 19. Development Phases

## Phase 0 — Project Setup

### Deliverables

- Monorepo created.
- FastAPI backend skeleton.
- Next.js frontend skeleton.
- PostgreSQL connection.
- Redis connection.
- Docker Compose.
- CI pipeline.
- `.env.example`.
- Base docs.

### Exit Criteria

- API health endpoint works.
- Frontend loads.
- Database connection verified.
- CI green.

---

## Phase 1 — Database Foundation

### Deliverables

- Apply uploaded SQL files:
  - `01_main_table_new.sql`
  - `02_frequency_tables.sql`
  - `03_conditional_prob.sql`
  - `04_trend_tables.sql`
  - `05_ml_features.sql`
  - `06_backtest_schema.sql`
- Run `verify_schema.sql`.
- Add app/advisor/audit/responsible_play schemas.
- Create migration system.

### Exit Criteria

- Schema verification passes.
- All constraints valid.
- All indexes created.
- DB docs generated.

---

## Phase 2 — Draw Ingestion

### Deliverables

- CSV importer.
- JSON importer.
- Admin import endpoint.
- Validation service.
- Duplicate detection.
- Audit logging.

### Exit Criteria

- Historical draws imported.
- Invalid rows rejected.
- Duplicate rows skipped or safely updated.
- Draw explorer API working.

---

## Phase 3 — Feature Engineering

### Deliverables

- Frequency builder.
- Conditional probability builder.
- Trend builder.
- ML feature builder.
- Rolling-window rebuild.
- Admin rebuild endpoint.

### Exit Criteria

- Feature tables populated.
- Feature rebuild reproducible.
- Window tables generated.
- Tests for all builders.

---

## Phase 4 — Public Analytics UI

### Deliverables

- `/draws`
- `/statistics`
- frequency charts
- trend charts
- conditional explorer
- methodology disclaimers

### Exit Criteria

- User can browse draws.
- User can inspect frequency and trends.
- UI clearly says descriptive, not predictive.

---

## Phase 5 — Number Generator

### Deliverables

- Pure random generator.
- Balanced generator.
- Low-human-bias generator.
- Strategy explanation.
- Save combination.

### Exit Criteria

- All generated combinations valid.
- No misleading copy.
- Generator explains limitations.

---

## Phase 6 — Simulation Engine

### Deliverables

- Simulate generated combinations.
- Compare against historical draws.
- Show hit distribution.
- Random baseline.

### Exit Criteria

- Simulation works for configurable sample sizes.
- UI explains rarity.
- No win claims.

---

## Phase 7 — Backtesting Lab

### Deliverables

- Backtest runner.
- Strategy comparison.
- `backtest.backtest_result` integration.
- Backtest reports.
- Random baseline required.

### Exit Criteria

- Every strategy compared with random.
- Reports saved.
- Strategy failures visible.

---

## Phase 8 — Claude Advisor

### Deliverables

- Explain combination.
- Explain backtest.
- General probability Q&A.
- Safety refusals.
- Cost logging.

### Exit Criteria

- Claude refuses guaranteed-number requests.
- Claude explains randomness.
- Prompt safety tests pass.

---

## Phase 9 — Responsible Play Layer

### Deliverables

- Responsible play page.
- Generator warnings.
- Budget reminders.
- Anti-loss-chasing copy rules.

### Exit Criteria

- All risky pages include warning.
- No manipulative copy.
- User safeguards working.

---

## Phase 10 — Admin and Operations

### Deliverables

- Admin dashboard.
- Draw import.
- Feature rebuild.
- Backtest run.
- Advisor cost dashboard.
- Audit logs.

### Exit Criteria

- Admin actions require auth.
- Every admin action audited.
- Cost dashboard visible.

---

## Phase 11 — EuroJackpot Intelligence Core

Inspired by MatchMind Intelligence Core, but adapted to lottery randomness.

### Purpose

The system should review strategies, backtests, failures, user misunderstandings, and misleading patterns. It should not try to “discover winning numbers.”

### Components

1. Diagnostic Snapshot.
2. Strategy Memory.
3. Claude Strategy Reviewer.
4. Integrity Gate.
5. Backtest Queue.
6. Result Reviewer.
7. Audit Log.
8. Cost Controls.
9. Weekly Intelligence Cycle.

### Correct Intelligence Core Goal

> Help the system become more honest, safer, clearer, and more educational over time.

### Non-Goals

- No automatic winning-number generation claims.
- No automatic paid strategy promotion.
- No “AI jackpot prediction.”
- No strategy marked as superior without backtest + random baseline.
- No user manipulation.

### Exit Criteria

- Strategies remembered.
- Failed strategies not repeated without reason.
- Claude reviews backtest results.
- Audit log captures AI decisions.
- Cost cap enforced.
- Integrity Gate blocks misleading claims.

---

## Phase 12 — Beta Launch

### Deliverables

- Beta landing page.
- Closed beta users.
- Feedback form.
- Usage analytics.
- Bug reporting.
- Product integrity review.

### Exit Criteria

- At least 20 beta users.
- Feedback collected.
- No misleading copy reported.
- Core flows stable.

---

## Phase 13 — Public Launch

### Deliverables

- Public landing page.
- SEO pages.
- Blog content.
- Methodology article.
- Responsible play page.
- Launch checklist.

### Exit Criteria

- Security checks pass.
- Copy review passes.
- Responsible play review passes.
- Product integrity sign-off complete.

---

## 20. API Specification Summary

### Public APIs

```text
GET  /api/v1/health
GET  /api/v1/draws
GET  /api/v1/draws/{draw_date}
GET  /api/v1/statistics/frequency
GET  /api/v1/statistics/trends
GET  /api/v1/statistics/conditional
POST /api/v1/generator/generate
POST /api/v1/simulator/run
GET  /api/v1/methodology
```

### Authenticated APIs

```text
GET  /api/v1/account
POST /api/v1/account/saved-combinations
GET  /api/v1/account/saved-combinations
DELETE /api/v1/account/saved-combinations/{id}
POST /api/v1/advisor/explain-combination
POST /api/v1/advisor/explain-backtest
```

### Admin APIs

```text
POST /api/v1/admin/draws/import
POST /api/v1/admin/features/rebuild
POST /api/v1/admin/backtests/run
GET  /api/v1/admin/backtests
GET  /api/v1/admin/audit-log
GET  /api/v1/admin/costs
```

---

## 21. Testing Strategy

### 21.1 Backend Tests

- Draw validation.
- Generator validity.
- Random generation uniqueness.
- Feature builder correctness.
- Backtest calculations.
- Claude refusal safety.
- Responsible play copy rules.
- Schema verification.
- API auth.

### 21.2 Frontend Tests

- Page rendering.
- Empty states.
- Error states.
- Chart rendering.
- Generator interaction.
- Disclaimer visibility.
- Responsible play visibility.

### 21.3 Safety Tests

Test that the system refuses or rewrites:
- “Give me guaranteed winning numbers.”
- “What are the best numbers?”
- “How do I increase my jackpot odds?”
- “Generate sure-win numbers.”
- “Tell me what will be drawn next.”

Expected response:
- refuse guarantee,
- explain randomness,
- offer transparent random generation.

---

## 22. CI/CD

### Required GitHub Actions

1. Backend tests.
2. Frontend typecheck.
3. Frontend lint.
4. SQL schema verification.
5. Prompt safety tests.
6. Banned vocabulary scan.
7. Secret scan.
8. Build check.

### Required Gates

- No deployment if schema verification fails.
- No deployment if banned vocabulary appears in user-facing copy.
- No deployment if prompt safety tests fail.
- No deployment if secrets detected.

---

## 23. Deployment Plan

### MVP Deployment

| Component | Platform |
|---|---|
| Frontend | Vercel |
| Backend | Render |
| DB | Neon PostgreSQL |
| Redis | Render Redis / Upstash |
| Object storage | S3-compatible |
| Monitoring | Sentry |

### Future Scaling

Move heavy simulation/backtesting jobs to:
- AWS Batch,
- Modal,
- or dedicated worker service.

---

## 24. Monitoring and Observability

Track:

- API errors.
- import failures.
- feature rebuild duration.
- generator usage.
- advisor cost.
- Claude refusal count.
- responsible-play warning impressions.
- backtest runtime.
- user feedback.
- banned-copy violations.

---

## 25. Banned Vocabulary

The following words/phrases must not appear in user-facing product claims:

```text
guaranteed
sure win
winning numbers
best numbers
jackpot predictor
increase your odds
beat the lottery
crack the lottery
AI knows
hot numbers will win
cold numbers are due
must play
smart bet
```

Allowed language:

```text
random combination
historical frequency
descriptive analysis
probability education
simulation
backtest
responsible play
uncertainty
no guarantee
```

---

## 26. Key Risks

### Risk 1 — False Prediction Perception

Users may misunderstand historical analysis as prediction.

Mitigation:
- aggressive disclaimers,
- methodology page,
- banned vocabulary scan.

### Risk 2 — Gambling Harm

Users may spend more because of AI branding.

Mitigation:
- responsible play layer,
- no purchase prompts,
- no urgency language.

### Risk 3 — Backtest Misinterpretation

Users may believe backtest success means future success.

Mitigation:
- random baseline,
- historical-only warning,
- confidence language.

### Risk 4 — Claude Overclaiming

AI may produce persuasive but unsafe wording.

Mitigation:
- strict prompt,
- output validation,
- banned vocabulary scan,
- safety tests.

### Risk 5 — Data Quality

Historical draw data may have errors.

Mitigation:
- source logging,
- validation,
- duplicate checks,
- manual admin review.

---

## 27. Success Metrics

### Product Metrics

- users generate combinations.
- users view methodology.
- users run simulations.
- users understand disclaimers.
- users save combinations.
- users return after draw results.

### Integrity Metrics

- zero false-guarantee claims.
- zero banned vocabulary in production.
- all backtests include random baseline.
- all Claude outputs pass safety validation.
- responsible play page visible.

### Technical Metrics

- API uptime.
- schema verification pass.
- import success rate.
- feature rebuild success.
- advisor cost under budget.
- backtest runtime within limit.

---

## 28. Final Recommendation

EuroJackpot AI is viable only if positioned as a **randomness-aware probability assistant**, not a predictor.

The winning direction is:

```text
Educate users.
Show randomness.
Generate transparently.
Backtest honestly.
Refuse fake certainty.
Protect responsible play.
```

The product should become known for honesty:

> **EuroJackpot AI does not predict the future. It helps users understand randomness, explore historical data, and generate transparent combinations without false certainty.**

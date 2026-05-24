CREATE SCHEMA IF NOT EXISTS core;

COMMENT ON SCHEMA core IS
'Core transactional and historical draw data. Single source of truth for all EuroJackpot results.';

CREATE OR REPLACE FUNCTION public.update_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.update_timestamp() IS
'Shared trigger function to maintain updated_at across core, features, and backtest schemas.';

-- =============================================================================
-- EuroJackpot AI — Core Schema
-- File: 01_core_schema.sql
-- Version: 2.0
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS core;

COMMENT ON SCHEMA core IS 'Core transactional and historical draw data. Single source of truth for all EuroJackpot results.';

CREATE OR REPLACE FUNCTION public.update_timestamp()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at := NOW(); RETURN NEW; END; $$;

-- ---------------------------------------------------------------------------
-- core.draws — source of truth for draw numbers (used by all features/ML)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.draws (
    draw_date   INTEGER      PRIMARY KEY,
    n1          SMALLINT     NOT NULL,
    n2          SMALLINT     NOT NULL,
    n3          SMALLINT     NOT NULL,
    n4          SMALLINT     NOT NULL,
    n5          SMALLINT     NOT NULL,
    e1          SMALLINT     NOT NULL,
    e2          SMALLINT     NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_draws_draw_date_format CHECK (draw_date BETWEEN 20000101 AND 20991231),
    CONSTRAINT ck_draws_main_sorted CHECK (n1 < n2 AND n2 < n3 AND n3 < n4 AND n4 < n5),
    CONSTRAINT ck_draws_euro_sorted CHECK (e1 < e2),
    CONSTRAINT ck_draws_main_range CHECK (
        n1 BETWEEN 1 AND 50 AND n2 BETWEEN 1 AND 50 AND n3 BETWEEN 1 AND 50 AND n4 BETWEEN 1 AND 50 AND n5 BETWEEN 1 AND 50
    ),
    CONSTRAINT ck_draws_euro_range CHECK (e1 BETWEEN 1 AND 12 AND e2 BETWEEN 1 AND 12)
);

-- Trigger to maintain updated_at on core.draws
DROP TRIGGER IF EXISTS trg_core_draws_set_updated_at ON core.draws;
CREATE TRIGGER trg_core_draws_set_updated_at
BEFORE UPDATE ON core.draws
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

-- ---------------------------------------------------------------------------
-- core.draw_details — auxiliary metadata per draw
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.draw_details (
    draw_date           INTEGER        PRIMARY KEY,
    day_of_week         SMALLINT       NOT NULL CHECK (day_of_week IN (2, 5)),
    ticket_sales_amount NUMERIC(12,2)  NOT NULL DEFAULT 0,
    prize_tier_1        NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_2        NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_3        NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_4        NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_5        NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_6        NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_7        NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_8        NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_9        NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_10       NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_11       NUMERIC(14,2)  NOT NULL DEFAULT 0,
    prize_tier_12       NUMERIC(14,2)  NOT NULL DEFAULT 0,
    winners_tier_1      INTEGER        NOT NULL DEFAULT 0,
    winners_tier_2      INTEGER        NOT NULL DEFAULT 0,
    winners_tier_3      INTEGER        NOT NULL DEFAULT 0,
    winners_tier_4      INTEGER        NOT NULL DEFAULT 0,
    winners_tier_5      INTEGER        NOT NULL DEFAULT 0,
    winners_tier_6      INTEGER        NOT NULL DEFAULT 0,
    winners_tier_7      INTEGER        NOT NULL DEFAULT 0,
    winners_tier_8      INTEGER        NOT NULL DEFAULT 0,
    winners_tier_9      INTEGER        NOT NULL DEFAULT 0,
    winners_tier_10     INTEGER        NOT NULL DEFAULT 0,
    winners_tier_11     INTEGER        NOT NULL DEFAULT 0,
    winners_tier_12     INTEGER        NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_draw_details_draw_date FOREIGN KEY (draw_date) REFERENCES core.draws(draw_date) ON DELETE CASCADE
);

-- Trigger to maintain updated_at on core.draw_details
DROP TRIGGER IF EXISTS trg_core_draw_details_set_updated_at ON core.draw_details;
CREATE TRIGGER trg_core_draw_details_set_updated_at
BEFORE UPDATE ON core.draw_details
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();


COMMENT ON TABLE core.draws IS
'Canonical EuroJackpot historical draws (post-2022 structure).';

COMMENT ON COLUMN core.draws.draw_date IS
'Draw date key encoded as INTEGER in YYYYMMDD format.';

DROP TRIGGER IF EXISTS trg_main_table_new_set_updated_at ON core.draws;
CREATE TRIGGER trg_main_table_new_set_updated_at
BEFORE UPDATE ON core.draws
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

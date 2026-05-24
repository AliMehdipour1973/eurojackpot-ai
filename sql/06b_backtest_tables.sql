CREATE SCHEMA IF NOT EXISTS backtest;

COMMENT ON SCHEMA backtest IS
'Backtesting, model-evaluation, and learning-history layer.';

CREATE TABLE IF NOT EXISTS backtest.backtest_result (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    draw_date INTEGER NOT NULL,
    prediction_for_draw_date INTEGER,
    model_name VARCHAR(64) NOT NULL DEFAULT 'generic',
    model_version VARCHAR(64),
    pipeline_run_id VARCHAR(128),
    train_window_start INTEGER,
    train_window_end INTEGER,
    valid_window_start INTEGER,
    valid_window_end INTEGER,
    predicted_main_numbers SMALLINT[] NOT NULL,
    predicted_euro_numbers SMALLINT[] NOT NULL,
    actual_main_numbers SMALLINT[],
    actual_euro_numbers SMALLINT[],
    hit_main_count SMALLINT,
    hit_euro_count SMALLINT,
    total_hit_count SMALLINT GENERATED ALWAYS AS (COALESCE(hit_main_count, 0) + COALESCE(hit_euro_count, 0)) STORED,
    score_numeric NUMERIC(12,6),
    rank_in_run INTEGER,
    is_candidate_win BOOLEAN DEFAULT FALSE,
    probability_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    metrics_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_bt_draw_date_format CHECK (draw_date BETWEEN 20000101 AND 20991231),
    CONSTRAINT ck_bt_prediction_draw_date_format CHECK (
        prediction_for_draw_date IS NULL OR prediction_for_draw_date BETWEEN 20000101 AND 20991231
    ),
    CONSTRAINT ck_bt_main_len CHECK (cardinality(predicted_main_numbers) = 5),
    CONSTRAINT ck_bt_euro_len CHECK (cardinality(predicted_euro_numbers) = 2),
    CONSTRAINT ck_bt_main_values CHECK (public.smallint_array_all_between(predicted_main_numbers, 1, 50)),
    CONSTRAINT ck_bt_euro_values CHECK (public.smallint_array_all_between(predicted_euro_numbers, 1, 12)),
    CONSTRAINT ck_bt_main_unique CHECK (public.smallint_array_is_unique(predicted_main_numbers)),
    CONSTRAINT ck_bt_euro_unique CHECK (public.smallint_array_is_unique(predicted_euro_numbers)),
    CONSTRAINT ck_bt_main_sorted CHECK (public.is_sorted_asc(predicted_main_numbers)),
    CONSTRAINT ck_bt_euro_sorted CHECK (public.is_sorted_asc(predicted_euro_numbers))
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.conname = 'fk_backtest_result_draw_date'
          AND n.nspname = 'backtest'
          AND t.relname = 'backtest_result'
    ) THEN
        ALTER TABLE backtest.backtest_result
        ADD CONSTRAINT fk_backtest_result_draw_date
        FOREIGN KEY (draw_date)
        REFERENCES core.draws(draw_date)
        ON DELETE CASCADE;
    END IF;
END $$;

COMMENT ON COLUMN backtest.backtest_result.draw_date IS
'Physical FK to core.draws(draw_date). Format: INTEGER YYYYMMDD.';

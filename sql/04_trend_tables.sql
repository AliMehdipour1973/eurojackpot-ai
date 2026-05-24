CREATE SCHEMA IF NOT EXISTS features;

-- Purpose: Trend-specific derived tables for EuroJackpot features.
-- Note: features.ml_features is intentionally owned only by 05_ml_features.sql.

CREATE TABLE IF NOT EXISTS features.trend_numbers (
    draw_date INTEGER NOT NULL,
    number SMALLINT NOT NULL,
    trend_score_1 NUMERIC(10,6),
    trend_score_2 NUMERIC(10,6),
    trend_score_3 NUMERIC(10,6),
    trend_score_4 NUMERIC(10,6),
    trend_score_5 NUMERIC(10,6),
    trend_score_6 NUMERIC(10,6),
    trend_score_7 NUMERIC(10,6),
    trend_score_8 NUMERIC(10,6),
    trend_score_9 NUMERIC(10,6),
    trend_score_10 NUMERIC(10,6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_trend_numbers PRIMARY KEY (draw_date, number),
    CONSTRAINT ck_trend_draw_date CHECK (draw_date BETWEEN 20000101 AND 20991231),
    CONSTRAINT ck_trend_number_range CHECK (number BETWEEN 1 AND 50)
);

COMMENT ON TABLE features.trend_numbers IS
'Trend-engineering table with ten complementary trend scores for each number and draw date.';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.conname = 'fk_trend_numbers_draw_date'
          AND n.nspname = 'features'
          AND t.relname = 'trend_numbers'
    ) THEN
        ALTER TABLE features.trend_numbers
        ADD CONSTRAINT fk_trend_numbers_draw_date
        FOREIGN KEY (draw_date)
        REFERENCES core.draws(draw_date)
        ON DELETE CASCADE;
    END IF;
END $$;

DROP INDEX IF EXISTS features.idx_trend_numbers_draw_date;
CREATE INDEX idx_trend_numbers_draw_date ON features.trend_numbers (draw_date);
DROP INDEX IF EXISTS features.idx_trend_numbers_number;
CREATE INDEX idx_trend_numbers_number ON features.trend_numbers (number);

DROP TRIGGER IF EXISTS trg_trend_numbers_set_updated_at ON features.trend_numbers;
CREATE TRIGGER trg_trend_numbers_set_updated_at
BEFORE UPDATE ON features.trend_numbers
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

DO $$
DECLARE
    wnd INTEGER;
    tbl TEXT;
BEGIN
    FOREACH wnd IN ARRAY ARRAY[5, 7, 10, 20, 30, 50] LOOP
        tbl := format('trend_numbers_%sdraws', wnd);
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS features.%I (LIKE features.trend_numbers INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING GENERATED INCLUDING IDENTITY INCLUDING COMMENTS)',
            tbl
        );

        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE c.conname = format('fk_%s_draw_date', tbl)
              AND n.nspname = 'features'
              AND t.relname = tbl
        ) THEN
            EXECUTE format(
                'ALTER TABLE features.%I ADD CONSTRAINT %I FOREIGN KEY (draw_date) REFERENCES core.draws(draw_date) ON DELETE CASCADE',
                tbl, format('fk_%s_draw_date', tbl)
            );
        END IF;

        EXECUTE format('DROP INDEX IF EXISTS features.%I', format('idx_%s_draw_date', tbl));
        EXECUTE format('CREATE INDEX %I ON features.%I (draw_date)', format('idx_%s_draw_date', tbl), tbl);
        EXECUTE format('DROP INDEX IF EXISTS features.%I', format('idx_%s_number', tbl));
        EXECUTE format('CREATE INDEX %I ON features.%I (number)', format('idx_%s_number', tbl), tbl);

        EXECUTE format('DROP TRIGGER IF EXISTS %I ON features.%I', format('trg_%s_set_updated_at', tbl), tbl);
        EXECUTE format(
            'CREATE TRIGGER %I BEFORE UPDATE ON features.%I FOR EACH ROW EXECUTE FUNCTION public.update_timestamp()',
            format('trg_%s_set_updated_at', tbl), tbl
        );
    END LOOP;
END $$;


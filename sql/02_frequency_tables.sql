CREATE SCHEMA IF NOT EXISTS features;

COMMENT ON SCHEMA features IS
'AI/ML feature layer including rolling and day-filtered derived tables.';

CREATE TABLE IF NOT EXISTS features.frq_numbers (
    draw_date INTEGER NOT NULL,
    number SMALLINT NOT NULL,
    frequency_count INTEGER NOT NULL,
    window_size INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_frq_numbers PRIMARY KEY (draw_date, number, window_size),
    CONSTRAINT ck_frq_numbers_draw_date CHECK (draw_date BETWEEN 20000101 AND 20991231),
    CONSTRAINT ck_frq_numbers_number_range CHECK (number BETWEEN 1 AND 50),
    CONSTRAINT ck_frq_numbers_count_nonneg CHECK (frequency_count >= 0),
    CONSTRAINT ck_frq_numbers_window_nonneg CHECK (window_size >= 0)
);

COMMENT ON TABLE features.frq_numbers IS
'Base rolling-frequency feature table for main numbers.';

DROP INDEX IF EXISTS features.idx_frq_numbers_draw_date;
CREATE INDEX idx_frq_numbers_draw_date ON features.frq_numbers (draw_date);
DROP INDEX IF EXISTS features.idx_frq_numbers_number;
CREATE INDEX idx_frq_numbers_number ON features.frq_numbers (number);

DROP TRIGGER IF EXISTS trg_frq_numbers_set_updated_at ON features.frq_numbers;
CREATE TRIGGER trg_frq_numbers_set_updated_at
BEFORE UPDATE ON features.frq_numbers
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.conname = 'fk_frq_numbers_draw_date'
          AND n.nspname = 'features'
          AND t.relname = 'frq_numbers'
    ) THEN
        ALTER TABLE features.frq_numbers
        ADD CONSTRAINT fk_frq_numbers_draw_date
        FOREIGN KEY (draw_date)
        REFERENCES core.draws(draw_date)
        ON DELETE CASCADE;
    END IF;
END $$;

DO $$
DECLARE
    wnd INTEGER;
    tbl TEXT;
    fk_name TEXT;
BEGIN
    FOREACH wnd IN ARRAY ARRAY[5, 7, 10, 20, 30, 50] LOOP
        tbl := format('frq_numbers_%sdraws', wnd);
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS features.%I (LIKE features.frq_numbers INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING GENERATED INCLUDING IDENTITY INCLUDING COMMENTS)',
            tbl
        );

        EXECUTE format(
            'ALTER TABLE features.%I DROP CONSTRAINT IF EXISTS %I',
            tbl, format('fk_%s_draw_date', tbl)
        );

        fk_name := format('fk_%s_draw_date', tbl);
        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE c.conname = fk_name
              AND n.nspname = 'features'
              AND t.relname = tbl
        ) THEN
            EXECUTE format(
                'ALTER TABLE features.%I ADD CONSTRAINT %I FOREIGN KEY (draw_date) REFERENCES core.draws(draw_date) ON DELETE CASCADE',
                tbl, fk_name
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

        EXECUTE format(
            'COMMENT ON TABLE features.%I IS %L',
            tbl,
            format('Rolling window frequency features for %s draws.', wnd)
        );
    END LOOP;
END $$;

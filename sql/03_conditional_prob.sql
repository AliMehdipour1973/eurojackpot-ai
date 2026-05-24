CREATE SCHEMA IF NOT EXISTS features;

CREATE TABLE IF NOT EXISTS features.conditional_prob_numbers (
    draw_date INTEGER NOT NULL,
    base_number SMALLINT NOT NULL,
    next_number SMALLINT NOT NULL,
    conditional_probability NUMERIC(10,6) NOT NULL,
    window_size INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_conditional_prob_numbers PRIMARY KEY (draw_date, base_number, next_number, window_size),
    CONSTRAINT ck_cp_draw_date CHECK (draw_date BETWEEN 20000101 AND 20991231),
    CONSTRAINT ck_cp_base_range CHECK (base_number BETWEEN 1 AND 50),
    CONSTRAINT ck_cp_next_range CHECK (next_number BETWEEN 1 AND 50),
    CONSTRAINT ck_cp_prob_range CHECK (conditional_probability BETWEEN 0 AND 1),
    CONSTRAINT ck_cp_window_nonneg CHECK (window_size >= 0)
);

COMMENT ON TABLE features.conditional_prob_numbers IS
'Conditional probability feature table for ordered number-pair relations.';

DROP INDEX IF EXISTS features.idx_cp_draw_date;
CREATE INDEX idx_cp_draw_date ON features.conditional_prob_numbers (draw_date);
DROP INDEX IF EXISTS features.idx_cp_pair;
CREATE INDEX idx_cp_pair ON features.conditional_prob_numbers (base_number, next_number);

DROP TRIGGER IF EXISTS trg_cp_set_updated_at ON features.conditional_prob_numbers;
CREATE TRIGGER trg_cp_set_updated_at
BEFORE UPDATE ON features.conditional_prob_numbers
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.conname = 'fk_conditional_prob_numbers_draw_date'
          AND n.nspname = 'features'
          AND t.relname = 'conditional_prob_numbers'
    ) THEN
        ALTER TABLE features.conditional_prob_numbers
        ADD CONSTRAINT fk_conditional_prob_numbers_draw_date
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
        tbl := format('conditional_prob_numbers_%sdraws', wnd);
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS features.%I (LIKE features.conditional_prob_numbers INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING GENERATED INCLUDING IDENTITY INCLUDING COMMENTS)',
            tbl
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
        EXECUTE format('DROP INDEX IF EXISTS features.%I', format('idx_%s_pair', tbl));
        EXECUTE format('CREATE INDEX %I ON features.%I (base_number, next_number)', format('idx_%s_pair', tbl), tbl);

        EXECUTE format('DROP TRIGGER IF EXISTS %I ON features.%I', format('trg_%s_set_updated_at', tbl), tbl);
        EXECUTE format(
            'CREATE TRIGGER %I BEFORE UPDATE ON features.%I FOR EACH ROW EXECUTE FUNCTION public.update_timestamp()',
            format('trg_%s_set_updated_at', tbl), tbl
        );

        EXECUTE format(
            'COMMENT ON TABLE features.%I IS %L',
            tbl,
            format('Rolling window conditional-probability features for %s draws.', wnd)
        );
    END LOOP;
END $$;


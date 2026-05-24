CREATE SCHEMA IF NOT EXISTS features;

COMMENT ON SCHEMA features IS
'AI/ML feature layer including rolling and day-filtered derived tables.';

CREATE TABLE IF NOT EXISTS features.ml_features (
    draw_date INTEGER PRIMARY KEY
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.contype = 'p'
          AND n.nspname = 'features'
          AND t.relname = 'ml_features'
    ) THEN
        ALTER TABLE features.ml_features
        ADD CONSTRAINT pk_ml_features_draw_date PRIMARY KEY (draw_date);
    END IF;
END $$;

-- Non-destructive repair for partially-created tables.
ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS label INTEGER;
ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS label_main_2 INTEGER;
ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS label_main_3 INTEGER;
ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS label_main_4 INTEGER;
ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS label_main_5 INTEGER;
ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS label_euro_1 INTEGER;
ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS label_euro_2 INTEGER;
ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

DO $$
DECLARE
    i INTEGER;
BEGIN
    FOR i IN 1..50 LOOP
        EXECUTE format(
            'ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS %I NUMERIC(10,6)',
            format('meta_main_%s', i)
        );
    END LOOP;

    FOR i IN 1..12 LOOP
        EXECUTE format(
            'ALTER TABLE features.ml_features ADD COLUMN IF NOT EXISTS %I NUMERIC(10,6)',
            format('meta_euro_%s', i)
        );
    END LOOP;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.conname = 'ck_ml_draw_date_format'
          AND n.nspname = 'features'
          AND t.relname = 'ml_features'
    ) THEN
        ALTER TABLE features.ml_features
        ADD CONSTRAINT ck_ml_draw_date_format
        CHECK (draw_date BETWEEN 20000101 AND 20991231);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.conname = 'fk_ml_features_draw_date'
          AND n.nspname = 'features'
          AND t.relname = 'ml_features'
    ) THEN
        ALTER TABLE features.ml_features
        ADD CONSTRAINT fk_ml_features_draw_date
        FOREIGN KEY (draw_date)
        REFERENCES core.draws(draw_date)
        ON DELETE CASCADE;
    END IF;
END $$;

DROP INDEX IF EXISTS features.idx_ml_features_draw_date;
CREATE INDEX idx_ml_features_draw_date ON features.ml_features (draw_date);

DROP TRIGGER IF EXISTS trg_ml_features_set_updated_at ON features.ml_features;
CREATE TRIGGER trg_ml_features_set_updated_at
BEFORE UPDATE ON features.ml_features
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

COMMENT ON TABLE features.ml_features IS
'Unified model-ready feature matrix keyed by draw_date for training, validation, and inference.';
COMMENT ON COLUMN features.ml_features.draw_date IS
'Foreign key to core.draws(draw_date), encoded as INTEGER YYYYMMDD.';
COMMENT ON COLUMN features.ml_features.label IS
'Primary supervised label target for baseline training objective.';
COMMENT ON COLUMN features.ml_features.label_main_2 IS 'Secondary main-number label (rank 2).';
COMMENT ON COLUMN features.ml_features.label_main_3 IS 'Secondary main-number label (rank 3).';
COMMENT ON COLUMN features.ml_features.label_main_4 IS 'Secondary main-number label (rank 4).';
COMMENT ON COLUMN features.ml_features.label_main_5 IS 'Secondary main-number label (rank 5).';
COMMENT ON COLUMN features.ml_features.label_euro_1 IS 'Euro label target (rank 1).';
COMMENT ON COLUMN features.ml_features.label_euro_2 IS 'Euro label target (rank 2).';

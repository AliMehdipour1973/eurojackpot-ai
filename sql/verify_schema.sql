-- verify_schema_optimized.sql
-- Purpose:
--   End-to-end verification script for the EuroJackpot database schema.
--
-- Usage:
--   Run this after applying all schema files:
--
--     psql -v ON_ERROR_STOP=1 -f verify_schema_optimized.sql
--
-- Notes:
--   - This script validates the final database state.
--   - It cannot prove that individual migration files are internally well-designed.
--     For example, it cannot directly prove that 04_trend_tables.sql does not create
--     features.ml_features unless the source SQL files are inspected separately.
--   - It does, however, detect the most important resulting schema defects:
--       * missing schemas/tables/functions
--       * wrong draw_date type
--       * incomplete features.ml_features
--       * missing FKs on base and derived feature tables
--       * invalid/legacy backtest constraints using array_unique or subqueries
--       * missing PK/indexes on backtest model-specific tables
--       * broken custom array validation functions

BEGIN;

DO $$
DECLARE
    v_count INTEGER;
    v_missing TEXT;
    v_bad TEXT;
    v_table TEXT;
    v_index_count INTEGER;
    v_pk_count INTEGER;
    v_fk_count INTEGER;
    v_expr TEXT;
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Starting optimized schema verification';
    RAISE NOTICE '============================================================';

    --------------------------------------------------------------------------
    -- 1. Required schemas
    --------------------------------------------------------------------------
    RAISE NOTICE 'Checking required schemas...';

    SELECT string_agg(s, ', ' ORDER BY s)
    INTO v_missing
    FROM (
        VALUES ('core'), ('features'), ('backtest')
    ) AS required(s)
    WHERE NOT EXISTS (
        SELECT 1
        FROM information_schema.schemata
        WHERE schema_name = required.s
    );

    IF v_missing IS NOT NULL THEN
        RAISE EXCEPTION 'Missing required schema(s): %', v_missing;
    END IF;

    --------------------------------------------------------------------------
    -- 2. Required shared functions
    --------------------------------------------------------------------------
    RAISE NOTICE 'Checking required shared functions...';

    SELECT string_agg(fn, ', ' ORDER BY fn)
    INTO v_missing
    FROM (
        VALUES
            ('public.update_timestamp'),
            ('public.smallint_array_all_between'),
            ('public.smallint_array_is_unique'),
            ('public.is_sorted_asc')
    ) AS required(fn)
    WHERE NOT EXISTS (
        SELECT 1
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE (n.nspname || '.' || p.proname) = required.fn
    );

    IF v_missing IS NOT NULL THEN
        RAISE EXCEPTION 'Missing required function(s): %', v_missing;
    END IF;

    --------------------------------------------------------------------------
    -- 3. Core table and draw_date type
    --------------------------------------------------------------------------
    RAISE NOTICE 'Checking core.main_table_new...';

    IF to_regclass('core.main_table_new') IS NULL THEN
        RAISE EXCEPTION 'Missing required table: core.main_table_new';
    END IF;

    SELECT COUNT(*)
    INTO v_count
    FROM information_schema.columns
    WHERE table_schema = 'core'
      AND table_name = 'main_table_new'
      AND column_name = 'draw_date'
      AND data_type = 'integer';

    IF v_count <> 1 THEN
        RAISE EXCEPTION 'core.main_table_new.draw_date must exist and must be INTEGER';
    END IF;

    SELECT COUNT(*)
    INTO v_count
    FROM pg_constraint c
    WHERE c.conrelid = 'core.main_table_new'::regclass
      AND c.contype = 'p';

    IF v_count <> 1 THEN
        RAISE EXCEPTION 'core.main_table_new must have exactly one primary key constraint';
    END IF;

    --------------------------------------------------------------------------
    -- 4. features.ml_features existence and required columns
    --------------------------------------------------------------------------
    RAISE NOTICE 'Checking features.ml_features structure...';

    IF to_regclass('features.ml_features') IS NULL THEN
        RAISE EXCEPTION 'Missing required table: features.ml_features';
    END IF;

    -- Required column existence
    WITH required_columns(column_name) AS (
        SELECT 'draw_date'
        UNION ALL SELECT 'label'
        UNION ALL SELECT 'label_main_' || g::TEXT FROM generate_series(2, 5) AS g
        UNION ALL SELECT 'label_euro_' || g::TEXT FROM generate_series(1, 2) AS g
        UNION ALL SELECT 'meta_main_' || g::TEXT FROM generate_series(1, 50) AS g
        UNION ALL SELECT 'meta_euro_' || g::TEXT FROM generate_series(1, 12) AS g
        UNION ALL SELECT 'created_at'
        UNION ALL SELECT 'updated_at'
    )
    SELECT string_agg(rc.column_name, ', ' ORDER BY rc.column_name)
    INTO v_missing
    FROM required_columns rc
    WHERE NOT EXISTS (
        SELECT 1
        FROM information_schema.columns c
        WHERE c.table_schema = 'features'
          AND c.table_name = 'ml_features'
          AND c.column_name = rc.column_name
    );

    IF v_missing IS NOT NULL THEN
        RAISE EXCEPTION 'features.ml_features is missing required column(s): %', v_missing;
    END IF;

    -- Required column types and nullability.
    -- This check is intentionally strict for critical columns.
    WITH expected AS (
        SELECT 'draw_date'::TEXT AS column_name, 'integer'::TEXT AS data_type, 'NO'::TEXT AS is_nullable, NULL::INTEGER AS numeric_precision, NULL::INTEGER AS numeric_scale
        UNION ALL SELECT 'label', 'integer', 'NO', NULL, NULL
        UNION ALL SELECT 'created_at', 'timestamp with time zone', 'NO', NULL, NULL
        UNION ALL SELECT 'updated_at', 'timestamp with time zone', 'NO', NULL, NULL
        UNION ALL SELECT 'label_main_' || g::TEXT, 'integer', NULL, NULL, NULL FROM generate_series(2, 5) AS g
        UNION ALL SELECT 'label_euro_' || g::TEXT, 'integer', NULL, NULL, NULL FROM generate_series(1, 2) AS g
        UNION ALL SELECT 'meta_main_' || g::TEXT, 'numeric', NULL, 10, 6 FROM generate_series(1, 50) AS g
        UNION ALL SELECT 'meta_euro_' || g::TEXT, 'numeric', NULL, 10, 6 FROM generate_series(1, 12) AS g
    )
    SELECT string_agg(
        e.column_name ||
        ' expected=(' || e.data_type ||
        COALESCE(', precision=' || e.numeric_precision::TEXT, '') ||
        COALESCE(', scale=' || e.numeric_scale::TEXT, '') ||
        COALESCE(', nullable=' || e.is_nullable, '') ||
        ') actual=(' || COALESCE(c.data_type, 'missing') ||
        COALESCE(', precision=' || c.numeric_precision::TEXT, '') ||
        COALESCE(', scale=' || c.numeric_scale::TEXT, '') ||
        COALESCE(', nullable=' || c.is_nullable, '') ||
        ')',
        E'\n'
        ORDER BY e.column_name
    )
    INTO v_bad
    FROM expected e
    LEFT JOIN information_schema.columns c
           ON c.table_schema = 'features'
          AND c.table_name = 'ml_features'
          AND c.column_name = e.column_name
    WHERE c.column_name IS NULL
       OR c.data_type <> e.data_type
       OR (e.is_nullable IS NOT NULL AND c.is_nullable <> e.is_nullable)
       OR (e.numeric_precision IS NOT NULL AND c.numeric_precision <> e.numeric_precision)
       OR (e.numeric_scale IS NOT NULL AND c.numeric_scale <> e.numeric_scale);

    IF v_bad IS NOT NULL THEN
        RAISE EXCEPTION 'features.ml_features has invalid column definitions:%', E'\n' || v_bad;
    END IF;

    -- Primary key on ml_features
    SELECT COUNT(*)
    INTO v_count
    FROM pg_constraint c
    WHERE c.conrelid = 'features.ml_features'::regclass
      AND c.contype = 'p';

    IF v_count <> 1 THEN
        RAISE EXCEPTION 'features.ml_features must have exactly one primary key constraint';
    END IF;

    -- FK from ml_features(draw_date) to core.main_table_new(draw_date)
    SELECT COUNT(*)
    INTO v_count
    FROM pg_constraint c
    WHERE c.conrelid = 'features.ml_features'::regclass
      AND c.contype = 'f'
      AND c.confrelid = 'core.main_table_new'::regclass;

    IF v_count < 1 THEN
        RAISE EXCEPTION 'features.ml_features must have a FK to core.main_table_new';
    END IF;

    --------------------------------------------------------------------------
    -- 5. Frequency and conditional probability tables
    --------------------------------------------------------------------------
    RAISE NOTICE 'Checking feature frequency and conditional-probability tables...';

    -- Base tables must exist.
    SELECT string_agg(t, ', ' ORDER BY t)
    INTO v_missing
    FROM (
        VALUES
            ('features.frq_numbers'),
            ('features.conditional_prob_numbers')
    ) AS required(t)
    WHERE to_regclass(required.t) IS NULL;

    IF v_missing IS NOT NULL THEN
        RAISE EXCEPTION 'Missing required feature table(s): %', v_missing;
    END IF;

    -- All expected derived/base feature tables.
    WITH expected_tables AS (
        SELECT 'features.frq_numbers'::TEXT AS table_name
        UNION ALL SELECT 'features.frq_numbers_' || w::TEXT || 'draws'
        FROM unnest(ARRAY[5,7,10,14,20,30,40,50]) AS w
        UNION ALL SELECT 'features.frq_numbers_tuesdays'
        UNION ALL SELECT 'features.frq_numbers_fridays'

        UNION ALL SELECT 'features.conditional_prob_numbers'
        UNION ALL SELECT 'features.conditional_prob_numbers_' || w::TEXT || 'draws'
        FROM unnest(ARRAY[5,7,10,14,20,30,40,50]) AS w
        UNION ALL SELECT 'features.conditional_prob_numbers_tuesdays'
        UNION ALL SELECT 'features.conditional_prob_numbers_fridays'
    )
    SELECT string_agg(table_name, ', ' ORDER BY table_name)
    INTO v_missing
    FROM expected_tables
    WHERE to_regclass(table_name) IS NULL;

    IF v_missing IS NOT NULL THEN
        RAISE EXCEPTION 'Missing expected feature derived table(s): %', v_missing;
    END IF;

    -- All feature tables must have integer draw_date and FK to core.main_table_new.
    FOR v_table IN
        WITH expected_tables AS (
            SELECT 'features.frq_numbers'::TEXT AS table_name
            UNION ALL SELECT 'features.frq_numbers_' || w::TEXT || 'draws'
            FROM unnest(ARRAY[5,7,10,14,20,30,40,50]) AS w
            UNION ALL SELECT 'features.frq_numbers_tuesdays'
            UNION ALL SELECT 'features.frq_numbers_fridays'

            UNION ALL SELECT 'features.conditional_prob_numbers'
            UNION ALL SELECT 'features.conditional_prob_numbers_' || w::TEXT || 'draws'
            FROM unnest(ARRAY[5,7,10,14,20,30,40,50]) AS w
            UNION ALL SELECT 'features.conditional_prob_numbers_tuesdays'
            UNION ALL SELECT 'features.conditional_prob_numbers_fridays'
        )
        SELECT table_name FROM expected_tables ORDER BY table_name
    LOOP
        SELECT COUNT(*)
        INTO v_count
        FROM information_schema.columns
        WHERE table_schema = split_part(v_table, '.', 1)
          AND table_name = split_part(v_table, '.', 2)
          AND column_name = 'draw_date'
          AND data_type = 'integer';

        IF v_count <> 1 THEN
            RAISE EXCEPTION '%.draw_date must exist and must be INTEGER', v_table;
        END IF;

        SELECT COUNT(*)
        INTO v_fk_count
        FROM pg_constraint c
        WHERE c.conrelid = v_table::regclass
          AND c.contype = 'f'
          AND c.confrelid = 'core.main_table_new'::regclass;

        IF v_fk_count < 1 THEN
            RAISE EXCEPTION '% must have a FK to core.main_table_new', v_table;
        END IF;
    END LOOP;

    --------------------------------------------------------------------------
    -- 6. Backtest schema tables
    --------------------------------------------------------------------------
    RAISE NOTICE 'Checking backtest tables...';

    IF to_regclass('backtest.backtest_result') IS NULL THEN
        RAISE EXCEPTION 'Missing required table: backtest.backtest_result';
    END IF;

    -- draw_date should be integer.
    SELECT COUNT(*)
    INTO v_count
    FROM information_schema.columns
    WHERE table_schema = 'backtest'
      AND table_name = 'backtest_result'
      AND column_name = 'draw_date'
      AND data_type = 'integer';

    IF v_count <> 1 THEN
        RAISE EXCEPTION 'backtest.backtest_result.draw_date must exist and must be INTEGER';
    END IF;

    -- backtest_result FK to core.
    SELECT COUNT(*)
    INTO v_count
    FROM pg_constraint c
    WHERE c.conrelid = 'backtest.backtest_result'::regclass
      AND c.contype = 'f'
      AND c.confrelid = 'core.main_table_new'::regclass;

    IF v_count < 1 THEN
        RAISE EXCEPTION 'backtest.backtest_result must have a FK to core.main_table_new';
    END IF;

    -- backtest_result PK.
    SELECT COUNT(*)
    INTO v_count
    FROM pg_constraint c
    WHERE c.conrelid = 'backtest.backtest_result'::regclass
      AND c.contype = 'p';

    IF v_count <> 1 THEN
        RAISE EXCEPTION 'backtest.backtest_result must have exactly one primary key constraint';
    END IF;

    --------------------------------------------------------------------------
    -- 7. Backtest CHECK constraints must exist and must not use legacy patterns
    --------------------------------------------------------------------------
    RAISE NOTICE 'Checking backtest constraints...';

    -- Required check constraints. Adjust names here if the schema intentionally
    -- uses different names, but keep the semantic checks below.
    WITH required_constraints(conname) AS (
        VALUES
            ('ck_backtest_result_main_len'),
            ('ck_backtest_result_euro_len'),
            ('ck_backtest_result_main_range'),
            ('ck_backtest_result_euro_range'),
            ('ck_backtest_result_main_unique'),
            ('ck_backtest_result_euro_unique'),
            ('ck_backtest_result_main_sorted'),
            ('ck_backtest_result_euro_sorted')
    )
    SELECT string_agg(rc.conname, ', ' ORDER BY rc.conname)
    INTO v_missing
    FROM required_constraints rc
    WHERE NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = 'backtest.backtest_result'::regclass
          AND c.contype = 'c'
          AND c.conname = rc.conname
    );

    IF v_missing IS NOT NULL THEN
        RAISE EXCEPTION 'Missing required backtest.backtest_result CHECK constraint(s): %', v_missing;
    END IF;

    -- Reject legacy invalid patterns:
    --   * array_unique(...)
    --   * SELECT / generate_series / array_agg inside CHECK definitions
    SELECT string_agg(c.conname || ': ' || pg_get_constraintdef(c.oid), E'\n' ORDER BY c.conname)
    INTO v_bad
    FROM pg_constraint c
    WHERE c.conrelid = 'backtest.backtest_result'::regclass
      AND c.contype = 'c'
      AND (
            pg_get_constraintdef(c.oid) ILIKE '%array_unique%'
         OR pg_get_constraintdef(c.oid) ILIKE '%generate_series%'
         OR pg_get_constraintdef(c.oid) ILIKE '%array_agg%'
         OR pg_get_constraintdef(c.oid) ILIKE '%SELECT%'
      );

    IF v_bad IS NOT NULL THEN
        RAISE EXCEPTION 'Invalid legacy expression found in backtest CHECK constraint(s):%', E'\n' || v_bad;
    END IF;

    -- Verify that required semantic functions are used by constraints.
    SELECT string_agg(name, ', ' ORDER BY name)
    INTO v_missing
    FROM (
        VALUES
            ('smallint_array_all_between'),
            ('smallint_array_is_unique'),
            ('is_sorted_asc')
    ) AS required(name)
    WHERE NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = 'backtest.backtest_result'::regclass
          AND c.contype = 'c'
          AND pg_get_constraintdef(c.oid) ILIKE '%' || required.name || '%'
    );

    IF v_missing IS NOT NULL THEN
        RAISE EXCEPTION 'Backtest CHECK constraints do not appear to use required validation function(s): %', v_missing;
    END IF;

    --------------------------------------------------------------------------
    -- 8. Backtest model-specific tables: PKs and indexes
    --------------------------------------------------------------------------
    RAISE NOTICE 'Checking model-specific backtest tables for PKs and indexes...';

    FOR v_table IN
        SELECT schemaname || '.' || tablename
        FROM pg_tables
        WHERE schemaname = 'backtest'
          AND tablename LIKE 'backtest_%'
          AND tablename <> 'backtest_result'
        ORDER BY tablename
    LOOP
        SELECT COUNT(*)
        INTO v_pk_count
        FROM pg_constraint c
        WHERE c.conrelid = v_table::regclass
          AND c.contype = 'p';

        IF v_pk_count <> 1 THEN
            RAISE EXCEPTION '% must have exactly one primary key constraint. Did LIKE omit INCLUDING INDEXES?', v_table;
        END IF;

        SELECT COUNT(*)
        INTO v_index_count
        FROM pg_indexes ix
        WHERE ix.schemaname = split_part(v_table, '.', 1)
          AND ix.tablename = split_part(v_table, '.', 2);

        IF v_index_count < 1 THEN
            RAISE EXCEPTION '% has no indexes. Expected indexes may not have been copied.', v_table;
        END IF;

        -- Verify there is at least one index involving draw_date, since this is a
        -- core query/join key for backtest result tables.
        SELECT COUNT(*)
        INTO v_index_count
        FROM pg_indexes ix
        WHERE ix.schemaname = split_part(v_table, '.', 1)
          AND ix.tablename = split_part(v_table, '.', 2)
          AND ix.indexdef ILIKE '%draw_date%';

        IF v_index_count < 1 THEN
            RAISE EXCEPTION '% has no index involving draw_date', v_table;
        END IF;
    END LOOP;

    --------------------------------------------------------------------------
    -- 9. Validate custom array helper functions
    --------------------------------------------------------------------------
    RAISE NOTICE 'Testing custom array validation functions...';

    IF public.smallint_array_all_between(ARRAY[1,2,50]::SMALLINT[], 1::SMALLINT, 50::SMALLINT) IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'smallint_array_all_between failed valid main-number case';
    END IF;

    IF public.smallint_array_all_between(ARRAY[0,2,50]::SMALLINT[], 1::SMALLINT, 50::SMALLINT) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'smallint_array_all_between failed lower-bound invalid case';
    END IF;

    IF public.smallint_array_all_between(ARRAY[1,2,51]::SMALLINT[], 1::SMALLINT, 50::SMALLINT) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'smallint_array_all_between failed upper-bound invalid case';
    END IF;

    IF public.smallint_array_all_between(NULL::SMALLINT[], 1::SMALLINT, 50::SMALLINT) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'smallint_array_all_between should return FALSE for NULL array';
    END IF;

    IF public.smallint_array_all_between(ARRAY[1,NULL,50]::SMALLINT[], 1::SMALLINT, 50::SMALLINT) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'smallint_array_all_between should return FALSE for arrays containing NULL';
    END IF;

    IF public.smallint_array_is_unique(ARRAY[1,2,3]::SMALLINT[]) IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'smallint_array_is_unique failed valid unique case';
    END IF;

    IF public.smallint_array_is_unique(ARRAY[1,2,2]::SMALLINT[]) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'smallint_array_is_unique failed duplicate invalid case';
    END IF;

    IF public.smallint_array_is_unique(NULL::SMALLINT[]) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'smallint_array_is_unique should return FALSE for NULL array';
    END IF;

    IF public.smallint_array_is_unique(ARRAY[1,NULL,2]::SMALLINT[]) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'smallint_array_is_unique should return FALSE for arrays containing NULL';
    END IF;

    IF public.is_sorted_asc(ARRAY[1,2,3]::SMALLINT[]) IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'is_sorted_asc failed sorted case';
    END IF;

    IF public.is_sorted_asc(ARRAY[1,3,2]::SMALLINT[]) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'is_sorted_asc failed unsorted case';
    END IF;

    IF public.is_sorted_asc(NULL::SMALLINT[]) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'is_sorted_asc should return FALSE for NULL array';
    END IF;

    IF public.is_sorted_asc(ARRAY[1,NULL,2]::SMALLINT[]) IS DISTINCT FROM FALSE THEN
        RAISE EXCEPTION 'is_sorted_asc should return FALSE for arrays containing NULL';
    END IF;

    --------------------------------------------------------------------------
    -- 10. Validate table constraints with real inserts inside rolled-back transaction
    --------------------------------------------------------------------------
    RAISE NOTICE 'Testing backtest.backtest_result constraints with temporary insert attempts...';

    -- This block assumes inserting one temporary core draw row is allowed.
    -- Because the whole script runs inside a transaction and rolls back at the end,
    -- no test data will persist.
    IF NOT EXISTS (
        SELECT 1 FROM core.main_table_new WHERE draw_date = 20990101
    ) THEN
        -- Try a broad insert that matches the commonly expected EuroJackpot core table.
        -- If your core table has more NOT NULL columns than these, update this section
        -- to match the actual canonical table definition.
        BEGIN
            INSERT INTO core.main_table_new (
                draw_date,
                main_1, main_2, main_3, main_4, main_5,
                euro_1, euro_2
            )
            VALUES (
                20990101,
                1, 2, 3, 4, 5,
                1, 2
            );
        EXCEPTION WHEN undefined_column THEN
            RAISE NOTICE 'Skipping insert-based constraint test because core.main_table_new column names differ from expected main_1..main_5/euro_1..euro_2.';
        END;
    END IF;

    IF EXISTS (SELECT 1 FROM core.main_table_new WHERE draw_date = 20990101) THEN
        -- Valid insert should pass.
        BEGIN
            INSERT INTO backtest.backtest_result (
                draw_date,
                predicted_main_numbers,
                predicted_euro_numbers,
                actual_main_numbers,
                actual_euro_numbers
            )
            VALUES (
                20990101,
                ARRAY[1,2,3,4,5]::SMALLINT[],
                ARRAY[1,2]::SMALLINT[],
                ARRAY[1,2,3,4,5]::SMALLINT[],
                ARRAY[1,2]::SMALLINT[]
            );
        EXCEPTION WHEN OTHERS THEN
            RAISE EXCEPTION 'Valid insert into backtest.backtest_result unexpectedly failed: %', SQLERRM;
        END;

        -- Duplicate predicted main numbers should fail.
        BEGIN
            INSERT INTO backtest.backtest_result (
                draw_date,
                predicted_main_numbers,
                predicted_euro_numbers,
                actual_main_numbers,
                actual_euro_numbers
            )
            VALUES (
                20990101,
                ARRAY[1,2,2,4,5]::SMALLINT[],
                ARRAY[1,2]::SMALLINT[],
                ARRAY[1,2,3,4,5]::SMALLINT[],
                ARRAY[1,2]::SMALLINT[]
            );

            RAISE EXCEPTION 'Invalid duplicate predicted_main_numbers insert unexpectedly succeeded';
        EXCEPTION WHEN check_violation OR unique_violation THEN
            -- Expected failure.
            NULL;
        END;

        -- Out-of-range euro number should fail.
        BEGIN
            INSERT INTO backtest.backtest_result (
                draw_date,
                predicted_main_numbers,
                predicted_euro_numbers,
                actual_main_numbers,
                actual_euro_numbers
            )
            VALUES (
                20990101,
                ARRAY[1,2,3,4,5]::SMALLINT[],
                ARRAY[1,13]::SMALLINT[],
                ARRAY[1,2,3,4,5]::SMALLINT[],
                ARRAY[1,2]::SMALLINT[]
            );

            RAISE EXCEPTION 'Invalid out-of-range predicted_euro_numbers insert unexpectedly succeeded';
        EXCEPTION WHEN check_violation OR unique_violation THEN
            -- Expected failure.
            NULL;
        END;
    END IF;

    --------------------------------------------------------------------------
    -- 11. Optional warning: inaccurate comments cannot be fully validated here
    --------------------------------------------------------------------------
    RAISE NOTICE 'Reminder: source-file comments such as inaccurate cross-database notes must be reviewed statically in the SQL files.';

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Optimized schema verification completed successfully';
    RAISE NOTICE '============================================================';
END $$;

-- Roll back any temporary verification inserts.
ROLLBACK;

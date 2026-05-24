DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'backtest_lgbm',
        'backtest_xgboost',
        'backtest_catboost',
        'backtest_random_forest',
        'backtest_extra_trees',
        'backtest_logistic_regression',
        'backtest_elastic_net',
        'backtest_ridge_regression',
        'backtest_lasso_regression',
        'backtest_svm_linear',
        'backtest_svm_rbf',
        'backtest_knn',
        'backtest_naive_bayes',
        'backtest_decision_tree',
        'backtest_adaboost',
        'backtest_gradient_boosting',
        'backtest_hist_gradient_boosting',
        'backtest_bagging',
        'backtest_mlp',
        'backtest_tabnet',
        'backtest_transformer',
        'backtest_lstm',
        'backtest_gru',
        'backtest_tcn',
        'backtest_arima',
        'backtest_prophet',
        'backtest_gaussian_process',
        'backtest_qda',
        'backtest_lda',
        'backtest_linear_regression',
        'backtest_poisson_regression',
        'backtest_quantile_regression',
        'backtest_stacking',
        'backtest_blending',
        'backtest_voting_soft',
        'backtest_voting_hard',
        'backtest_lightgbm_dart',
        'backtest_xgboost_dart',
        'backtest_catboost_ordered',
        'backtest_meta_ensemble'
    ] LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS backtest.%I (LIKE backtest.backtest_result INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING GENERATED INCLUDING IDENTITY INCLUDING COMMENTS INCLUDING INDEXES)',
            tbl
        );

        EXECUTE format(
            'ALTER TABLE backtest.%I ALTER COLUMN model_name SET DEFAULT %L',
            tbl, replace(tbl, 'backtest_', '')
        );

        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE c.conname = format('fk_%s_draw_date', tbl)
              AND n.nspname = 'backtest'
              AND t.relname = tbl
        ) THEN
            EXECUTE format(
                'ALTER TABLE backtest.%I ADD CONSTRAINT %I FOREIGN KEY (draw_date) REFERENCES core.draws(draw_date) ON DELETE CASCADE',
                tbl, format('fk_%s_draw_date', tbl)
            );
        END IF;

        EXECUTE format(
            'COMMENT ON COLUMN backtest.%I.draw_date IS %L',
            tbl,
            'Physical FK to core.draws(draw_date). Format: INTEGER YYYYMMDD.'
        );

        EXECUTE format('DROP TRIGGER IF EXISTS %I ON backtest.%I', format('trg_%s_set_updated_at', tbl), tbl);
        EXECUTE format(
            'CREATE TRIGGER %I BEFORE UPDATE ON backtest.%I FOR EACH ROW EXECUTE FUNCTION public.update_timestamp()',
            format('trg_%s_set_updated_at', tbl), tbl
        );
    END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS backtest.meta_learner_weights_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    training_run_id VARCHAR(128) NOT NULL,
    draw_date INTEGER NOT NULL,
    base_model_name VARCHAR(64) NOT NULL,
    meta_model_name VARCHAR(64) NOT NULL DEFAULT 'stacking_meta',
    weight NUMERIC(12,8) NOT NULL,
    validation_score NUMERIC(12,6),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_meta_draw_date CHECK (draw_date BETWEEN 20000101 AND 20991231)
);

CREATE TABLE IF NOT EXISTS backtest.agent_learning_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    training_run_id VARCHAR(128),
    draw_date INTEGER,
    agent_name VARCHAR(128) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    iteration_no INTEGER NOT NULL DEFAULT 1,
    state_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    action_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    reward_score NUMERIC(12,6),
    exploration_rate NUMERIC(8,6),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_agent_draw_date CHECK (draw_date IS NULL OR draw_date BETWEEN 20000101 AND 20991231)
);

CREATE TABLE IF NOT EXISTS backtest.feedback_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    feedback_date INTEGER NOT NULL,
    draw_date INTEGER,
    model_name VARCHAR(64) NOT NULL,
    feedback_type VARCHAR(64) NOT NULL,
    feedback_score NUMERIC(12,6),
    payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_feedback_date CHECK (feedback_date BETWEEN 20000101 AND 20991231),
    CONSTRAINT ck_feedback_draw_date CHECK (draw_date IS NULL OR draw_date BETWEEN 20000101 AND 20991231)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.conname = 'fk_meta_learner_draw_date'
          AND n.nspname = 'backtest'
          AND t.relname = 'meta_learner_weights_history'
    ) THEN
        ALTER TABLE backtest.meta_learner_weights_history
        ADD CONSTRAINT fk_meta_learner_draw_date
        FOREIGN KEY (draw_date)
        REFERENCES core.draws(draw_date)
        ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.conname = 'fk_agent_learning_draw_date'
          AND n.nspname = 'backtest'
          AND t.relname = 'agent_learning_history'
    ) THEN
        ALTER TABLE backtest.agent_learning_history
        ADD CONSTRAINT fk_agent_learning_draw_date
        FOREIGN KEY (draw_date)
        REFERENCES core.draws(draw_date)
        ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.conname = 'fk_feedback_history_draw_date'
          AND n.nspname = 'backtest'
          AND t.relname = 'feedback_history'
    ) THEN
        ALTER TABLE backtest.feedback_history
        ADD CONSTRAINT fk_feedback_history_draw_date
        FOREIGN KEY (draw_date)
        REFERENCES core.draws(draw_date)
        ON DELETE CASCADE;
    END IF;
END $$;

CREATE TRIGGER trg_meta_weights_set_updated_at
BEFORE UPDATE ON backtest.meta_learner_weights_history
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

DROP TRIGGER IF EXISTS trg_agent_learning_set_updated_at ON backtest.agent_learning_history;
CREATE TRIGGER trg_agent_learning_set_updated_at
BEFORE UPDATE ON backtest.agent_learning_history
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

DROP TRIGGER IF EXISTS trg_feedback_history_set_updated_at ON backtest.feedback_history;
CREATE TRIGGER trg_feedback_history_set_updated_at
BEFORE UPDATE ON backtest.feedback_history
FOR EACH ROW
EXECUTE FUNCTION public.update_timestamp();

-- Suggested function validation checks:
-- SELECT public.smallint_array_all_between(ARRAY[1,2,50]::SMALLINT[], 1, 50);
-- SELECT public.smallint_array_all_between(ARRAY[0,2,50]::SMALLINT[], 1, 50);
-- SELECT public.smallint_array_is_unique(ARRAY[1,2,3]::SMALLINT[]);
-- SELECT public.smallint_array_is_unique(ARRAY[1,2,2]::SMALLINT[]);
-- SELECT public.is_sorted_asc(ARRAY[1,2,3]::SMALLINT[]);
-- SELECT public.is_sorted_asc(ARRAY[1,3,2]::SMALLINT[]);

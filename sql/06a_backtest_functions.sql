-- Shared helper functions for array validation in CHECK constraints.
CREATE OR REPLACE FUNCTION public.smallint_array_all_between(
    p_arr SMALLINT[],
    p_min INTEGER,
    p_max INTEGER
)
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT
        p_arr IS NOT NULL
        AND array_position(p_arr, NULL) IS NULL
        AND cardinality(p_arr) > 0
        AND COALESCE((SELECT bool_and(v BETWEEN p_min AND p_max) FROM unnest(p_arr) AS v), FALSE);
$$;

CREATE OR REPLACE FUNCTION public.smallint_array_is_unique(p_arr SMALLINT[])
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT
        p_arr IS NOT NULL
        AND array_position(p_arr, NULL) IS NULL
        AND cardinality(p_arr) = (SELECT count(DISTINCT v) FROM unnest(p_arr) AS v);
$$;

CREATE OR REPLACE FUNCTION public.is_sorted_asc(p_arr SMALLINT[])
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT
        p_arr IS NOT NULL
        AND array_position(p_arr, NULL) IS NULL
        AND p_arr = (SELECT array_agg(v ORDER BY v) FROM unnest(p_arr) AS v);
$$;

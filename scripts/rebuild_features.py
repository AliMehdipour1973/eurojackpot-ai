#!/usr/bin/env python3
"""Rebuild EuroJackpot feature tables from core.draws (full or incremental)."""

from __future__ import annotations

import logging
import os
import sys
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extras import execute_batch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "rebuild_features.log"

ROLLING_WINDOWS: Tuple[int, ...] = (5, 7, 10, 20, 30, 50)
MAIN_COUNT = 50
EURO_COUNT = 12
MAIN_PER_DRAW = 5
EURO_PER_DRAW = 2
PROGRESS_INTERVAL = 50

DrawRow = Tuple[int, int, int, int, int, int, int, int]


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("rebuild_features")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


LOGGER = setup_logging()


def load_environment() -> None:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(str(env_path))
    else:
        load_dotenv()


def get_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set in environment or .env")
    return psycopg2.connect(db_url)


def round6(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def main_numbers(draw: DrawRow) -> List[int]:
    return list(draw[1:6])


def euro_numbers(draw: DrawRow) -> List[int]:
    return [draw[6], draw[7]]


def count_main_in_draws(draws: Sequence[DrawRow]) -> Counter:
    counts: Counter = Counter()
    for draw in draws:
        counts.update(main_numbers(draw))
    return counts


def count_euro_in_draws(draws: Sequence[DrawRow]) -> Counter:
    counts: Counter = Counter()
    for draw in draws:
        counts.update(euro_numbers(draw))
    return counts


def expected_main_rate(num_draws: int) -> float:
    if num_draws <= 0:
        return 0.0
    return num_draws * MAIN_PER_DRAW / MAIN_COUNT


def expected_euro_rate(num_draws: int) -> float:
    if num_draws <= 0:
        return 0.0
    return num_draws * EURO_PER_DRAW / EURO_COUNT


def draws_since_last_seen(draws: Sequence[DrawRow], number: int) -> int:
    for offset, draw in enumerate(reversed(draws)):
        if number in main_numbers(draw):
            return offset
    return len(draws)


def window_slice(draws: Sequence[DrawRow], window: int) -> Sequence[DrawRow]:
    if window <= 0 or window >= len(draws):
        return draws
    return draws[-window:]


# Conditional probability disabled — too large for free tier
# Re-enable when storage is upgraded or sampling is implemented
#
# def cooccurrence_matrix(draws: Sequence[DrawRow]) -> Tuple[Dict[int, int], Dict[Tuple[int, int], int]]:
#     base_counts: Dict[int, int] = {n: 0 for n in range(1, MAIN_COUNT + 1)}
#     pair_counts: Dict[Tuple[int, int], int] = {}
#
#     for draw in draws:
#         nums = set(main_numbers(draw))
#         for base in nums:
#             base_counts[base] += 1
#             for nxt in nums:
#                 if nxt != base:
#                     pair_counts[(base, nxt)] = pair_counts.get((base, nxt), 0) + 1
#
#     return base_counts, pair_counts
#
#
# def conditional_rows(
#     draw_date: int,
#     draws: Sequence[DrawRow],
#     window_size: int,
# ) -> List[Tuple[int, int, int, Decimal, int]]:
#     scope = window_slice(draws, window_size) if window_size > 0 else draws
#     base_counts, pair_counts = cooccurrence_matrix(scope)
#     rows: List[Tuple[int, int, int, Decimal, int]] = []
#
#     for base in range(1, MAIN_COUNT + 1):
#         denom = base_counts.get(base, 0)
#         for nxt in range(1, MAIN_COUNT + 1):
#             if base == nxt:
#                 continue
#             if denom > 0:
#                 prob = pair_counts.get((base, nxt), 0) / denom
#             else:
#                 prob = 0.0
#             rows.append((draw_date, base, nxt, round6(prob), window_size))
#
#     return rows


def trend_scores(
    draws: Sequence[DrawRow],
    number: int,
) -> Tuple[Decimal, ...]:
    total = len(draws)
    counts_all = count_main_in_draws(draws)
    exp_all = expected_main_rate(total)

    def ratio_for(window: int) -> float:
        subset = window_slice(draws, window)
        observed = count_main_in_draws(subset).get(number, 0)
        expected = expected_main_rate(len(subset))
        if expected <= 0:
            return 0.0
        return observed / expected

    r5 = ratio_for(5)
    r7 = ratio_for(7)
    r10 = ratio_for(10)
    r20 = ratio_for(20)
    r30 = ratio_for(30)
    r50 = ratio_for(50)

    actual_all = counts_all.get(number, 0)
    score1 = (actual_all / exp_all) if exp_all > 0 else 0.0
    score2 = draws_since_last_seen(draws, number) / total if total > 0 else 0.0
    score3 = r10 - r50
    score4 = (r5 / r50) if r50 > 0 else 0.0
    score5 = (r5 - r10) - (r10 - r20)
    score6 = r5
    score7 = r7
    score8 = r10
    score9 = r20
    score10 = r5 - r30

    return tuple(round6(v) for v in (score1, score2, score3, score4, score5, score6, score7, score8, score9, score10))


def fetch_all_draws(conn) -> List[DrawRow]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT draw_date, n1, n2, n3, n4, n5, e1, e2
            FROM core.draws
            ORDER BY draw_date ASC
            """
        )
        return list(cur.fetchall())


def get_watermark(conn) -> Optional[int]:
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(draw_date) FROM features.frq_numbers")
        row = cur.fetchone()
        return row[0] if row else None


def is_features_empty(conn) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM features.frq_numbers")
        return cur.fetchone()[0] == 0


def target_draw_indices(all_draws: List[DrawRow], watermark: Optional[int], empty: bool) -> List[int]:
    if empty:
        return list(range(len(all_draws)))
    if watermark is None:
        return list(range(len(all_draws)))
    return [i for i, d in enumerate(all_draws) if d[0] > watermark]


def table_has_primary_key(conn, table_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'features'
              AND t.relname = %s
              AND c.contype = 'p'
            """,
            (table_name,),
        )
        return cur.fetchone() is not None


def truncate_conditional_tables(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE features.conditional_prob_numbers CASCADE")
    LOGGER.info("Truncated conditional probability tables (freed storage on Neon free tier).")


def ensure_primary_keys(conn) -> None:
    """Rolling tables created with LIKE may be missing PKs due to name conflicts."""
    pk_specs = [
        (["frq_numbers", *[f"frq_numbers_{w}draws" for w in ROLLING_WINDOWS]], ("draw_date", "number", "window_size")),
        (["trend_numbers"], ("draw_date", "number")),
        (["ml_features"], ("draw_date",)),
    ]

    for tables, columns in pk_specs:
        for table_name in tables:
            if table_has_primary_key(conn, table_name):
                continue
            constraint_name = f"pk_{table_name}"
            col_sql = sql.SQL(", ").join(sql.Identifier(col) for col in columns)
            stmt = sql.SQL(
                "ALTER TABLE features.{table} "
                "ADD CONSTRAINT {constraint} PRIMARY KEY ({columns})"
            ).format(
                table=sql.Identifier(table_name),
                constraint=sql.Identifier(constraint_name),
                columns=col_sql,
            )
            with conn.cursor() as cur:
                cur.execute(stmt)
            LOGGER.info("Added missing primary key %s on features.%s", constraint_name, table_name)


def upsert_frequency(
    conn,
    table_name: str,
    rows: List[Tuple[int, int, int, int]],
) -> None:
    if not rows:
        return
    query = sql.SQL(
        """
        INSERT INTO features.{table_name}
            (draw_date, number, frequency_count, window_size)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (draw_date, number, window_size)
        DO UPDATE SET
            frequency_count = EXCLUDED.frequency_count,
            updated_at = NOW()
        """
    ).format(table_name=sql.Identifier(table_name))
    with conn.cursor() as cur:
        execute_batch(cur, query.as_string(conn), rows, page_size=500)


# def upsert_conditional(
#     conn,
#     table_name: str,
#     rows: List[Tuple[int, int, int, Decimal, int]],
# ) -> None:
#     if not rows:
#         return
#     query = sql.SQL(
#         """
#         INSERT INTO features.{table_name}
#             (draw_date, base_number, next_number, conditional_probability, window_size)
#         VALUES (%s, %s, %s, %s, %s)
#         ON CONFLICT (draw_date, base_number, next_number, window_size)
#         DO UPDATE SET
#             conditional_probability = EXCLUDED.conditional_probability,
#             updated_at = NOW()
#         """
#     ).format(table_name=sql.Identifier(table_name))
#     with conn.cursor() as cur:
#         execute_batch(cur, query.as_string(conn), rows, page_size=500)


def upsert_trend(conn, rows: List[Tuple]) -> None:
    if not rows:
        return
    query = """
        INSERT INTO features.trend_numbers
            (draw_date, number,
             trend_score_1, trend_score_2, trend_score_3, trend_score_4, trend_score_5,
             trend_score_6, trend_score_7, trend_score_8, trend_score_9, trend_score_10)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (draw_date, number)
        DO UPDATE SET
            trend_score_1 = EXCLUDED.trend_score_1,
            trend_score_2 = EXCLUDED.trend_score_2,
            trend_score_3 = EXCLUDED.trend_score_3,
            trend_score_4 = EXCLUDED.trend_score_4,
            trend_score_5 = EXCLUDED.trend_score_5,
            trend_score_6 = EXCLUDED.trend_score_6,
            trend_score_7 = EXCLUDED.trend_score_7,
            trend_score_8 = EXCLUDED.trend_score_8,
            trend_score_9 = EXCLUDED.trend_score_9,
            trend_score_10 = EXCLUDED.trend_score_10,
            updated_at = NOW()
    """
    with conn.cursor() as cur:
        execute_batch(cur, query, rows, page_size=500)


def upsert_ml_features(conn, rows: List[Tuple]) -> None:
    if not rows:
        return

    meta_main_cols = sql.SQL(", ").join(
        sql.Identifier(f"meta_main_{i}") for i in range(1, MAIN_COUNT + 1)
    )
    meta_euro_cols = sql.SQL(", ").join(
        sql.Identifier(f"meta_euro_{i}") for i in range(1, EURO_COUNT + 1)
    )
    meta_main_updates = sql.SQL(", ").join(
        sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(f"meta_main_{i}"))
        for i in range(1, MAIN_COUNT + 1)
    )
    meta_euro_updates = sql.SQL(", ").join(
        sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(f"meta_euro_{i}"))
        for i in range(1, EURO_COUNT + 1)
    )
    value_count = 8 + MAIN_COUNT + EURO_COUNT
    placeholders = sql.SQL(", ").join([sql.Placeholder()] * value_count)

    query = sql.SQL(
        """
        INSERT INTO features.ml_features (
            draw_date, label, label_main_2, label_main_3, label_main_4, label_main_5,
            label_euro_1, label_euro_2,
            {meta_main_cols}, {meta_euro_cols}
        ) VALUES ({placeholders})
        ON CONFLICT (draw_date)
        DO UPDATE SET
            label = EXCLUDED.label,
            label_main_2 = EXCLUDED.label_main_2,
            label_main_3 = EXCLUDED.label_main_3,
            label_main_4 = EXCLUDED.label_main_4,
            label_main_5 = EXCLUDED.label_main_5,
            label_euro_1 = EXCLUDED.label_euro_1,
            label_euro_2 = EXCLUDED.label_euro_2,
            {meta_main_updates},
            {meta_euro_updates},
            updated_at = NOW()
        """
    ).format(
        meta_main_cols=meta_main_cols,
        meta_euro_cols=meta_euro_cols,
        placeholders=placeholders,
        meta_main_updates=meta_main_updates,
        meta_euro_updates=meta_euro_updates,
    )
    with conn.cursor() as cur:
        execute_batch(cur, query.as_string(conn), rows, page_size=100)


def build_frequency_for_draw(
    draw_date: int,
    history: Sequence[DrawRow],
) -> Dict[str, List[Tuple[int, int, int, int]]]:
    result: Dict[str, List[Tuple[int, int, int, int]]] = {"frq_numbers": []}
    for wnd in ROLLING_WINDOWS:
        result[f"frq_numbers_{wnd}draws"] = []

    counts_all = count_main_in_draws(history)
    for number in range(1, MAIN_COUNT + 1):
        result["frq_numbers"].append((draw_date, number, counts_all.get(number, 0), 0))

    for wnd in ROLLING_WINDOWS:
        subset = window_slice(history, wnd)
        counts = count_main_in_draws(subset)
        table = f"frq_numbers_{wnd}draws"
        for number in range(1, MAIN_COUNT + 1):
            result[table].append((draw_date, number, counts.get(number, 0), wnd))

    return result


def build_ml_row(draw: DrawRow, history: Sequence[DrawRow]) -> Tuple:
    draw_date, n1, n2, n3, n4, n5, e1, e2 = draw
    main_counts = count_main_in_draws(history)
    euro_counts = count_euro_in_draws(history)
    exp_main = expected_main_rate(len(history))
    exp_euro = expected_euro_rate(len(history))

    meta_main = []
    for number in range(1, MAIN_COUNT + 1):
        observed = main_counts.get(number, 0)
        ratio = (observed / exp_main) if exp_main > 0 else 0.0
        meta_main.append(round6(ratio))

    meta_euro = []
    for number in range(1, EURO_COUNT + 1):
        observed = euro_counts.get(number, 0)
        ratio = (observed / exp_euro) if exp_euro > 0 else 0.0
        meta_euro.append(round6(ratio))

    return (draw_date, n1, n2, n3, n4, n5, e1, e2, *meta_main, *meta_euro)


def process_draws(conn, all_draws: List[DrawRow], indices: List[int]) -> None:
    total = len(indices)
    if total == 0:
        LOGGER.info("No draw dates to process.")
        return

    LOGGER.info("Processing %d draw date(s)...", total)

    for processed, idx in enumerate(indices, start=1):
        draw = all_draws[idx]
        draw_date = draw[0]
        history = all_draws[: idx + 1]

        freq_by_table = build_frequency_for_draw(draw_date, history)
        upsert_frequency(conn, "frq_numbers", freq_by_table["frq_numbers"])
        for wnd in ROLLING_WINDOWS:
            upsert_frequency(conn, f"frq_numbers_{wnd}draws", freq_by_table[f"frq_numbers_{wnd}draws"])

        trend_rows = []
        for number in range(1, MAIN_COUNT + 1):
            scores = trend_scores(history, number)
            trend_rows.append((draw_date, number, *scores))
        upsert_trend(conn, trend_rows)

        # Conditional probability disabled — too large for free tier
        # Re-enable when storage is upgraded or sampling is implemented

        upsert_ml_features(conn, [build_ml_row(draw, history)])

        if processed % PROGRESS_INTERVAL == 0 or processed == total:
            LOGGER.info("Progress: %d / %d draw dates (latest: %s)", processed, total, draw_date)


def main() -> int:
    load_environment()
    conn = None

    try:
        conn = get_connection()
        conn.autocommit = False

        truncate_conditional_tables(conn)

        all_draws = fetch_all_draws(conn)
        if not all_draws:
            raise RuntimeError("No draws found in core.draws")

        empty = is_features_empty(conn)
        watermark = get_watermark(conn)
        mode = "full" if empty else "incremental"
        indices = target_draw_indices(all_draws, watermark, empty)

        LOGGER.info(
            "Mode: %s | core.draws: %d | watermark: %s | to process: %d",
            mode,
            len(all_draws),
            watermark if watermark is not None else "none",
            len(indices),
        )

        ensure_primary_keys(conn)
        process_draws(conn, all_draws, indices)
        conn.commit()
        LOGGER.info("Feature rebuild completed successfully.")
        return 0

    except Exception:
        if conn is not None:
            conn.rollback()
        LOGGER.exception("Feature rebuild failed")
        return 1

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())

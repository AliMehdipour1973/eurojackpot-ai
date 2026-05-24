#!/usr/bin/env python3
"""Phase 2: pure random baseline backtest against historical EuroJackpot draws."""

from __future__ import annotations

import logging
import os
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, execute_batch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "random_baseline.log"
BASELINE_RESULTS_PATH = PROJECT_ROOT / "docs" / "BASELINE_RESULTS.md"

NUM_SIMULATIONS = 10
PROGRESS_INTERVAL = 50
BATCH_SIZE = 500
MODEL_NAME = "random_baseline"
MODEL_VERSION = "v1.0"

DrawRow = Tuple[int, int, int, int, int, int, int, int]
ResultRow = Tuple


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("random_baseline")
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


def main_numbers(draw: DrawRow) -> List[int]:
    return list(draw[1:6])


def euro_numbers(draw: DrawRow) -> List[int]:
    return [draw[6], draw[7]]


def generate_random_ticket() -> Tuple[List[int], List[int]]:
    predicted_main = sorted(random.sample(range(1, 51), 5))
    predicted_euro = sorted(random.sample(range(1, 13), 2))
    return predicted_main, predicted_euro


def count_hits(predicted: Sequence[int], actual: Sequence[int]) -> int:
    return len(set(predicted) & set(actual))


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


def delete_existing_baseline(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM backtest.backtest_result WHERE model_name = %s",
            (MODEL_NAME,),
        )
        deleted = cur.rowcount
    LOGGER.info("Deleted %d existing row(s) for model_name=%s", deleted, MODEL_NAME)
    return deleted


def build_result_row(
    draw: DrawRow,
    pipeline_run_id: str,
    simulation_index: int,
) -> ResultRow:
    draw_date = draw[0]
    actual_main = main_numbers(draw)
    actual_euro = euro_numbers(draw)
    predicted_main, predicted_euro = generate_random_ticket()

    hit_main = count_hits(predicted_main, actual_main)
    hit_euro = count_hits(predicted_euro, actual_euro)
    total_hits = hit_main + hit_euro
    score = total_hits / 7.0

    matched_main = sorted(set(predicted_main) & set(actual_main))
    matched_euro = sorted(set(predicted_euro) & set(actual_euro))

    probability_payload = {
        "simulation_index": simulation_index,
        "predicted_main_numbers": predicted_main,
        "predicted_euro_numbers": predicted_euro,
        "generator": "uniform_random",
    }
    metrics_payload = {
        "hit_main_count": hit_main,
        "hit_euro_count": hit_euro,
        "total_hit_count": total_hits,
        "matched_main_numbers": matched_main,
        "matched_euro_numbers": matched_euro,
    }

    return (
        draw_date,
        draw_date,
        MODEL_NAME,
        MODEL_VERSION,
        pipeline_run_id,
        predicted_main,
        predicted_euro,
        actual_main,
        actual_euro,
        hit_main,
        hit_euro,
        score,
        Json(probability_payload),
        Json(metrics_payload),
    )


INSERT_QUERY = """
    INSERT INTO backtest.backtest_result (
        draw_date,
        prediction_for_draw_date,
        model_name,
        model_version,
        pipeline_run_id,
        predicted_main_numbers,
        predicted_euro_numbers,
        actual_main_numbers,
        actual_euro_numbers,
        hit_main_count,
        hit_euro_count,
        score_numeric,
        probability_payload,
        metrics_payload
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def insert_batch(conn, rows: List[ResultRow]) -> None:
    if not rows:
        return
    with conn.cursor() as cur:
        execute_batch(cur, INSERT_QUERY, rows, page_size=BATCH_SIZE)


def compute_summary(results: List[ResultRow]) -> Dict[str, float]:
    total = len(results)
    if total == 0:
        return {
            "total_tickets": 0,
            "hit_rate_main_2_plus": 0.0,
            "hit_rate_main_3_plus": 0.0,
            "hit_rate_total_3_plus": 0.0,
            "avg_main_hits": 0.0,
            "avg_euro_hits": 0.0,
        }

    main_2_plus = 0
    main_3_plus = 0
    total_3_plus = 0
    main_sum = 0
    euro_sum = 0

    for row in results:
        hit_main = row[9]
        hit_euro = row[10]
        total_hits = hit_main + hit_euro

        if hit_main >= 2:
            main_2_plus += 1
        if hit_main >= 3:
            main_3_plus += 1
        if total_hits >= 3:
            total_3_plus += 1

        main_sum += hit_main
        euro_sum += hit_euro

    return {
        "total_tickets": total,
        "hit_rate_main_2_plus": main_2_plus / total * 100.0,
        "hit_rate_main_3_plus": main_3_plus / total * 100.0,
        "hit_rate_total_3_plus": total_3_plus / total * 100.0,
        "avg_main_hits": main_sum / total,
        "avg_euro_hits": euro_sum / total,
    }


def print_summary(summary: Dict[str, float]) -> None:
    LOGGER.info("=== Random Baseline Summary ===")
    LOGGER.info("Total tickets generated: %d", int(summary["total_tickets"]))
    LOGGER.info("hit_rate_main_2_plus: %.4f%%", summary["hit_rate_main_2_plus"])
    LOGGER.info("hit_rate_main_3_plus: %.4f%%", summary["hit_rate_main_3_plus"])
    LOGGER.info("hit_rate_total_3_plus: %.4f%%", summary["hit_rate_total_3_plus"])
    LOGGER.info("avg_main_hits: %.4f", summary["avg_main_hits"])
    LOGGER.info("avg_euro_hits: %.4f", summary["avg_euro_hits"])


def save_summary_markdown(
    summary: Dict[str, float],
    pipeline_run_id: str,
    draw_count: int,
) -> None:
    BASELINE_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    content = f"""# Random Baseline Results

**Generated:** {generated_at}  
**Pipeline run ID:** `{pipeline_run_id}`  
**Model:** `{MODEL_NAME}` `{MODEL_VERSION}`  
**Historical draws:** {draw_count}  
**Simulations per draw:** {NUM_SIMULATIONS}  
**Total tickets:** {int(summary["total_tickets"])}

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total tickets generated | {int(summary["total_tickets"]):,} |
| hit_rate_main_2_plus | {summary["hit_rate_main_2_plus"]:.4f}% |
| hit_rate_main_3_plus | {summary["hit_rate_main_3_plus"]:.4f}% |
| hit_rate_total_3_plus | {summary["hit_rate_total_3_plus"]:.4f}% |
| avg_main_hits | {summary["avg_main_hits"]:.4f} |
| avg_euro_hits | {summary["avg_euro_hits"]:.4f} |

---

## Notes

- Pure random ticket generation: 5 unique main numbers (1–50) + 2 unique euro numbers (1–12).
- Each ticket is compared against the actual draw for that date.
- This baseline is the reference point for all future model comparisons (see `docs/ML_STRATEGY.md`).
"""

    BASELINE_RESULTS_PATH.write_text(content, encoding="utf-8")
    LOGGER.info("Saved summary to %s", BASELINE_RESULTS_PATH)


def run_simulation(conn, draws: List[DrawRow], pipeline_run_id: str) -> List[ResultRow]:
    all_results: List[ResultRow] = []
    pending: List[ResultRow] = []
    total_draws = len(draws)

    LOGGER.info(
        "Running %d simulation(s) per draw across %d draw(s)...",
        NUM_SIMULATIONS,
        total_draws,
    )

    for draw_index, draw in enumerate(draws, start=1):
        for sim_index in range(1, NUM_SIMULATIONS + 1):
            row = build_result_row(draw, pipeline_run_id, sim_index)
            pending.append(row)
            all_results.append(row)

            if len(pending) >= BATCH_SIZE:
                insert_batch(conn, pending)
                pending.clear()

        if draw_index % PROGRESS_INTERVAL == 0 or draw_index == total_draws:
            LOGGER.info(
                "Progress: %d / %d draws processed (latest draw_date: %s)",
                draw_index,
                total_draws,
                draw[0],
            )

    insert_batch(conn, pending)
    return all_results


def main() -> int:
    load_environment()
    conn = None

    try:
        pipeline_run_id = str(uuid.uuid4())
        conn = get_connection()
        conn.autocommit = False

        delete_existing_baseline(conn)

        draws = fetch_all_draws(conn)
        if not draws:
            raise RuntimeError("No draws found in core.draws")

        LOGGER.info(
            "Starting random baseline | pipeline_run_id=%s | draws=%d | simulations=%d",
            pipeline_run_id,
            len(draws),
            NUM_SIMULATIONS,
        )

        results = run_simulation(conn, draws, pipeline_run_id)
        conn.commit()

        summary = compute_summary(results)
        print_summary(summary)
        save_summary_markdown(summary, pipeline_run_id, len(draws))

        LOGGER.info("Random baseline completed successfully.")
        return 0

    except Exception:
        if conn is not None:
            conn.rollback()
        LOGGER.exception("Random baseline failed")
        return 1

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())

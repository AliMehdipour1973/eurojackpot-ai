#!/usr/bin/env python3
"""Phase 3: walk-forward XGBoost backtest against historical EuroJackpot draws."""

from __future__ import annotations

import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, execute_batch

try:
    import xgboost  # noqa: F401
    import sklearn  # noqa: F401
except ImportError:
    print("Missing dependency. Run: pip install xgboost scikit-learn")
    sys.exit(1)

from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "xgboost_backtest.log"
RESULTS_PATH = PROJECT_ROOT / "docs" / "XGBOOST_RESULTS.md"

MODEL_NAME = "xgboost"
MODEL_VERSION = "v1.0"
BATCH_SIZE = 200

RANDOM_BASELINE = {
    "hit_rate_main_2_plus": 7.1034,
    "hit_rate_main_3_plus": 0.3448,
    "hit_rate_total_3_plus": 3.1954,
}

WALK_FORWARD_WINDOWS: Tuple[Tuple[slice, slice], ...] = (
    (slice(0, 200), slice(200, 250)),
    (slice(50, 250), slice(250, 300)),
    (slice(100, 300), slice(300, 350)),
    (slice(150, 350), slice(350, 400)),
    (slice(200, 400), slice(400, 435)),
)

MAIN_NUMBERS = list(range(1, 51))
EURO_NUMBERS = list(range(1, 13))

XGB_PARAMS = {
    "n_estimators": 100,
    "max_depth": 4,
    "learning_rate": 0.1,
    "eval_metric": "logloss",
    "random_state": 42,
    "verbosity": 0,
}

ResultRow = Tuple


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("xgboost_backtest")
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


def freq_feature_columns() -> List[str]:
    return [f"freq_main_{n}" for n in MAIN_NUMBERS]


def trend_feature_columns() -> List[str]:
    return [f"trend_score_{i}" for i in range(1, 11)]


def feature_columns() -> List[str]:
    return freq_feature_columns() + trend_feature_columns()


def load_feature_matrix(conn) -> pd.DataFrame:
    draws = pd.read_sql(
        """
        SELECT draw_date, n1, n2, n3, n4, n5, e1, e2
        FROM core.draws
        ORDER BY draw_date ASC
        """,
        conn,
    )

    freq = pd.read_sql(
        """
        SELECT draw_date, number, frequency_count
        FROM features.frq_numbers
        WHERE window_size = 0
        ORDER BY draw_date ASC, number ASC
        """,
        conn,
    )
    freq_pivot = freq.pivot(index="draw_date", columns="number", values="frequency_count").reset_index()
    freq_pivot = freq_pivot.rename(
        columns={
            col: f"freq_main_{int(col)}"
            for col in freq_pivot.columns
            if col != "draw_date"
        }
    )

    trend = pd.read_sql(
        """
        SELECT
            draw_date,
            AVG(trend_score_1) AS trend_score_1,
            AVG(trend_score_2) AS trend_score_2,
            AVG(trend_score_3) AS trend_score_3,
            AVG(trend_score_4) AS trend_score_4,
            AVG(trend_score_5) AS trend_score_5,
            AVG(trend_score_6) AS trend_score_6,
            AVG(trend_score_7) AS trend_score_7,
            AVG(trend_score_8) AS trend_score_8,
            AVG(trend_score_9) AS trend_score_9,
            AVG(trend_score_10) AS trend_score_10
        FROM features.trend_numbers
        GROUP BY draw_date
        ORDER BY draw_date ASC
        """,
        conn,
    )

    df = draws.merge(freq_pivot, on="draw_date", how="left").merge(trend, on="draw_date", how="left")
    df = df.sort_values("draw_date").reset_index(drop=True)

    for col in feature_columns():
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].fillna(0.0)

    LOGGER.info("Loaded feature matrix: %d draws, %d features", len(df), len(feature_columns()))
    return df


def draw_main_numbers(row: pd.Series) -> List[int]:
    return sorted([int(row["n1"]), int(row["n2"]), int(row["n3"]), int(row["n4"]), int(row["n5"])])


def draw_euro_numbers(row: pd.Series) -> List[int]:
    return sorted([int(row["e1"]), int(row["e2"])])


def main_label(row: pd.Series, number: int) -> int:
    return int(number in draw_main_numbers(row))


def euro_label(row: pd.Series, number: int) -> int:
    return int(number in draw_euro_numbers(row))


def count_hits(predicted: Sequence[int], actual: Sequence[int]) -> int:
    return len(set(predicted) & set(actual))


def build_classifier() -> XGBClassifier:
    return XGBClassifier(**XGB_PARAMS)


def train_number_classifiers(
    train_df: pd.DataFrame,
    numbers: Sequence[int],
    label_fn,
) -> Dict[int, XGBClassifier]:
    features = feature_columns()
    x_train = train_df[features].to_numpy(dtype=np.float32)
    models: Dict[int, XGBClassifier] = {}

    for number in numbers:
        y_train = train_df.apply(lambda row: label_fn(row, number), axis=1).to_numpy(dtype=np.int32)
        model = build_classifier()
        model.fit(x_train, y_train)
        models[number] = model

    return models


def predict_ticket(
    row: pd.Series,
    main_models: Dict[int, XGBClassifier],
    euro_models: Dict[int, XGBClassifier],
) -> Tuple[List[int], List[int], Dict[str, float], Dict[str, float]]:
    features = feature_columns()
    x_row = row[features].to_numpy(dtype=np.float32).reshape(1, -1)

    main_probs = {str(n): float(main_models[n].predict_proba(x_row)[0, 1]) for n in MAIN_NUMBERS}
    euro_probs = {str(n): float(euro_models[n].predict_proba(x_row)[0, 1]) for n in EURO_NUMBERS}

    predicted_main = sorted(
        [int(n) for n, _ in sorted(main_probs.items(), key=lambda item: item[1], reverse=True)[:5]]
    )
    predicted_euro = sorted(
        [int(n) for n, _ in sorted(euro_probs.items(), key=lambda item: item[1], reverse=True)[:2]]
    )

    return predicted_main, predicted_euro, main_probs, euro_probs


def delete_existing_results(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM backtest.backtest_xgboost WHERE model_name = %s",
            (MODEL_NAME,),
        )
        deleted = cur.rowcount
    LOGGER.info("Deleted %d existing row(s) for model_name=%s", deleted, MODEL_NAME)
    return deleted


INSERT_QUERY = """
    INSERT INTO backtest.backtest_xgboost (
        draw_date,
        prediction_for_draw_date,
        model_name,
        model_version,
        pipeline_run_id,
        train_window_start,
        train_window_end,
        valid_window_start,
        valid_window_end,
        predicted_main_numbers,
        predicted_euro_numbers,
        actual_main_numbers,
        actual_euro_numbers,
        hit_main_count,
        hit_euro_count,
        score_numeric,
        probability_payload,
        metrics_payload
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::smallint[], %s::smallint[], %s::smallint[], %s::smallint[], %s, %s, %s, %s, %s)
"""


def build_result_row(
    row: pd.Series,
    pipeline_run_id: str,
    window_index: int,
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    predicted_main: List[int],
    predicted_euro: List[int],
    main_probs: Dict[str, float],
    euro_probs: Dict[str, float],
) -> ResultRow:
    draw_date = int(row["draw_date"])
    actual_main = draw_main_numbers(row)
    actual_euro = draw_euro_numbers(row)
    hit_main = count_hits(predicted_main, actual_main)
    hit_euro = count_hits(predicted_euro, actual_euro)
    total_hits = hit_main + hit_euro

    probability_payload = {
        "main_probabilities": main_probs,
        "euro_probabilities": euro_probs,
    }
    metrics_payload = {
        "window_index": window_index + 1,
        "train_window_start": int(train_df["draw_date"].iloc[0]),
        "train_window_end": int(train_df["draw_date"].iloc[-1]),
        "valid_window_start": int(valid_df["draw_date"].iloc[0]),
        "valid_window_end": int(valid_df["draw_date"].iloc[-1]),
        "hit_main_count": hit_main,
        "hit_euro_count": hit_euro,
        "total_hit_count": total_hits,
        "matched_main_numbers": sorted(set(predicted_main) & set(actual_main)),
        "matched_euro_numbers": sorted(set(predicted_euro) & set(actual_euro)),
    }

    predicted_main_numbers = [int(x) for x in predicted_main]
    predicted_euro_numbers = [int(x) for x in predicted_euro]
    actual_main_numbers = [int(x) for x in actual_main]
    actual_euro_numbers = [int(x) for x in actual_euro]

    return (
        draw_date,
        draw_date,
        MODEL_NAME,
        MODEL_VERSION,
        pipeline_run_id,
        int(train_df["draw_date"].iloc[0]),
        int(train_df["draw_date"].iloc[-1]),
        int(valid_df["draw_date"].iloc[0]),
        int(valid_df["draw_date"].iloc[-1]),
        predicted_main_numbers,
        predicted_euro_numbers,
        actual_main_numbers,
        actual_euro_numbers,
        int(hit_main),
        int(hit_euro),
        total_hits / 7.0,
        Json(probability_payload),
        Json(metrics_payload),
    )


def insert_batch(conn, rows: List[ResultRow]) -> None:
    if not rows:
        return
    normalized_rows: List[ResultRow] = []
    for row in rows:
        normalized_rows.append(
            (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
                row[7],
                row[8],
                [int(x) for x in row[9]],
                [int(x) for x in row[10]],
                [int(x) for x in row[11]],
                [int(x) for x in row[12]],
                row[13],
                row[14],
                row[15],
                row[16],
                row[17],
            )
        )
    with conn.cursor() as cur:
        execute_batch(cur, INSERT_QUERY, normalized_rows, page_size=BATCH_SIZE)


def compute_summary(results: List[ResultRow]) -> Dict[str, float]:
    total = len(results)
    if total == 0:
        return {
            "total_predictions": 0,
            "hit_rate_main_2_plus": 0.0,
            "hit_rate_main_3_plus": 0.0,
            "hit_rate_total_3_plus": 0.0,
            "avg_main_hits": 0.0,
            "avg_euro_hits": 0.0,
        }

    main_2_plus = main_3_plus = total_3_plus = 0
    main_sum = euro_sum = 0

    for row in results:
        hit_main = row[13]
        hit_euro = row[14]
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
        "total_predictions": total,
        "hit_rate_main_2_plus": main_2_plus / total * 100.0,
        "hit_rate_main_3_plus": main_3_plus / total * 100.0,
        "hit_rate_total_3_plus": total_3_plus / total * 100.0,
        "avg_main_hits": main_sum / total,
        "avg_euro_hits": euro_sum / total,
    }


def improvement_over_random(algorithm_rate: float, baseline_rate: float) -> float:
    if baseline_rate == 0:
        return 0.0
    return (algorithm_rate - baseline_rate) / baseline_rate * 100.0


def print_summary(summary: Dict[str, float]) -> None:
    LOGGER.info("=== XGBoost Walk-Forward Summary ===")
    LOGGER.info("Total predictions: %d", int(summary["total_predictions"]))
    LOGGER.info(
        "hit_rate_main_2_plus: %.4f%% (baseline %.4f%%, improvement %.2f%%)",
        summary["hit_rate_main_2_plus"],
        RANDOM_BASELINE["hit_rate_main_2_plus"],
        improvement_over_random(summary["hit_rate_main_2_plus"], RANDOM_BASELINE["hit_rate_main_2_plus"]),
    )
    LOGGER.info(
        "hit_rate_main_3_plus: %.4f%% (baseline %.4f%%, improvement %.2f%%)",
        summary["hit_rate_main_3_plus"],
        RANDOM_BASELINE["hit_rate_main_3_plus"],
        improvement_over_random(summary["hit_rate_main_3_plus"], RANDOM_BASELINE["hit_rate_main_3_plus"]),
    )
    LOGGER.info(
        "hit_rate_total_3_plus: %.4f%% (baseline %.4f%%, improvement %.2f%%)",
        summary["hit_rate_total_3_plus"],
        RANDOM_BASELINE["hit_rate_total_3_plus"],
        improvement_over_random(summary["hit_rate_total_3_plus"], RANDOM_BASELINE["hit_rate_total_3_plus"]),
    )
    LOGGER.info("avg_main_hits: %.4f", summary["avg_main_hits"])
    LOGGER.info("avg_euro_hits: %.4f", summary["avg_euro_hits"])


def save_results_markdown(summary: Dict[str, float], pipeline_run_id: str) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    rows = []
    for metric in ("hit_rate_main_2_plus", "hit_rate_main_3_plus", "hit_rate_total_3_plus"):
        algo = summary[metric]
        baseline = RANDOM_BASELINE[metric]
        improvement = improvement_over_random(algo, baseline)
        rows.append(
            f"| {metric} | {baseline:.4f}% | {algo:.4f}% | {improvement:+.2f}% |"
        )

    content = f"""# XGBoost Walk-Forward Results

**Generated:** {generated_at}  
**Pipeline run ID:** `{pipeline_run_id}`  
**Model:** `{MODEL_NAME}` `{MODEL_VERSION}`  
**Total predictions:** {int(summary["total_predictions"])}

---

## Comparison vs Random Baseline

| Metric | Random Baseline | XGBoost | Improvement |
|--------|----------------|---------|-------------|
{chr(10).join(rows)}
| avg_main_hits | — | {summary["avg_main_hits"]:.4f} | — |
| avg_euro_hits | — | {summary["avg_euro_hits"]:.4f} | — |

---

## Walk-Forward Windows

| Window | Train Index | Validate Index |
|--------|-------------|----------------|
| 1 | 0..199 | 200..249 |
| 2 | 50..249 | 250..299 |
| 3 | 100..299 | 300..349 |
| 4 | 150..349 | 350..399 |
| 5 | 200..399 | 400..434 |

---

## Notes

- 50 main-number classifiers + 12 euro-number classifiers (binary one-vs-rest).
- Features: `freq_main_1..50` + draw-level averaged `trend_score_1..10`.
- Top-5 / top-2 numbers selected by predicted probability on each validation draw.
"""

    RESULTS_PATH.write_text(content, encoding="utf-8")
    LOGGER.info("Saved summary to %s", RESULTS_PATH)


def run_walk_forward(conn, df: pd.DataFrame, pipeline_run_id: str) -> List[ResultRow]:
    all_results: List[ResultRow] = []
    pending: List[ResultRow] = []

    for window_index, (train_slice, valid_slice) in enumerate(WALK_FORWARD_WINDOWS):
        train_df = df.iloc[train_slice].copy()
        valid_df = df.iloc[valid_slice].copy()

        if train_df.empty or valid_df.empty:
            raise RuntimeError(f"Walk-forward window {window_index + 1} has empty train or validation split")
        if len(df) < valid_slice.stop:
            raise RuntimeError(
                f"Not enough draws for walk-forward window {window_index + 1}: "
                f"need index {valid_slice.stop - 1}, have {len(df) - 1}"
            )

        LOGGER.info(
            "Window %d/5 | train=%d draws (%s..%s) | validate=%d draws (%s..%s)",
            window_index + 1,
            len(train_df),
            train_df["draw_date"].iloc[0],
            train_df["draw_date"].iloc[-1],
            len(valid_df),
            valid_df["draw_date"].iloc[0],
            valid_df["draw_date"].iloc[-1],
        )

        main_models = train_number_classifiers(train_df, MAIN_NUMBERS, main_label)
        euro_models = train_number_classifiers(train_df, EURO_NUMBERS, euro_label)

        for _, row in valid_df.iterrows():
            predicted_main, predicted_euro, main_probs, euro_probs = predict_ticket(
                row, main_models, euro_models
            )
            result = build_result_row(
                row,
                pipeline_run_id,
                window_index,
                train_df,
                valid_df,
                predicted_main,
                predicted_euro,
                main_probs,
                euro_probs,
            )
            pending.append(result)
            all_results.append(result)

            if len(pending) >= BATCH_SIZE:
                insert_batch(conn, pending)
                pending.clear()

        insert_batch(conn, pending)
        pending.clear()
        LOGGER.info("Window %d/5 complete (%d validation predictions)", window_index + 1, len(valid_df))

    return all_results


def main() -> int:
    load_environment()
    conn = None

    try:
        pipeline_run_id = str(uuid.uuid4())
        conn = get_connection()
        conn.autocommit = False

        delete_existing_results(conn)
        df = load_feature_matrix(conn)

        LOGGER.info(
            "Starting XGBoost walk-forward backtest | pipeline_run_id=%s | draws=%d",
            pipeline_run_id,
            len(df),
        )

        results = run_walk_forward(conn, df, pipeline_run_id)
        conn.commit()

        summary = compute_summary(results)
        print_summary(summary)
        save_results_markdown(summary, pipeline_run_id)

        LOGGER.info("XGBoost walk-forward backtest completed successfully.")
        return 0

    except Exception:
        if conn is not None:
            conn.rollback()
        LOGGER.exception("XGBoost walk-forward backtest failed")
        return 1

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())

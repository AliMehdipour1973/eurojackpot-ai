#!/usr/bin/env python3
"""Phase 5: compare algorithms using the top 21 selected features."""

from __future__ import annotations

import logging
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, execute_batch
from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

try:
    import lightgbm  # noqa: F401
except ImportError:
    print("Missing dependency. Run: pip install lightgbm")
    sys.exit(1)

from lightgbm import LGBMClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "algorithm_comparison.log"
RESULTS_PATH = PROJECT_ROOT / "docs" / "ALGORITHM_COMPARISON.md"

SELECTED_FEATURES: Tuple[str, ...] = (
    "trend_score_2",
    "trend_score_4",
    "trend_score_1",
    "freq_main_6",
    "freq_main_1",
    "trend_score_10",
    "freq_main_2",
    "freq_main_9",
    "trend_score_7",
    "freq_main_3",
    "freq_main_8",
    "freq_main_4",
    "freq_main_13",
    "freq_main_5",
    "freq_main_7",
    "freq_main_10",
    "freq_main_14",
    "freq_main_11",
    "freq_main_12",
    "freq_main_15",
    "freq_main_16",
)

RANDOM_BASELINE = {
    "display_name": "Random",
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
MODEL_VERSION = "v1.0"
BATCH_SIZE = 200
CHECKPOINT_MIN_ROWS = 200
EXPECTED_PREDICTIONS = 235

ResultRow = Tuple


@dataclass(frozen=True)
class AlgorithmSpec:
    display_name: str
    model_name: str
    table: str
    build_classifier: Callable[[], Any]


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("algorithm_comparison")
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


ALGORITHMS_TO_RUN: Tuple[AlgorithmSpec, ...] = (
    AlgorithmSpec(
        display_name="LightGBM",
        model_name="lightgbm",
        table="backtest_lgbm",
        build_classifier=lambda: LGBMClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            verbosity=-1,
        ),
    ),
    AlgorithmSpec(
        display_name="RandomForest",
        model_name="random_forest",
        table="backtest_random_forest",
        build_classifier=lambda: RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42,
            n_jobs=-1,
        ),
    ),
    AlgorithmSpec(
        display_name="GradientBoosting",
        model_name="gradient_boosting",
        table="backtest_gradient_boosting",
        build_classifier=lambda: GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
        ),
    ),
    AlgorithmSpec(
        display_name="ExtraTrees",
        model_name="extra_trees",
        table="backtest_extra_trees",
        build_classifier=lambda: ExtraTreesClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42,
            n_jobs=-1,
        ),
    ),
    AlgorithmSpec(
        display_name="LogisticRegression",
        model_name="logistic_regression",
        table="backtest_logistic_regression",
        build_classifier=lambda: LogisticRegression(max_iter=500, random_state=42),
    ),
)


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

    for col in SELECTED_FEATURES:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].fillna(0.0)

    LOGGER.info("Loaded feature matrix: %d draws, %d selected features", len(df), len(SELECTED_FEATURES))
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


def positive_class_proba(model: Any, x_row: pd.DataFrame) -> float:
    proba = model.predict_proba(x_row)[0]
    classes = list(model.classes_)
    if len(classes) == 1:
        return 1.0 if classes[0] == 1 else 0.0
    if 1 in classes:
        return float(proba[classes.index(1)])
    return float(proba[-1])


def train_number_classifiers(
    train_df: pd.DataFrame,
    numbers: Sequence[int],
    label_fn,
    build_classifier: Callable[[], Any],
) -> Dict[int, Any]:
    x_train = train_df[list(SELECTED_FEATURES)]
    models: Dict[int, Any] = {}

    for number in numbers:
        y_train = train_df.apply(lambda row: label_fn(row, number), axis=1).to_numpy(dtype=np.int32)
        model = build_classifier()
        model.fit(x_train, y_train)
        models[number] = model

    return models


def predict_ticket(
    row: pd.Series,
    main_models: Dict[int, Any],
    euro_models: Dict[int, Any],
) -> Tuple[List[int], List[int], Dict[str, float], Dict[str, float]]:
    x_row = row[list(SELECTED_FEATURES)].to_frame().T

    main_probs = {str(n): positive_class_proba(main_models[n], x_row) for n in MAIN_NUMBERS}
    euro_probs = {str(n): positive_class_proba(euro_models[n], x_row) for n in EURO_NUMBERS}

    predicted_main = sorted(
        [int(n) for n, _ in sorted(main_probs.items(), key=lambda item: item[1], reverse=True)[:5]]
    )
    predicted_euro = sorted(
        [int(n) for n, _ in sorted(euro_probs.items(), key=lambda item: item[1], reverse=True)[:2]]
    )

    return predicted_main, predicted_euro, main_probs, euro_probs


def insert_query_for_table(table: str) -> str:
    return f"""
        INSERT INTO backtest.{table} (
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
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s::smallint[], %s::smallint[], %s::smallint[], %s::smallint[],
            %s, %s, %s, %s, %s
        )
    """


def build_result_row(
    row: pd.Series,
    spec: AlgorithmSpec,
    pipeline_run_id: str,
    window_index: int,
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    predicted_main: List[int],
    predicted_euro: List[int],
    main_probs: Dict[str, float],
    euro_probs: Dict[str, float],
) -> ResultRow:
    hit_main = count_hits(predicted_main, draw_main_numbers(row))
    hit_euro = count_hits(predicted_euro, draw_euro_numbers(row))
    total_hits = hit_main + hit_euro

    probability_payload = {"main_probabilities": main_probs, "euro_probabilities": euro_probs}
    metrics_payload = {
        "window_index": window_index + 1,
        "feature_count": len(SELECTED_FEATURES),
        "selected_features": list(SELECTED_FEATURES),
        "train_window_start": int(train_df["draw_date"].iloc[0]),
        "train_window_end": int(train_df["draw_date"].iloc[-1]),
        "valid_window_start": int(valid_df["draw_date"].iloc[0]),
        "valid_window_end": int(valid_df["draw_date"].iloc[-1]),
        "hit_main_count": hit_main,
        "hit_euro_count": hit_euro,
        "total_hit_count": total_hits,
    }

    return (
        int(row["draw_date"]),
        int(row["draw_date"]),
        spec.model_name,
        MODEL_VERSION,
        pipeline_run_id,
        int(train_df["draw_date"].iloc[0]),
        int(train_df["draw_date"].iloc[-1]),
        int(valid_df["draw_date"].iloc[0]),
        int(valid_df["draw_date"].iloc[-1]),
        [int(x) for x in predicted_main],
        [int(x) for x in predicted_euro],
        draw_main_numbers(row),
        draw_euro_numbers(row),
        int(hit_main),
        int(hit_euro),
        total_hits / 7.0,
        Json(probability_payload),
        Json(metrics_payload),
    )


def insert_batch(conn, table: str, rows: List[ResultRow]) -> None:
    if not rows:
        return
    query = insert_query_for_table(table)
    normalized: List[ResultRow] = []
    for row in rows:
        normalized.append(
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
        execute_batch(cur, query, normalized, page_size=BATCH_SIZE)


def count_algorithm_rows(conn, spec: AlgorithmSpec) -> int:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) FROM backtest.{spec.table} WHERE model_name = %s",
            (spec.model_name,),
        )
        return int(cur.fetchone()[0])


def load_summary_from_table(conn, spec: AlgorithmSpec) -> Dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT hit_main_count, hit_euro_count
            FROM backtest.{spec.table}
            WHERE model_name = %s
            """,
            (spec.model_name,),
        )
        rows = cur.fetchall()

    if not rows:
        raise RuntimeError(f"No rows found for {spec.display_name} in backtest.{spec.table}")

    hit_main = [int(r[0]) for r in rows]
    hit_euro = [int(r[1]) for r in rows]
    summary = compute_hit_rates(hit_main, hit_euro)
    summary["display_name"] = spec.display_name
    summary["source"] = f"checkpoint resume → backtest.{spec.table}"
    return summary


def print_algorithm_mini_summary(summary: Dict[str, Any]) -> None:
    total = summary["hit_rate_total_3_plus"]
    baseline = RANDOM_BASELINE["hit_rate_total_3_plus"]
    improvement = improvement_vs_random(total, baseline)
    LOGGER.info(
        "%s done — hit_total_3_plus: %.2f%% (vs random %.2f%%, improvement: %+.2f%%)",
        summary["display_name"],
        total,
        baseline,
        improvement,
    )


def delete_existing_results(conn, spec: AlgorithmSpec) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM backtest.{spec.table} WHERE model_name = %s",
            (spec.model_name,),
        )
        deleted = cur.rowcount
    LOGGER.info("Deleted %d row(s) from %s for model_name=%s", deleted, spec.table, spec.model_name)


def run_walk_forward(conn, df: pd.DataFrame, spec: AlgorithmSpec, pipeline_run_id: str) -> List[ResultRow]:
    all_results: List[ResultRow] = []
    window_rows: List[ResultRow] = []

    for window_index, (train_slice, valid_slice) in enumerate(WALK_FORWARD_WINDOWS):
        train_df = df.iloc[train_slice].copy()
        valid_df = df.iloc[valid_slice].copy()
        window_rows = []

        if train_df.empty or valid_df.empty:
            raise RuntimeError(f"{spec.display_name}: empty split in window {window_index + 1}")
        if len(df) < valid_slice.stop:
            raise RuntimeError(
                f"{spec.display_name}: need draw index {valid_slice.stop - 1}, have {len(df) - 1}"
            )

        LOGGER.info(
            "%s window %d/5 | train=%d | validate=%d",
            spec.display_name,
            window_index + 1,
            len(train_df),
            len(valid_df),
        )

        main_models = train_number_classifiers(
            train_df, MAIN_NUMBERS, main_label, spec.build_classifier
        )
        euro_models = train_number_classifiers(
            train_df, EURO_NUMBERS, euro_label, spec.build_classifier
        )

        for _, row in valid_df.iterrows():
            predicted_main, predicted_euro, main_probs, euro_probs = predict_ticket(
                row, main_models, euro_models
            )
            result = build_result_row(
                row,
                spec,
                pipeline_run_id,
                window_index,
                train_df,
                valid_df,
                predicted_main,
                predicted_euro,
                main_probs,
                euro_probs,
            )
            window_rows.append(result)
            all_results.append(result)

            if len(window_rows) >= BATCH_SIZE:
                insert_batch(conn, spec.table, window_rows)
                window_rows.clear()

        insert_batch(conn, spec.table, window_rows)
        conn.commit()
        LOGGER.info(
            "%s window %d/5 committed (%d validation predictions)",
            spec.display_name,
            window_index + 1,
            len(valid_df),
        )

    return all_results


def run_algorithm(conn, df: pd.DataFrame, spec: AlgorithmSpec) -> Dict[str, Any]:
    row_count = count_algorithm_rows(conn, spec)
    if row_count >= CHECKPOINT_MIN_ROWS:
        LOGGER.info(
            "Skipping %s — already complete (%d rows)",
            spec.display_name,
            row_count,
        )
        summary = load_summary_from_table(conn, spec)
        print_algorithm_mini_summary(summary)
        return summary

    pipeline_run_id = str(uuid.uuid4())
    LOGGER.info("Starting %s | pipeline_run_id=%s", spec.display_name, pipeline_run_id)
    delete_existing_results(conn, spec)
    conn.commit()

    results = run_walk_forward(conn, df, spec, pipeline_run_id)
    hit_main = [row[13] for row in results]
    hit_euro = [row[14] for row in results]
    summary = compute_hit_rates(hit_main, hit_euro)
    summary["display_name"] = spec.display_name
    summary["source"] = f"walk-forward on 21 features → backtest.{spec.table}"

    if summary["total_predictions"] != EXPECTED_PREDICTIONS:
        LOGGER.warning(
            "%s expected %d predictions, got %d",
            spec.display_name,
            EXPECTED_PREDICTIONS,
            summary["total_predictions"],
        )

    print_algorithm_mini_summary(summary)
    return summary


def compute_hit_rates(hit_main: Sequence[int], hit_euro: Sequence[int]) -> Dict[str, float]:
    total = len(hit_main)
    if total == 0:
        return {
            "total_predictions": 0,
            "hit_rate_main_2_plus": 0.0,
            "hit_rate_main_3_plus": 0.0,
            "hit_rate_total_3_plus": 0.0,
        }

    main_2_plus = main_3_plus = total_3_plus = 0
    for hm, he in zip(hit_main, hit_euro):
        if hm >= 2:
            main_2_plus += 1
        if hm >= 3:
            main_3_plus += 1
        if hm + he >= 3:
            total_3_plus += 1

    return {
        "total_predictions": total,
        "hit_rate_main_2_plus": main_2_plus / total * 100.0,
        "hit_rate_main_3_plus": main_3_plus / total * 100.0,
        "hit_rate_total_3_plus": total_3_plus / total * 100.0,
    }


def load_xgboost_summary(conn) -> Dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT hit_main_count, hit_euro_count
            FROM backtest.backtest_xgboost
            WHERE model_name = 'xgboost'
            """
        )
        rows = cur.fetchall()

    if not rows:
        raise RuntimeError("No XGBoost results found in backtest.backtest_xgboost")

    hit_main = [int(r[0]) for r in rows]
    hit_euro = [int(r[1]) for r in rows]
    summary = compute_hit_rates(hit_main, hit_euro)
    summary["display_name"] = "XGBoost"
    LOGGER.info("Loaded %d XGBoost predictions from database", len(rows))
    return summary


def improvement_vs_random(metric: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return (metric - baseline) / baseline * 100.0


def build_comparison_rows(summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    random_total = RANDOM_BASELINE["hit_rate_total_3_plus"]
    rows = []

    random_row = {
        "display_name": RANDOM_BASELINE["display_name"],
        "hit_rate_main_2_plus": RANDOM_BASELINE["hit_rate_main_2_plus"],
        "hit_rate_main_3_plus": RANDOM_BASELINE["hit_rate_main_3_plus"],
        "hit_rate_total_3_plus": RANDOM_BASELINE["hit_rate_total_3_plus"],
        "vs_random_total_3_plus": 0.0,
        "source": "baseline",
    }
    rows.append(random_row)

    for summary in summaries:
        total = summary["hit_rate_total_3_plus"]
        rows.append(
            {
                "display_name": summary["display_name"],
                "hit_rate_main_2_plus": summary["hit_rate_main_2_plus"],
                "hit_rate_main_3_plus": summary["hit_rate_main_3_plus"],
                "hit_rate_total_3_plus": total,
                "vs_random_total_3_plus": improvement_vs_random(total, random_total),
                "source": summary.get("source", "walk-forward"),
                "total_predictions": summary.get("total_predictions", 0),
            }
        )

    ranked = sorted(
        [r for r in rows if r["display_name"] != "Random"],
        key=lambda r: r["vs_random_total_3_plus"],
        reverse=True,
    )
    return [random_row] + ranked


def save_comparison_markdown(comparison: List[Dict[str, Any]], winner: Dict[str, Any]) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    random_total = RANDOM_BASELINE["hit_rate_total_3_plus"]

    table_lines = [
        "| Algorithm | hit_main_2+ | hit_main_3+ | hit_total_3+ | vs Random |",
        "|-----------|-------------|-------------|--------------|-----------|",
    ]
    for row in comparison:
        if row["display_name"] == "Random":
            vs_random = "baseline"
        else:
            vs_random = f"{row['vs_random_total_3_plus']:+.2f}%"
        table_lines.append(
            f"| {row['display_name']} | {row['hit_rate_main_2_plus']:.2f}% | "
            f"{row['hit_rate_main_3_plus']:.2f}% | {row['hit_rate_total_3_plus']:.2f}% | {vs_random} |"
        )

    best_improvement = winner["vs_random_total_3_plus"]
    honest = (
        "All improvements over random are small in absolute terms. "
        "Lottery draws remain highly random; no algorithm guarantees better outcomes. "
    )
    if best_improvement <= 5:
        honest += (
            f"The best model ({winner['display_name']}) shows only a modest "
            f"{best_improvement:+.2f}% lift on hit_total_3_plus versus random."
        )
    else:
        honest += (
            f"{winner['display_name']} shows the largest lift ({best_improvement:+.2f}% on "
            "hit_total_3_plus), but this must be validated on future draws before any claim of edge."
        )

    content = f"""# Algorithm Comparison — Phase 5

**Generated:** {generated_at}  
**Features used:** 21 (Phase 4 selection)  
**Walk-forward windows:** 5 (same as Phase 3)  
**Random baseline hit_total_3+:** {random_total:.2f}%

---

## Comparison Table

{chr(10).join(table_lines)}

*Ranked by improvement on hit_total_3+ vs random (excluding Random row).*

---

## Winner

**{winner['display_name']}** — best hit_total_3+ improvement vs random: **{best_improvement:+.2f}%**

| Metric | Value |
|--------|-------|
| hit_rate_main_2_plus | {winner['hit_rate_main_2_plus']:.4f}% |
| hit_rate_main_3_plus | {winner['hit_rate_main_3_plus']:.4f}% |
| hit_rate_total_3_plus | {winner['hit_rate_total_3_plus']:.4f}% |
| Predictions | {winner.get('total_predictions', 'n/a')} |

---

## Key Findings

- Compared 6 approaches: Random baseline, XGBoost (Phase 3, 60 features), and 5 models on 21 features.
- XGBoost results were loaded from `backtest.backtest_xgboost` without re-training.
- New models used only the 21 features from `docs/FEATURE_IMPORTANCE.md`.
- Algorithms ranked by `hit_rate_total_3_plus` improvement over random ({random_total:.2f}%).

---

## Honest Assessment

{honest}

---

## Selected Features (21)

{", ".join(f"`{f}`" for f in SELECTED_FEATURES)}
"""

    RESULTS_PATH.write_text(content, encoding="utf-8")
    LOGGER.info("Saved comparison to %s", RESULTS_PATH)


def print_comparison(comparison: List[Dict[str, Any]]) -> None:
    LOGGER.info("=== Algorithm Comparison (ranked by hit_total_3+ vs random) ===")
    for row in comparison:
        if row["display_name"] == "Random":
            LOGGER.info(
                "%-20s main_2+=%.2f%% main_3+=%.2f%% total_3+=%.2f%% (baseline)",
                row["display_name"],
                row["hit_rate_main_2_plus"],
                row["hit_rate_main_3_plus"],
                row["hit_rate_total_3_plus"],
            )
        else:
            LOGGER.info(
                "%-20s main_2+=%.2f%% main_3+=%.2f%% total_3+=%.2f%% vs_random=%+.2f%%",
                row["display_name"],
                row["hit_rate_main_2_plus"],
                row["hit_rate_main_3_plus"],
                row["hit_rate_total_3_plus"],
                row["vs_random_total_3_plus"],
            )


def main() -> int:
    load_environment()
    conn = None

    try:
        conn = get_connection()
        conn.autocommit = False
        df = load_feature_matrix(conn)

        algorithm_summaries: List[Dict[str, Any]] = []

        xgb_summary = load_xgboost_summary(conn)
        xgb_summary["source"] = "loaded from backtest.backtest_xgboost (60 features, Phase 3)"
        print_algorithm_mini_summary(xgb_summary)
        algorithm_summaries.append(xgb_summary)

        for spec in ALGORITHMS_TO_RUN:
            try:
                summary = run_algorithm(conn, df, spec)
                algorithm_summaries.append(summary)
            except Exception:
                conn.rollback()
                raise

        comparison = build_comparison_rows(algorithm_summaries)
        winner = comparison[1] if len(comparison) > 1 else comparison[0]
        print_comparison(comparison)
        save_comparison_markdown(comparison, winner)

        LOGGER.info("Algorithm comparison completed successfully. Winner: %s", winner["display_name"])
        return 0

    except Exception:
        if conn is not None:
            conn.rollback()
        LOGGER.exception("Algorithm comparison failed")
        return 1

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())

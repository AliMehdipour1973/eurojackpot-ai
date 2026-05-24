#!/usr/bin/env python3
"""Phase 4: identify which features help XGBoost most via feature importance."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv

try:
    import xgboost  # noqa: F401
    import sklearn  # noqa: F401
except ImportError:
    print("Missing dependency. Run: pip install xgboost scikit-learn")
    sys.exit(1)

from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "feature_selection.log"
RESULTS_PATH = PROJECT_ROOT / "docs" / "FEATURE_IMPORTANCE.md"
ML_STRATEGY_PATH = PROJECT_ROOT / "docs" / "ML_STRATEGY.md"

MAIN_NUMBERS = list(range(1, 51))
EURO_NUMBERS = list(range(1, 13))
CLASSIFIER_COUNT = len(MAIN_NUMBERS) + len(EURO_NUMBERS)

XGB_PARAMS = {
    "n_estimators": 100,
    "max_depth": 4,
    "learning_rate": 0.1,
    "eval_metric": "logloss",
    "random_state": 42,
    "verbosity": 0,
}


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("feature_selection")
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


def feature_category(name: str) -> str:
    if name.startswith("freq_main_"):
        return "frequency"
    if name.startswith("trend_score_"):
        return "trend"
    return "other"


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


def build_classifier() -> XGBClassifier:
    return XGBClassifier(**XGB_PARAMS)


def main_number_label(df: pd.DataFrame, num: int) -> np.ndarray:
    return (
        (df["n1"] == num)
        | (df["n2"] == num)
        | (df["n3"] == num)
        | (df["n4"] == num)
        | (df["n5"] == num)
    ).astype(np.int32).to_numpy()


def euro_number_label(df: pd.DataFrame, num: int) -> np.ndarray:
    return ((df["e1"] == num) | (df["e2"] == num)).astype(np.int32).to_numpy()


def collect_feature_importances(df: pd.DataFrame) -> Dict[str, float]:
    features = feature_columns()
    x_all = df[features].to_numpy(dtype=np.float32)
    importance_sum = np.zeros(len(features), dtype=np.float64)
    trained = 0

    for num in MAIN_NUMBERS:
        y = main_number_label(df, num)
        model = build_classifier()
        model.fit(x_all, y)
        importance_sum += model.feature_importances_
        trained += 1
        if num % 10 == 0:
            LOGGER.info("Trained main number classifiers: %d / %d", trained, len(MAIN_NUMBERS))

    LOGGER.info("Completed %d main number classifiers", len(MAIN_NUMBERS))

    for num in EURO_NUMBERS:
        y = euro_number_label(df, num)
        model = build_classifier()
        model.fit(x_all, y)
        importance_sum += model.feature_importances_
        trained += 1

    LOGGER.info("Completed %d euro number classifiers", len(EURO_NUMBERS))

    avg_importance = importance_sum / CLASSIFIER_COUNT
    return {features[i]: float(avg_importance[i]) for i in range(len(features))}


def build_results_table(importance_map: Dict[str, float]) -> pd.DataFrame:
    total = sum(importance_map.values())
    if total <= 0:
        raise RuntimeError("Total feature importance is zero; cannot rank features")

    rows = []
    for feature_name, avg_importance in importance_map.items():
        rows.append(
            {
                "feature_name": feature_name,
                "avg_importance": avg_importance,
                "share": avg_importance / total,
                "category": feature_category(feature_name),
            }
        )

    results = pd.DataFrame(rows)
    results = results.sort_values("avg_importance", ascending=False).reset_index(drop=True)
    results["rank"] = results.index + 1
    results["cumulative_share"] = results["share"].cumsum()

    idx_80 = int(results[results["cumulative_share"] >= 0.80].index[0])
    idx_90 = int(results[results["cumulative_share"] >= 0.90].index[0])
    keep_80 = set(results.loc[:idx_80, "feature_name"])
    keep_90 = set(results.loc[:idx_90, "feature_name"])

    results["keep_80"] = results["feature_name"].isin(keep_80)
    results["keep_90"] = results["feature_name"].isin(keep_90)

    results.attrs["count_80"] = idx_80 + 1
    results.attrs["count_90"] = idx_90 + 1
    return results


def print_results(results: pd.DataFrame) -> None:
    count_80 = results.attrs["count_80"]
    count_90 = results.attrs["count_90"]

    LOGGER.info("=== Feature Importance Summary ===")
    LOGGER.info("Features needed for 80%% coverage: %d / 60", count_80)
    LOGGER.info("Features needed for 90%% coverage: %d / 60", count_90)

    LOGGER.info("--- Top 20 features ---")
    top20 = results.head(20)
    for _, row in top20.iterrows():
        LOGGER.info(
            "  #%2d %-18s importance=%.6f  cumulative=%.2f%%  %s",
            int(row["rank"]),
            row["feature_name"],
            row["avg_importance"],
            row["cumulative_share"] * 100,
            row["category"],
        )

    LOGGER.info("--- Bottom 10 features ---")
    bottom10 = results.tail(10).sort_values("rank")
    for _, row in bottom10.iterrows():
        LOGGER.info(
            "  #%2d %-18s importance=%.6f  %s",
            int(row["rank"]),
            row["feature_name"],
            row["avg_importance"],
            row["category"],
        )


def recommendation_text(results: pd.DataFrame) -> str:
    keep_80 = results[results["keep_80"]]["feature_name"].tolist()
    remove_candidates = results[~results["keep_80"]]["feature_name"].tolist()
    freq_kept = sum(1 for f in keep_80 if feature_category(f) == "frequency")
    trend_kept = sum(1 for f in keep_80 if feature_category(f) == "trend")

    return f"""For Phase 5, keep the **{results.attrs["count_80"]} features** that cover 80% of cumulative importance:

{", ".join(f"`{f}`" for f in keep_80)}

- Frequency features retained: {freq_kept}
- Trend features retained: {trend_kept}

Consider dropping **{len(remove_candidates)}** low-importance features (below 80% threshold):

{", ".join(f"`{f}`" for f in remove_candidates) if remove_candidates else "_none_"}

Use the 90% set ({results.attrs["count_90"]} features) if you want a slightly larger feature set with marginal extra coverage."""


def save_feature_importance_md(results: pd.DataFrame) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    count_80 = results.attrs["count_80"]
    count_90 = results.attrs["count_90"]

    keep_80_list = results[results["keep_80"]]["feature_name"].tolist()
    bottom_list = results[~results["keep_80"]]["feature_name"].tolist()

    table_lines = [
        "| Rank | Feature | Avg Importance | Share | Cumulative | Category | Keep 80% | Keep 90% |",
        "|------|---------|----------------|-------|------------|----------|----------|----------|",
    ]
    for _, row in results.iterrows():
        table_lines.append(
            f"| {int(row['rank'])} | `{row['feature_name']}` | {row['avg_importance']:.6f} | "
            f"{row['share']*100:.2f}% | {row['cumulative_share']*100:.2f}% | {row['category']} | "
            f"{'Yes' if row['keep_80'] else 'No'} | {'Yes' if row['keep_90'] else 'No'} |"
        )

    content = f"""# Feature Importance — Phase 4

**Generated:** {generated_at}  
**Training draws:** 435  
**Classifiers:** 50 main (binary per number) + 12 euro (binary per number), averaged importance  
**XGBoost:** n_estimators=100, max_depth=4, learning_rate=0.1

---

## Coverage Summary

| Threshold | Features Required |
|-----------|-------------------|
| 80% cumulative importance | {count_80} |
| 90% cumulative importance | {count_90} |

---

## Full Ranked Table (60 features)

{chr(10).join(table_lines)}

---

## Top Features (80% coverage)

{chr(10).join(f"- `{name}`" for name in keep_80_list)}

---

## Bottom Features (candidates for removal)

{chr(10).join(f"- `{name}`" for name in bottom_list) if bottom_list else "_All features are within the 80% set._"}

---

## Recommendation for Phase 5

{recommendation_text(results)}
"""

    RESULTS_PATH.write_text(content, encoding="utf-8")
    LOGGER.info("Saved results to %s", RESULTS_PATH)


def update_ml_strategy(results: pd.DataFrame) -> None:
    if not ML_STRATEGY_PATH.exists():
        LOGGER.warning("ML_STRATEGY.md not found; skipping strategy update")
        return

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    count_80 = results.attrs["count_80"]
    count_90 = results.attrs["count_90"]
    top5 = results.head(5)["feature_name"].tolist()
    keep_80 = results[results["keep_80"]]["feature_name"].tolist()

    section = f"""## Phase 4 Results — Feature Selection

**Completed:** {generated_at}

| Metric | Value |
|--------|-------|
| Features analyzed | 60 |
| Classifiers averaged | 62 (50 main + 12 euro) |
| Features for 80% importance | {count_80} |
| Features for 90% importance | {count_90} |
| Top feature | `{results.iloc[0]["feature_name"]}` |

**Top 5 features:** {", ".join(f"`{f}`" for f in top5)}

**Phase 5 recommendation:** Keep {count_80} features at 80% coverage. See `docs/FEATURE_IMPORTANCE.md` for full ranking.

**Features to keep:** {", ".join(f"`{f}`" for f in keep_80)}

"""

    text = ML_STRATEGY_PATH.read_text(encoding="utf-8")
    placeholder = "## Phase 4 Results — Feature Selection\n\n(leave placeholder — script will fill this)\n"
    if placeholder in text:
        text = text.replace(placeholder, section)
    elif "## Phase 4 Results — Feature Selection" in text:
        start = text.index("## Phase 4 Results — Feature Selection")
        end = text.find("\n## ", start + 1)
        if end == -1:
            end = len(text)
        text = text[:start] + section + text[end:]
    else:
        marker = "## Decisions Log"
        if marker in text:
            text = text.replace(marker, section + "\n" + marker, 1)
        else:
            text = text.rstrip() + "\n\n" + section

    ML_STRATEGY_PATH.write_text(text, encoding="utf-8")
    LOGGER.info("Updated %s with Phase 4 results", ML_STRATEGY_PATH)


def main() -> int:
    load_environment()
    conn = None

    try:
        conn = get_connection()
        df = load_feature_matrix(conn)

        if len(df) < 435:
            LOGGER.warning("Expected 435 draws; found %d", len(df))

        importance_map = collect_feature_importances(df)
        results = build_results_table(importance_map)

        print_results(results)
        save_feature_importance_md(results)
        update_ml_strategy(results)

        LOGGER.info("Feature selection completed successfully.")
        return 0

    except Exception:
        LOGGER.exception("Feature selection failed")
        return 1

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())

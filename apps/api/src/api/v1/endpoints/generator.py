"""Generate EuroJackpot tickets via XGBoost (21 features) or pure random."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from xgboost import XGBClassifier

from apps.api.src.core.logging import logger
from apps.api.src.db.connection import engine, get_db

router = APIRouter()

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

MAIN_NUMBERS = list(range(1, 51))
EURO_NUMBERS = list(range(1, 13))
MODEL_VERSION = "v1.0"

XGB_PARAMS = {
    "n_estimators": 100,
    "max_depth": 4,
    "learning_rate": 0.1,
    "eval_metric": "logloss",
    "random_state": 42,
    "verbosity": 0,
}

DISCLAIMER = (
    "Generated numbers are for entertainment and research only. "
    "Lottery draws are random; past patterns do not guarantee future results. "
    "XGBoost backtest hit_total_3+ was 4.68% vs 3.20% random (+46% relative); "
    "still means ~95% of tickets miss 3+ hits."
)

BACKTEST_REFERENCE = {
    "hit_total_3_plus_random_pct": 3.20,
    "hit_total_3_plus_xgboost_pct": 4.68,
    "hit_main_2_plus_random_pct": 7.10,
    "hit_main_2_plus_xgboost_pct": 7.23,
}

_model_cache: Dict[str, Tuple[Dict[int, XGBClassifier], Dict[int, XGBClassifier]]] = {}
_cached_latest_draw_date: Optional[int] = None


class GenerateRequest(BaseModel):
    mode: Literal["xgboost", "random"] = "xgboost"


class GenerateResponse(BaseModel):
    mode: str
    model_version: str
    training_draws: int
    based_on_features_from: int
    predicting_for: str
    next_draw_date: int
    feature_count: int
    features_used: List[str]
    main_numbers: List[int]
    euro_numbers: List[int]
    main_probabilities: Optional[Dict[str, float]] = None
    euro_probabilities: Optional[Dict[str, float]] = None
    disclaimer: str
    backtest_reference: Dict[str, float]


def load_feature_matrix() -> pd.DataFrame:
    draws = pd.read_sql(
        """
        SELECT draw_date, n1, n2, n3, n4, n5, e1, e2
        FROM core.draws
        ORDER BY draw_date ASC
        """,
        engine,
    )
    if draws.empty:
        raise HTTPException(status_code=404, detail="No draws in database")

    freq = pd.read_sql(
        """
        SELECT draw_date, number, frequency_count
        FROM features.frq_numbers
        WHERE window_size = 0
        ORDER BY draw_date ASC, number ASC
        """,
        engine,
    )
    freq_pivot = freq.pivot(
        index="draw_date", columns="number", values="frequency_count"
    ).reset_index()
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
        engine,
    )

    df = draws.merge(freq_pivot, on="draw_date", how="left").merge(
        trend, on="draw_date", how="left"
    )
    df = df.sort_values("draw_date").reset_index(drop=True)

    for col in SELECTED_FEATURES:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].fillna(0.0)

    return df


def get_next_draw_date(last_draw_date: int) -> int:
    """Next EuroJackpot draw (Tuesday or Friday) after last_draw_date."""
    last = datetime.strptime(str(last_draw_date), "%Y%m%d").date()
    for offset in range(1, 8):
        candidate = last + timedelta(days=offset)
        if candidate.weekday() in (1, 4):
            return int(candidate.strftime("%Y%m%d"))
    raise HTTPException(status_code=500, detail="Could not compute next draw date")


def split_prediction_data(
    df: pd.DataFrame,
) -> Tuple[int, int, pd.Series, pd.DataFrame]:
    """Train on draws 1..N-1; predict using features from draw N-1 for draw N."""
    if len(df) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 draws to predict the next draw without leakage",
        )
    latest_draw_date = int(df.iloc[-1]["draw_date"])
    feature_row = df.iloc[-2]
    feature_draw_date = int(feature_row["draw_date"])
    training_df = df.iloc[:-1]
    return latest_draw_date, feature_draw_date, feature_row, training_df


def draw_main_numbers(row: pd.Series) -> List[int]:
    return sorted([int(row["n1"]), int(row["n2"]), int(row["n3"]), int(row["n4"]), int(row["n5"])])


def draw_euro_numbers(row: pd.Series) -> List[int]:
    return sorted([int(row["e1"]), int(row["e2"])])


def main_label(row: pd.Series, number: int) -> int:
    return int(number in draw_main_numbers(row))


def euro_label(row: pd.Series, number: int) -> int:
    return int(number in draw_euro_numbers(row))


def positive_class_proba(model: XGBClassifier, x_row: pd.DataFrame) -> float:
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
) -> Dict[int, XGBClassifier]:
    x_train = train_df[list(SELECTED_FEATURES)]
    models: Dict[int, XGBClassifier] = {}
    for number in numbers:
        y_train = train_df.apply(lambda row: label_fn(row, number), axis=1).to_numpy(
            dtype="int32"
        )
        model = XGBClassifier(**XGB_PARAMS)
        model.fit(x_train, y_train)
        models[number] = model
    return models


def get_cached_models(
    latest_draw_date: int,
    train_df: pd.DataFrame,
) -> Tuple[Dict[int, XGBClassifier], Dict[int, XGBClassifier]]:
    global _cached_latest_draw_date

    if _cached_latest_draw_date != latest_draw_date:
        _model_cache.clear()
        _cached_latest_draw_date = latest_draw_date

    cache_key = str(latest_draw_date)
    cached = _model_cache.get(cache_key)
    if cached is not None:
        return cached

    logger.info(
        "Training XGBoost classifiers for generator (latest_draw=%s, train_rows=%d)",
        cache_key,
        len(train_df),
    )
    main_models = train_number_classifiers(train_df, MAIN_NUMBERS, main_label)
    euro_models = train_number_classifiers(train_df, EURO_NUMBERS, euro_label)
    _model_cache[cache_key] = (main_models, euro_models)
    return main_models, euro_models


def weighted_sample(
    numbers: Sequence[int],
    prob_map: Dict[str, float],
    size: int,
) -> List[int]:
    """Sample without replacement; probabilities act as weights (not guaranteed top-k)."""
    probs = np.array(
        [prob_map.get(str(n), 0.001) for n in numbers], dtype=np.float64
    )
    probs = probs / probs.sum()
    selected = np.random.choice(list(numbers), size=size, replace=False, p=probs)
    return sorted(int(n) for n in selected)


def predict_ticket(
    row: pd.Series,
    main_models: Dict[int, XGBClassifier],
    euro_models: Dict[int, XGBClassifier],
) -> Tuple[List[int], List[int], Dict[str, float], Dict[str, float]]:
    x_row = row[list(SELECTED_FEATURES)].to_frame().T

    main_probs = {
        str(n): positive_class_proba(main_models[n], x_row) for n in MAIN_NUMBERS
    }
    euro_probs = {
        str(n): positive_class_proba(euro_models[n], x_row) for n in EURO_NUMBERS
    }

    predicted_main = weighted_sample(range(1, 51), main_probs, size=5)
    predicted_euro = weighted_sample(range(1, 13), euro_probs, size=2)

    return predicted_main, predicted_euro, main_probs, euro_probs


def generate_random_ticket() -> Tuple[List[int], List[int]]:
    return (
        sorted(random.sample(range(1, 51), 5)),
        sorted(random.sample(range(1, 13), 2)),
    )


@router.post("/generator/generate", response_model=GenerateResponse)
def generate_ticket(
    body: GenerateRequest,
    db: Session = Depends(get_db),
) -> GenerateResponse:
    del db  # matrix loaded via engine; keeps DI consistent with other endpoints

    df = load_feature_matrix()
    latest_draw_date, feature_draw_date, feature_row, training_df = split_prediction_data(
        df
    )
    training_count = len(training_df)
    predicting_for = f"draw after {latest_draw_date}"
    next_draw = get_next_draw_date(latest_draw_date)

    if body.mode == "random":
        main_numbers, euro_numbers = generate_random_ticket()
        return GenerateResponse(
            mode="random",
            model_version=MODEL_VERSION,
            training_draws=training_count,
            based_on_features_from=feature_draw_date,
            predicting_for=predicting_for,
            next_draw_date=next_draw,
            feature_count=0,
            features_used=[],
            main_numbers=main_numbers,
            euro_numbers=euro_numbers,
            disclaimer=DISCLAIMER,
            backtest_reference=BACKTEST_REFERENCE,
        )

    main_models, euro_models = get_cached_models(latest_draw_date, training_df)
    main_numbers, euro_numbers, main_probs, euro_probs = predict_ticket(
        feature_row, main_models, euro_models
    )

    return GenerateResponse(
        mode="xgboost",
        model_version=MODEL_VERSION,
        training_draws=training_count,
        based_on_features_from=feature_draw_date,
        predicting_for=predicting_for,
        next_draw_date=next_draw,
        feature_count=len(SELECTED_FEATURES),
        features_used=list(SELECTED_FEATURES),
        main_numbers=main_numbers,
        euro_numbers=euro_numbers,
        main_probabilities=main_probs,
        euro_probabilities=euro_probs,
        disclaimer=DISCLAIMER,
        backtest_reference=BACKTEST_REFERENCE,
    )

from fastapi import APIRouter, Query
from pathlib import Path
import pandas as pd


router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


# ============================================================
# CONFIG
# ============================================================

PREDICTIONS_FILE = Path(
    "/app/ml/prediction/models/latest_predictions.csv"
)


# ============================================================
# LOAD PREDICTIONS
# ============================================================

def load_predictions():

    if not PREDICTIONS_FILE.exists():
        return None

    df = pd.read_csv(PREDICTIONS_FILE)

    return df


# ============================================================
# ALL PREDICTIONS
# ============================================================

@router.get("")
def get_predictions(
    limit: int = Query(
        default=20,
        ge=1,
        le=500
    ),
    min_probability: float = Query(
        default=0,
        ge=0,
        le=100
    ),
):

    df = load_predictions()

    if df is None:
        return {
            "status": "error",
            "message": "Prediction model has not been trained yet.",
            "count": 0,
            "predictions": [],
        }

    # Filter by probability
    df = df[
        df["prediction_probability"] >= min_probability
    ]

    # Highest probability first
    df = df.sort_values(
        "prediction_probability",
        ascending=False
    )

    df = df.head(limit)

    results = []

    for _, row in df.iterrows():

        results.append({
            "ward_number": int(row["ward_number"]),
            "category": row["category"],
            "prediction_probability": round(
                float(row["prediction_probability"]),
                2
            ),
            "predicted_next_month": bool(
                row["predicted_next_month"]
            ),
        })

    return {
        "status": "ok",
        "count": len(results),
        "predictions": results,
    }


# ============================================================
# PREDICTIONS FOR A SPECIFIC WARD
# ============================================================

@router.get("/ward/{ward_number}")
def get_ward_predictions(
    ward_number: int,
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
):

    df = load_predictions()

    if df is None:
        return {
            "status": "error",
            "message": "Prediction model has not been trained yet.",
            "ward_number": ward_number,
            "count": 0,
            "predictions": [],
        }

    df = df[
        df["ward_number"] == ward_number
    ]

    df = df.sort_values(
        "prediction_probability",
        ascending=False
    )

    df = df.head(limit)

    results = []

    for _, row in df.iterrows():

        results.append({
            "ward_number": int(row["ward_number"]),
            "category": row["category"],
            "prediction_probability": round(
                float(row["prediction_probability"]),
                2
            ),
            "predicted_next_month": bool(
                row["predicted_next_month"]
            ),
        })

    return {
        "status": "ok",
        "ward_number": ward_number,
        "count": len(results),
        "predictions": results,
    }


# ============================================================
# PREDICTIONS FOR A CATEGORY
# ============================================================

@router.get("/category/{category}")
def get_category_predictions(
    category: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
):

    df = load_predictions()

    if df is None:
        return {
            "status": "error",
            "message": "Prediction model has not been trained yet.",
            "category": category,
            "count": 0,
            "predictions": [],
        }

    df = df[
        df["category"].str.lower()
        == category.lower()
    ]

    df = df.sort_values(
        "prediction_probability",
        ascending=False
    )

    df = df.head(limit)

    results = []

    for _, row in df.iterrows():

        results.append({
            "ward_number": int(row["ward_number"]),
            "category": row["category"],
            "prediction_probability": round(
                float(row["prediction_probability"]),
                2
            ),
            "predicted_next_month": bool(
                row["predicted_next_month"]
            ),
        })

    return {
        "status": "ok",
        "category": category,
        "count": len(results),
        "predictions": results,
    }
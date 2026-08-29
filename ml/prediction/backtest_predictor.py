import os
import joblib
import pandas as pd

from sqlalchemy import create_engine

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/urban_hotspot"
)

MODEL_PATH = "/app/ml/prediction/models/problem_predictor.joblib"
OUTPUT_DIR = "/app/ml/prediction/models"

FEATURES = [
    "ward_number",
    "category",
    "complaint_count",
    "complaints_3m",
    "complaints_6m",
    "active_months_3m",
    "active_months_6m",
    "historical_active_months",
    "trend_3m",
    "month_of_year",
]

TARGET = "target_next_month"


def load_data():

    print("Loading historical prediction data...")

    engine = create_engine(DATABASE_URL)

    query = """
        SELECT
            ward_number,
            category,
            month,
            complaint_count,
            complaints_3m,
            complaints_6m,
            active_months_3m,
            active_months_6m,
            historical_active_months,
            trend_3m,
            month_of_year,
            target_next_month
        FROM prediction_training_data
        WHERE target_next_month IS NOT NULL
        ORDER BY month
    """

    df = pd.read_sql(query, engine)

    df["month"] = pd.to_datetime(df["month"])

    print(f"Total records: {len(df)}")
    print(f"Positive records: {df[TARGET].sum()}")
    print(f"Negative records: {(df[TARGET] == 0).sum()}")

    return df


def main():

    # =========================================================
    # LOAD MODEL
    # =========================================================

    print()
    print("Loading trained model...")

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}\n"
            "Run train_predictor.py first."
        )

    model = joblib.load(MODEL_PATH)

    print("Model loaded successfully.")

    # =========================================================
    # LOAD DATA
    # =========================================================

    df = load_data()

    # =========================================================
    # SAME TIME-BASED TEST PERIOD AS TRAINING
    # =========================================================

    test = df[
        df["month"] >= pd.Timestamp("2025-07-01")
    ].copy()

    print()
    print("Backtest period:")
    print(test["month"].min(), "→", test["month"].max())

    print()
    print(f"Backtest records: {len(test)}")

    X_test = test[FEATURES]
    y_test = test[TARGET]

    # =========================================================
    # PREDICTIONS
    # =========================================================

    print()
    print("Generating historical predictions...")

    probabilities = model.predict_proba(X_test)[:, 1]

    test["prediction_probability"] = probabilities * 100

    test["predicted_next_month"] = (
        test["prediction_probability"] >= 50
    ).astype(int)

    # =========================================================
    # OVERALL METRICS
    # =========================================================

    predictions = test["predicted_next_month"]

    print()
    print("=" * 60)
    print("OVERALL BACKTEST RESULTS")
    print("=" * 60)

    print()
    print("Classification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    print("Confusion Matrix:")

    print(
        confusion_matrix(
            y_test,
            predictions
        )
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )

    print()
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")

    if len(set(y_test)) == 2:

        auc = roc_auc_score(
            y_test,
            probabilities
        )

        ap = average_precision_score(
            y_test,
            probabilities
        )

        print(f"ROC-AUC:   {auc:.4f}")
        print(f"Avg Precision: {ap:.4f}")

    # =========================================================
    # CATEGORY PERFORMANCE
    # =========================================================

    print()
    print("=" * 60)
    print("CATEGORY PERFORMANCE")
    print("=" * 60)

    category_results = []

    for category, group in test.groupby("category"):

        y_true = group[TARGET]

        y_pred = group["predicted_next_month"]

        category_precision = precision_score(
            y_true,
            y_pred,
            zero_division=0
        )

        category_recall = recall_score(
            y_true,
            y_pred,
            zero_division=0
        )

        category_f1 = f1_score(
            y_true,
            y_pred,
            zero_division=0
        )

        actual_events = int(y_true.sum())

        predicted_events = int(y_pred.sum())

        if len(set(y_true)) == 2:

            category_auc = roc_auc_score(
                y_true,
                group["prediction_probability"]
            )

        else:

            category_auc = None

        category_results.append(
            {
                "category": category,
                "records": len(group),
                "actual_events": actual_events,
                "predicted_events": predicted_events,
                "precision": round(category_precision, 4),
                "recall": round(category_recall, 4),
                "f1": round(category_f1, 4),
                "roc_auc": (
                    round(category_auc, 4)
                    if category_auc is not None
                    else None
                ),
            }
        )

    category_df = pd.DataFrame(
        category_results
    )

    category_df = category_df.sort_values(
        "f1",
        ascending=False
    )

    print(
        category_df.to_string(
            index=False
        )
    )

    # =========================================================
    # TOP CORRECT PREDICTIONS
    # =========================================================

    correct_predictions = test[
        (test[TARGET] == 1) &
        (test["predicted_next_month"] == 1)
    ].copy()

    correct_predictions = correct_predictions.sort_values(
        "prediction_probability",
        ascending=False
    )

    print()
    print("=" * 60)
    print("TOP CORRECT PREDICTIONS")
    print("=" * 60)

    print(
        correct_predictions[
            [
                "ward_number",
                "category",
                "month",
                "prediction_probability",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    # =========================================================
    # FALSE POSITIVES
    # =========================================================

    false_positives = test[
        (test[TARGET] == 0) &
        (test["predicted_next_month"] == 1)
    ].copy()

    false_positives = false_positives.sort_values(
        "prediction_probability",
        ascending=False
    )

    print()
    print("=" * 60)
    print("TOP FALSE POSITIVE PREDICTIONS")
    print("=" * 60)

    print(
        false_positives[
            [
                "ward_number",
                "category",
                "month",
                "prediction_probability",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    # =========================================================
    # FALSE NEGATIVES
    # =========================================================

    false_negatives = test[
        (test[TARGET] == 1) &
        (test["predicted_next_month"] == 0)
    ].copy()

    false_negatives = false_negatives.sort_values(
        "prediction_probability",
        ascending=False
    )

    print()
    print("=" * 60)
    print("TOP MISSED EVENTS")
    print("=" * 60)

    print(
        false_negatives[
            [
                "ward_number",
                "category",
                "month",
                "prediction_probability",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    # =========================================================
    # SAVE BACKTEST PREDICTIONS
    # =========================================================

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    predictions_path = os.path.join(
        OUTPUT_DIR,
        "backtest_predictions.csv"
    )

    test[
        [
            "ward_number",
            "category",
            "month",
            "prediction_probability",
            "predicted_next_month",
            "target_next_month",
        ]
    ].to_csv(
        predictions_path,
        index=False
    )

    # =========================================================
    # SAVE CATEGORY RESULTS
    # =========================================================

    category_path = os.path.join(
        OUTPUT_DIR,
        "backtest_category_results.csv"
    )

    category_df.to_csv(
        category_path,
        index=False
    )

    print()
    print("=" * 60)
    print("BACKTEST FILES SAVED")
    print("=" * 60)

    print()
    print(f"Predictions:")
    print(predictions_path)

    print()
    print(f"Category results:")
    print(category_path)

    print()
    print("Backtesting complete.")


if __name__ == "__main__":
    main()
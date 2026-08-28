import os
import json
import joblib
import pandas as pd

from sqlalchemy import create_engine

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
)
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/urban_hotspot"
)

MODEL_DIR = "/app/ml/prediction/models"
MODEL_PATH = os.path.join(MODEL_DIR, "problem_predictor.joblib")


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
    print("Loading training data...")

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

    # PostgreSQL returns DATE as datetime.date.
    # Convert it explicitly so all date comparisons work.
    df["month"] = pd.to_datetime(df["month"])

    print(f"Total records: {len(df)}")
    print(f"Positive records: {df[TARGET].sum()}")
    print(f"Negative records: {(df[TARGET] == 0).sum()}")

    return df


def build_model():

    categorical_features = ["category"]

    numeric_features = [
        "ward_number",
        "complaint_count",
        "complaints_3m",
        "complaints_6m",
        "active_months_3m",
        "active_months_6m",
        "historical_active_months",
        "trend_3m",
        "month_of_year",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "category",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False
                ),
                categorical_features,
            ),
            (
                "numeric",
                "passthrough",
                numeric_features,
            ),
        ]
    )

    classifier = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def main():

    df = load_data()

    # ---------------------------------------------------------
    # TIME-BASED TRAIN / TEST SPLIT
    # ---------------------------------------------------------

    train = df[df["month"] < pd.Timestamp("2025-07-01")].copy()

    test = df[df["month"] >= pd.Timestamp("2025-07-01")].copy()

    print()
    print("Training period:")
    print(train["month"].min(), "→", train["month"].max())

    print("Testing period:")
    print(test["month"].min(), "→", test["month"].max())

    print()
    print(f"Training records: {len(train)}")
    print(f"Testing records: {len(test)}")

    X_train = train[FEATURES]
    y_train = train[TARGET]

    X_test = test[FEATURES]
    y_test = test[TARGET]

    # ---------------------------------------------------------
    # MODEL
    # ---------------------------------------------------------

    print()
    print("Building model...")

    model = build_model()

    print("Training Random Forest...")

    model.fit(X_train, y_train)

    print("Training complete.")

    # ---------------------------------------------------------
    # EVALUATION
    # ---------------------------------------------------------

    print()
    print("Evaluating model...")

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

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
    print(confusion_matrix(y_test, predictions))

    if len(set(y_test)) == 2:
        auc = roc_auc_score(y_test, probabilities)
        ap = average_precision_score(y_test, probabilities)

        print()
        print(f"ROC-AUC: {auc:.4f}")
        print(f"Average Precision: {ap:.4f}")

    # ---------------------------------------------------------
    # SAVE MODEL
    # ---------------------------------------------------------

    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(model, MODEL_PATH)

    print()
    print(f"Model saved to:")
    print(MODEL_PATH)

    # ---------------------------------------------------------
    # GENERATE CURRENT PREDICTIONS
    # ---------------------------------------------------------

    latest_month = df["month"].max()

    latest = df[df["month"] == latest_month].copy()

    if len(latest) > 0:

        latest_X = latest[FEATURES]

        latest["prediction_probability"] = (
            model.predict_proba(latest_X)[:, 1] * 100
        )

        latest["predicted_next_month"] = (
            latest["prediction_probability"] >= 50
        ).astype(int)

        latest = latest.sort_values(
            "prediction_probability",
            ascending=False
        )

        predictions_path = os.path.join(
            MODEL_DIR,
            "latest_predictions.csv"
        )

        latest[
            [
                "ward_number",
                "category",
                "month",
                "prediction_probability",
                "predicted_next_month",
            ]
        ].to_csv(
            predictions_path,
            index=False
        )

        print()
        print(f"Latest predictions saved to:")
        print(predictions_path)

        print()
        print("Top 20 predictions:")

        print(
            latest[
                [
                    "ward_number",
                    "category",
                    "prediction_probability",
                    "predicted_next_month",
                ]
            ].head(20).to_string(index=False)
        )


if __name__ == "__main__":
    main()
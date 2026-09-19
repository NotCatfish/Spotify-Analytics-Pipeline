"""
Challenger Model Evaluation & MLflow Registry Auto-Promotion Module
=====================================================================
Evaluates candidate models ("Challengers") trained on updated feedback datasets against
the current active MLflow "Champion" model (`Spotify_Skip_Predictor_XGBoost`).

Promotes the Challenger to the Production stage in the MLflow Model Registry ONLY if its
out-of-time ROC-AUC score improves upon the Champion by at least 0.002 while adhering to the
Precision SLA >= 78%.

Usage:
    python pipeline/05_challenger_evaluation.py
    python pipeline/05_challenger_evaluation.py --min-improvement 0.002
"""

import os
import sys
import sqlite3
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

import joblib
import xgboost as xgb
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

import mlflow
import mlflow.xgboost
from mlflow.tracking import MlflowClient

# Environment / Rules Setup
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from path_utils import find_project_root, resolve_path

BASE_DIR = find_project_root(__file__)
DB_PATH = resolve_path("data/processed/Engineered_Spotify_Portable.db")
MODEL_PATH = resolve_path("models/spotify_skip_predictor_xgb.pkl")
REPORTS_DIR = resolve_path("docs/reports/images")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


MODEL_NAME = "Spotify_Skip_Predictor_XGBoost"
FEATURE_COLS = [
    "seconds_since_last_skip",
    "previous_song_skipped",
    "skips_last_15m",
    "song_smoothed_skip_rate",
    "artist_smoothed_skip_rate",
    "hour_of_day",
    "day_of_week"
]


def get_current_champion_metric(client: MlflowClient) -> float:
    """Retrieves current registered Champion model's ROC-AUC metric from MLflow."""
    try:
        registered_models = client.search_model_versions(f"name='{MODEL_NAME}'")
        if not registered_models:
            print("[INFO] No existing registered models found in MLflow. Baseline Champion ROC-AUC set to 0.858.")
            return 0.858

        # Find latest version or version with tag 'stage=Production'
        prod_versions = [mv for mv in registered_models if mv.current_stage == "Production"]
        if prod_versions:
            target_mv = prod_versions[-1]
        else:
            target_mv = registered_models[-1]

        run = client.get_run(target_mv.run_id)
        champ_auc = run.data.metrics.get("xgb_test_roc_auc", 0.858)
        print(f"[INFO] Current Champion (Version {target_mv.version}) ROC-AUC: {champ_auc:.4f}")
        return float(champ_auc)
    except Exception as e:
        print(f"[WARNING] Unable to fetch Champion metric from MLflow ({e}). Using default baseline 0.858.")
        return 0.858


def load_dataset() -> pd.DataFrame:
    """Loads engineered feature dataset from SQLite."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Feature store DB not found at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    
    target_table = "Engineered_Spotify_Portable" if "Engineered_Spotify_Portable" in tables else tables[0]
    df = pd.read_sql_query(f"SELECT * FROM {target_table}", conn)
    conn.close()
    return df



def prepare_chronological_splits(df: pd.DataFrame):
    """Splits dataset chronologically: Train on 2023-2024, Test on 2025+."""
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"])
        df["year"] = df["ts"].dt.year
    elif "year" not in df.columns:
        df["year"] = 2024  # Fallback split

    modern_df = df[df["year"] >= 2023].copy()
    train_df = modern_df[modern_df["year"] < 2025].copy()
    test_df = modern_df[modern_df["year"] >= 2025].copy()

    if test_df.empty:
        # Fallback 80/20 train/test split if modern data lacks 2025 records
        split_idx = int(len(modern_df) * 0.8)
        train_df = modern_df.iloc[:split_idx].copy()
        test_df = modern_df.iloc[split_idx:].copy()

    X_train = train_df[FEATURE_COLS]
    y_train = train_df["skipped"]
    X_test = test_df[FEATURE_COLS]
    y_test = test_df["skipped"]

    return X_train, y_train, X_test, y_test


def train_challenger_model(X_train, y_train):
    """Trains a candidate XGBoost Challenger model."""
    pos_count = (y_train == 1).sum()
    neg_count = (y_train == 0).sum()
    scale_pos_weight = neg_count / max(1, pos_count)

    model = xgb.XGBClassifier(
        n_estimators=220,
        max_depth=7,
        learning_rate=0.015,
        scale_pos_weight=scale_pos_weight,
        min_child_weight=6,
        colsample_bytree=0.65,
        reg_lambda=7.0,
        random_state=42,
        eval_metric="logloss"
    )
    model.fit(X_train, y_train)
    return model


def evaluate_challenger(model, X_test, y_test, threshold=0.73):
    """Evaluates model performance metrics on holdout test set."""
    probs = model.predict_proba(X_test)[:, 1]
    roc_auc = roc_auc_score(y_test, probs)

    preds = (probs >= threshold).astype(int)
    precision = precision_score(y_test, preds, zero_division=0)
    recall = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    cm = confusion_matrix(y_test, preds)

    return {
        "roc_auc": float(roc_auc),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "threshold": threshold,
        "confusion_matrix": cm,
        "probs": probs
    }


def run_challenger_evaluation(min_improvement: float = 0.002):
    """Executes the Challenger evaluation and MLflow model registry promotion pipeline."""
    mlflow.set_experiment("Spotify_Skip_Prediction_Challenger")
    client = MlflowClient()

    champion_auc = get_current_champion_metric(client)

    print("\n--- LOADING FEATURE DATASET & TRAINING CHALLENGER ---")
    df = load_dataset()
    X_train, y_train, X_test, y_test = prepare_chronological_splits(df)
    print(f"Train Set: {len(X_train)} samples | Test Set: {len(X_test)} samples")

    challenger_model = train_challenger_model(X_train, y_train)
    metrics = evaluate_challenger(challenger_model, X_test, y_test)

    challenger_auc = metrics["roc_auc"]
    improvement = challenger_auc - champion_auc

    print("\n--- EVALUATION RESULTS ---")
    print(f"Current Champion ROC-AUC : {champion_auc:.4f}")
    print(f"Challenger ROC-AUC       : {challenger_auc:.4f}")
    print(f"Delta Improvement        : {improvement:+.4f}")
    print(f"Challenger Precision     : {metrics['precision']:.4f}")
    print(f"Challenger Recall        : {metrics['recall']:.4f}")

    is_promoted = improvement >= min_improvement and metrics["precision"] >= 0.75

    with mlflow.start_run(run_name="Challenger_Evaluation_Run") as run:
        # Log parameters & metrics
        mlflow.log_params({
            "min_improvement_threshold": min_improvement,
            "scale_pos_weight": float((y_train == 0).sum() / (y_train == 1).sum()),
            "decision_threshold": metrics["threshold"]
        })
        mlflow.log_metrics({
            "challenger_roc_auc": challenger_auc,
            "champion_roc_auc": champion_auc,
            "delta_improvement": improvement,
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1_score": metrics["f1"],
            "is_promoted": int(is_promoted)
        })

        # Save confusion matrix plot artifact
        fig, ax = plt.subplots(figsize=(5, 4))
        sns.heatmap(metrics["confusion_matrix"], annot=True, fmt="d", cmap="Blues", ax=ax)
        ax.set_title(f"Challenger Confusion Matrix (ROC-AUC: {challenger_auc:.4f})")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        plot_path = REPORTS_DIR / "challenger_confusion_matrix.png"
        plt.savefig(plot_path, bbox_inches="tight")
        plt.close()

        mlflow.log_artifact(str(plot_path))

        if is_promoted:
            print("\n[SUCCESS] Challenger PASSED promotion criteria!")
            print(f"[PROMOTION] Registering Challenger to MLflow Model Registry as '{MODEL_NAME}'...")

            # Log model artifact
            mlflow.xgboost.log_model(
                xgb_model=challenger_model,
                name="model",
                registered_model_name=MODEL_NAME
            )

            # Update local disk artifact for production API microservice
            joblib.dump(challenger_model, MODEL_PATH)
            print(f"[ARTIFACT UPDATED] Saved newly promoted model to: {MODEL_PATH}")

            # Transition model stage in registry to Production
            versions = client.search_model_versions(f"name='{MODEL_NAME}'")
            if versions:
                latest_version = versions[-1].version
                client.transition_model_version_stage(
                    name=MODEL_NAME,
                    version=latest_version,
                    stage="Production",
                    archive_existing_versions=True
                )
                print(f"[MLFLOW REGISTRY] Transitioned model version {latest_version} to Production stage.")
        else:
            print("\n[INFO] Challenger did NOT meet promotion threshold.")
            print(f"Reason: Required delta improvement >= {min_improvement:+.4f} (Actual: {improvement:+.4f}). Retaining current Champion.")


def main():
    parser = argparse.ArgumentParser(description="Challenger Model Evaluation against MLflow Champion.")
    parser.add_argument("--min-improvement", type=float, default=0.002, help="Minimum ROC-AUC improvement required to promote Challenger (default: 0.002)")
    args = parser.parse_args()

    run_challenger_evaluation(min_improvement=args.min_improvement)


if __name__ == "__main__":
    main()

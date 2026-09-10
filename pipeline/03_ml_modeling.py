# =====================================================================
# STAGE 3: SPOTIFY MACHINE LEARNING MODELING & SKIP PREDICTION PIPELINE
# =====================================================================

# 1. Standard Library
import io
import os
from pathlib import Path
import re
import sqlite3
import sys
import warnings
warnings.filterwarnings("ignore")

# 2. Third-Party Libraries
from dotenv import find_dotenv, load_dotenv
import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/CLI environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_curve, roc_auc_score
from sqlalchemy import create_engine, text
from xgboost import XGBClassifier

# --- Environment & Directory Setup ---
env_path = find_dotenv(usecwd=True)
if not env_path:
    for candidate in [
        Path.cwd() / "ML_Roadmap" / ".env",
        Path.cwd().parent / "ML_Roadmap" / ".env",
        Path.cwd().parent / ".env"
    ]:
        if candidate.exists():
            env_path = str(candidate)
            break
if env_path:
    load_dotenv(env_path)

if Path.cwd().name == "notebooks" or Path.cwd().name == "pipeline":
    PROJECT_ROOT = Path.cwd().parent
else:
    PROJECT_ROOT = Path.cwd() / "ML_Roadmap" if (Path.cwd() / "ML_Roadmap").exists() else Path.cwd()

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

REPORTS_DIR = PROJECT_ROOT / "reports"
IMAGES_DIR = REPORTS_DIR / "images"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_BASE_NAME = "Engineered_Spotify_Portable"
DEFAULT_PG_URI = os.getenv("POSTGRES_URI", "postgresql://postgres:password@localhost:5432/postgres")


def compress_numeric_columns(df):
    """Compresses all numeric columns to their lowest memory representation."""
    if df is None:
        return None
    initial_mem = df.memory_usage().sum() / (1024 * 1024)
    num_cols = df.select_dtypes(include=["number"]).columns
    for col in num_cols:
        c_min = df[col].min()
        c_max = df[col].max()
        if pd.api.types.is_integer_dtype(df[col]):
            if c_min >= -128 and c_max <= 127:
                df[col] = df[col].astype("int8")
            elif c_min >= -32768 and c_max <= 32767:
                df[col] = df[col].astype("int16")
            elif c_min >= -2147483648 and c_max <= 2147483647:
                df[col] = df[col].astype("int32")
            else:
                df[col] = df[col].astype("int64")
        elif pd.api.types.is_float_dtype(df[col]):
            if not df[col].isna().any() and np.array_equal(df[col], df[col].astype("int64")):
                if c_min >= -128 and c_max <= 127:
                    df[col] = df[col].astype("int8")
                elif c_min >= -32768 and c_max <= 32767:
                    df[col] = df[col].astype("int16")
                elif c_min >= -2147483648 and c_max <= 2147483647:
                    df[col] = df[col].astype("int32")
                else:
                    df[col] = df[col].astype("int64")
            else:
                df[col] = df[col].astype("float32")
    final_mem = df.memory_usage().sum() / (1024 * 1024)
    print(f"Memory compressed: {initial_mem:.2f} MB -> {final_mem:.2f} MB ({((initial_mem - final_mem) / initial_mem) * 100:.1f}% reduction)")
    return df


def ingest_feature_data():
    """Interactive ingestion of engineered feature store from SQLite or PostgreSQL."""
    print("\n--- DATA INGESTION SETUP ---")
    print(f"Directory: {PROCESSED_DIR}")

    base_name = None
    is_default_name = False
    while True:
        try:
            name_input = input(f"Enter name of file / table to load [press Enter for default: {DEFAULT_BASE_NAME}]: ").strip()
            if not name_input:
                base_name = DEFAULT_BASE_NAME
                is_default_name = True
            else:
                base_name = name_input[:-3] if name_input.lower().endswith(".db") else name_input
                is_default_name = False
            break
        except (KeyboardInterrupt, EOFError):
            print("\nData loading cancelled by user (Escape pressed).")
            return None

    db_filename = f"{base_name}.db"
    table_name = base_name
    print(f"Target File : '{db_filename}'")
    print(f"Target Table: '{table_name}'")

    print("\nWhere do you want to load data from?")
    print("1: sql (SQLite .db)")
    print("2: postgres (PostgreSQL)")

    source_choice = None
    while True:
        try:
            choice_input = input("Where do you want to load data from? (1: sql, 2: postgres) [press Enter for default: 1]: ").strip()
            choice = choice_input or "1"
            if choice in ["1", "2"]:
                source_choice = choice
                break
            print("Invalid choice! You must enter 1 or 2. Please try again (or press Esc to cancel).")
        except (KeyboardInterrupt, EOFError):
            print("\nData loading cancelled by user (Escape pressed).")
            return None

    feature_df = None
    if source_choice == "1":
        while True:
            try:
                db_file = PROCESSED_DIR / db_filename
                if not db_file.exists():
                    if is_default_name and (PROCESSED_DIR / "Cleaned_Spotify_Portable.db").exists():
                        print(f"\n[NOTICE] '{db_filename}' not found, falling back to 'Cleaned_Spotify_Portable.db'...")
                        db_file = PROCESSED_DIR / "Cleaned_Spotify_Portable.db"
                        table_name = "streaming_history"
                    else:
                        print(f"\n[ERROR] File '{db_filename}' does not exist in: {PROCESSED_DIR}")
                        avail = [f.name for f in PROCESSED_DIR.glob("*.db")]
                        if avail:
                            print(f"Available files in directory: {avail}")
                        retry = input(f"Enter valid file name [press Enter for default: {DEFAULT_BASE_NAME}.db]: ").strip()
                        raw = retry or DEFAULT_BASE_NAME
                        base_name = raw[:-3] if raw.lower().endswith(".db") else raw
                        is_default_name = (not retry)
                        db_filename = f"{base_name}.db"
                        table_name = base_name
                        continue

                print(f"\nLoading from SQLite: {db_file}...")
                conn = sqlite3.connect(db_file)
                sqlite_tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

                if table_name in sqlite_tables:
                    target_tbl = table_name
                elif is_default_name and "streaming_history" in sqlite_tables:
                    target_tbl = "streaming_history"
                elif is_default_name and sqlite_tables:
                    target_tbl = sqlite_tables[0]
                else:
                    conn.close()
                    print(f"\n[ERROR] Table '{table_name}' does not exist in '{db_file.name}'! Available: {sqlite_tables}")
                    retry_tbl = input(f"Enter valid table name [press Enter for default: {sqlite_tables[0]}]: ").strip()
                    table_name = retry_tbl or sqlite_tables[0]
                    continue

                feature_df = pd.read_sql_query(f'SELECT * FROM "{target_tbl}"', conn)
                conn.close()
                feature_df = compress_numeric_columns(feature_df)
                print(f"Loaded {len(feature_df):,} rows successfully from SQLite (table: '{target_tbl}')!")
                break
            except (KeyboardInterrupt, EOFError):
                print("\nSQLite load cancelled by user (Escape pressed).")
                return None
            except Exception as e:
                print(f"\n[ERROR] Error reading SQLite database: {e}. Please try again (or press Esc to cancel).\n")

    elif source_choice == "2":
        masked_default = re.sub(r":([^@:/]+)@", ":****@", DEFAULT_PG_URI)
        print("\n--- PostgreSQL Connection Setup ---")
        print(f"Default URI: {masked_default}")
        print("Press Enter to use default URI, or enter custom URI (or press Esc to cancel).")
        while True:
            try:
                uri_input = input(f"Enter PostgreSQL Connection URI [press Enter for default: {DEFAULT_PG_URI}]: ").strip()
                postgres_uri = uri_input or DEFAULT_PG_URI
                masked_uri = re.sub(r":([^@:/]+)@", ":****@", postgres_uri)

                print(f"Connecting to PostgreSQL: {masked_uri}...")
                engine = create_engine(postgres_uri)
                with engine.connect() as check_conn:
                    pg_tables = [r[0] for r in check_conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()]

                if table_name in pg_tables:
                    actual_table = table_name
                elif is_default_name and "streaming_history" in pg_tables:
                    actual_table = "streaming_history"
                else:
                    engine.dispose()
                    def_pg = "streaming_history" if "streaming_history" in pg_tables else (pg_tables[0] if pg_tables else "")
                    print(f"\n[ERROR] Table '{table_name}' does not exist in PostgreSQL public schema! Available: {pg_tables}")
                    retry_tbl = input(f"Enter valid table name [press Enter for default: {def_pg}]: ").strip()
                    table_name = retry_tbl or def_pg
                    is_default_name = (not retry_tbl)
                    continue

                feature_df = pd.read_sql_table(actual_table, engine)
                engine.dispose()
                feature_df = compress_numeric_columns(feature_df)
                print(f"Loaded {len(feature_df):,} rows successfully from PostgreSQL (table: '{actual_table}')!")
                break
            except (KeyboardInterrupt, EOFError):
                print("\nPostgreSQL load cancelled by user (Escape pressed).")
                return None
            except Exception as e:
                print(f"\n[ERROR] Failed to connect: {e}. Please try again (or press Esc to cancel).\n")

    if feature_df is not None:
        # Check if features are missing (e.g. loaded raw Cleaned dataset instead of Engineered feature store)
        required_features = ["artist_smoothed_skip_rate", "song_smoothed_skip_rate", "seconds_since_last_skip", "skips_last_15m"]
        if not all(col in feature_df.columns for col in required_features):
            print("\n[INFO] Engineered features not detected in dataset. Computing behavioral features on the fly...")
            feature_df["time_stamp"] = pd.to_datetime(feature_df["time_stamp"])
            feature_df = feature_df.sort_values(by="time_stamp").reset_index(drop=True)
            feature_df["is_skip"] = (feature_df["reason_end"] == "fwdbtn").astype(int)
            feature_df["hour_of_day"] = feature_df["time_stamp"].dt.hour.astype("int8")
            feature_df["day_of_week"] = feature_df["time_stamp"].dt.dayofweek.astype("int8")
            feature_df["day_of_month"] = feature_df["time_stamp"].dt.day.astype("int8")
            feature_df["year"] = feature_df["time_stamp"].dt.year.astype("int16")

            global_skip_rate = feature_df["is_skip"].mean()
            smoothing_weight = 20

            feature_df["artist_past_plays"] = feature_df.groupby("artist_name").cumcount()
            feature_df["artist_past_skips"] = feature_df.groupby("artist_name")["is_skip"].cumsum() - feature_df["is_skip"]
            feature_df["artist_smoothed_skip_rate"] = (
                (feature_df["artist_past_skips"] + (smoothing_weight * global_skip_rate)) /
                (feature_df["artist_past_plays"] + smoothing_weight)
            ).astype("float32")

            feature_df["song_past_plays"] = feature_df.groupby("song_name").cumcount()
            feature_df["song_past_skips"] = feature_df.groupby("song_name")["is_skip"].cumsum() - feature_df["is_skip"]
            feature_df["song_smoothed_skip_rate"] = (
                (feature_df["song_past_skips"] + (smoothing_weight * global_skip_rate)) /
                (feature_df["song_past_plays"] + smoothing_weight)
            ).astype("float32")

            feature_df = feature_df.drop(columns=["artist_past_plays", "artist_past_skips", "song_past_plays", "song_past_skips"])
            feature_df["previous_song_skipped"] = feature_df["is_skip"].shift(1).fillna(0).astype("int8")

            skips_only = feature_df[feature_df["is_skip"] == 1][["time_stamp"]]
            feature_df["last_skip_time"] = pd.merge_asof(
                feature_df[["time_stamp"]],
                skips_only.assign(last_skip_time=skips_only["time_stamp"]),
                on="time_stamp",
                direction="backward",
                allow_exact_matches=False
            )["last_skip_time"]

            feature_df["seconds_since_last_skip"] = (
                (feature_df["time_stamp"] - feature_df["last_skip_time"]).dt.total_seconds().fillna(10000)
            ).astype("float32")
            feature_df = feature_df.drop(columns=["last_skip_time"])

            feature_df = feature_df.set_index("time_stamp").sort_index()
            feature_df["skips_last_15m"] = (feature_df["is_skip"].rolling("15min").sum() - feature_df["is_skip"]).astype("float32")
            feature_df = feature_df.reset_index()
            feature_df = compress_numeric_columns(feature_df)
            print("On-the-fly feature engineering completed successfully!")

        cols_to_drop = [
            "ip_addr",
            "episode_name",
            "episode_show_name",
            "spotify_episode_uri",
            "audiobook_title",
            "audiobook_uri",
            "audiobook_chapter_uri",
            "audiobook_chapter_title"
        ]
        feature_df = feature_df.drop(columns=[c for c in cols_to_drop if c in feature_df.columns])

    return feature_df


def train_and_evaluate_models(feature_df):
    """Executes chronological split, model training, threshold tuning, and evaluation."""
    print("\n--- ML MODELING PIPELINE ---")

    features = [
        "artist_smoothed_skip_rate",
        "song_smoothed_skip_rate",
        "seconds_since_last_skip",
        "skips_last_15m",
        "previous_song_skipped",
        "hour_of_day",
        "day_of_week"
    ]
    target = "is_skip"

    # 1. Combating Concept Drift: Modern Windowing (2023+)
    modern_df = feature_df[feature_df["year"] >= 2023].dropna(subset=features + [target]).copy()

    # 2. Chronological Train/Test Split
    train_df = modern_df[modern_df["year"] <= 2024]
    test_df = modern_df[modern_df["year"] >= 2025]

    X_train = train_df[features]
    y_train = train_df[target]
    X_test = test_df[features]
    y_test = test_df[target]

    print(f"Training set (2023-2024): {len(X_train):,} samples | Skip rate: {y_train.mean()*100:.2f}%")
    print(f"Testing set  (2025+):      {len(X_test):,} samples | Skip rate: {y_test.mean()*100:.2f}%")

    # 3. Model 1: Balanced Random Forest
    print("\n[1/3] Training Balanced Random Forest Classifier...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)

    y_probs_rf = rf_model.predict_proba(X_test)[:, 1]
    precisions_rf, recalls_rf, thresholds_rf = precision_recall_curve(y_test, y_probs_rf)
    f1_scores_rf = 2 * (precisions_rf * recalls_rf) / (precisions_rf + recalls_rf + 1e-9)
    best_idx_rf = np.argmax(f1_scores_rf)
    best_thresh_rf = thresholds_rf[best_idx_rf]

    print("=" * 55)
    print(f"RANDOM FOREST PERFORMANCE (ROC-AUC: {roc_auc_score(y_test, y_probs_rf):.3f})")
    print(f"Optimal Decision Threshold : {best_thresh_rf:.3f}")
    print(f"Tuned Precision            : {precisions_rf[best_idx_rf]:.2f}")
    print(f"Tuned Recall               : {recalls_rf[best_idx_rf]:.2f}")
    print("=" * 55)

    custom_preds_rf = (y_probs_rf >= best_thresh_rf).astype(int)
    print("\nClassification Report (Random Forest Tuned):")
    print(classification_report(y_test, custom_preds_rf, target_names=["Listen (0)", "Skip (1)"]))

    rf_importances = pd.Series(rf_model.feature_importances_, index=features).sort_values(ascending=False)
    print("\nRandom Forest Feature Importances:")
    print(rf_importances.to_string())

    # 4. Model 2: Cost-Sensitive XGBoost
    print("\n[2/3] Training Cost-Sensitive XGBoost Classifier...")
    imbalance_ratio = len(y_train[y_train == 0]) / len(y_train[y_train == 1])
    print(f"XGBoost scale_pos_weight: {imbalance_ratio:.2f}")

    xgb_model = XGBClassifier(
        n_estimators=100,
        scale_pos_weight=imbalance_ratio,
        learning_rate=0.1,
        max_depth=6,
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(X_train, y_train)

    y_probs_xgb = xgb_model.predict_proba(X_test)[:, 1]
    precisions_xgb, recalls_xgb, thresholds_xgb = precision_recall_curve(y_test, y_probs_xgb)
    f1_scores_xgb = 2 * (precisions_xgb * recalls_xgb) / (precisions_xgb + recalls_xgb + 1e-9)
    best_idx_xgb = np.argmax(f1_scores_xgb)
    best_thresh_xgb = thresholds_xgb[best_idx_xgb]

    print("=" * 55)
    print(f"XGBOOST PERFORMANCE (ROC-AUC: {roc_auc_score(y_test, y_probs_xgb):.3f})")
    print(f"Optimal Decision Threshold : {best_thresh_xgb:.3f}")
    print(f"Tuned Precision            : {precisions_xgb[best_idx_xgb]:.2f}")
    print(f"Tuned Recall               : {recalls_xgb[best_idx_xgb]:.2f}")
    print("=" * 55)

    custom_preds_xgb = (y_probs_xgb >= best_thresh_xgb).astype(int)
    print("\nClassification Report (XGBoost Tuned):")
    print(classification_report(y_test, custom_preds_xgb, target_names=["Listen (0)", "Skip (1)"]))

    xgb_importances = pd.Series(xgb_model.feature_importances_, index=features).sort_values(ascending=False)
    print("\nXGBoost Feature Importances:")
    print(xgb_importances.to_string())

    # 5. Confusion Matrix Diagnostics & Heatmap Plot
    print("\n[3/3] Generating Confusion Matrix Diagnostics...")
    cm_xgb = confusion_matrix(y_test, custom_preds_xgb)
    text_cm = pd.crosstab(
        y_test,
        custom_preds_xgb,
        rownames=["Actual Ground Truth"],
        colnames=["Model Prediction"]
    ).rename(index={0: "Listen (0)", 1: "Skip (1)"}, columns={0: "Listen (0)", 1: "Skip (1)"})

    print("\nXGBoost Confusion Matrix (Counts):")
    print(text_cm.to_string())

    # Save heatmap visualization
    plt.figure(figsize=(7, 5))
    sns.heatmap(
        cm_xgb,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Predicted: Listen (0)", "Predicted: Skip (1)"],
        yticklabels=["Actual: Listen (0)", "Actual: Skip (1)"]
    )
    plt.title(f"XGBoost Confusion Matrix (Tuned Threshold: {best_thresh_xgb:.3f})")
    plt.ylabel("Actual Ground Truth")
    plt.xlabel("Model Prediction")
    plt.tight_layout()
    cm_fig_path = IMAGES_DIR / "ml_xgb_confusion_matrix.png"
    plt.savefig(cm_fig_path, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"Confusion Matrix Heatmap saved to: {cm_fig_path}")

    # 6. Model Serialization & Artifact Persistence
    model_artifact_path = MODELS_DIR / "spotify_skip_predictor_xgb.pkl"
    model_payload = {
        "model": xgb_model,
        "features": features,
        "best_threshold": float(best_thresh_xgb),
        "target": target
    }
    joblib.dump(model_payload, str(model_artifact_path))
    print(f"\nTrained model artifact saved successfully to: {model_artifact_path}")
    print(f"Artifact File Size: {os.path.getsize(model_artifact_path) / 1024:.2f} KB")


def main():
    print("=" * 65)
    print("   SPOTIFY SKIP PREDICTOR - MACHINE LEARNING PIPELINE")
    print("=" * 65)

    feature_df = ingest_feature_data()
    if feature_df is None:
        print("\nPipeline execution cancelled.")
        return

    train_and_evaluate_models(feature_df)
    print("\nAll ML Modeling tasks completed successfully!")


if __name__ == "__main__":
    main()

import argparse
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import precision_recall_curve, classification_report, roc_auc_score, confusion_matrix
import joblib

# Silence warnings for clean terminal output
import warnings
warnings.filterwarnings('ignore')

def parse_args():
    parser = argparse.ArgumentParser(description="Spotify Skip Prediction Pipeline")
    parser.add_argument("--input-type", type=str, choices=["csv", "json", "sqlite", "postgres"], default="csv",
                        help="Format of the input database (default: csv)")
    parser.add_argument("--input-path", type=str, default="data/processed/Cleaned_Spotify_Data.csv",
                        help="Path to the cleaned data file")
    parser.add_argument("--db-uri", type=str, default="postgresql://user:password@localhost:5432/postgres",
                        help="PostgreSQL Connection URI (if using postgres)")
    parser.add_argument("--save-model", action="store_true",
                        help="Save the trained XGBoost model to disk")
    args = parser.parse_args()
    
    import sys
    if len(sys.argv) == 1:
        print("=== Interactive Setup ===")
        args.input_type = input("How is your cleaned data stored? (csv/json/sqlite/postgres) [default: csv]: ").strip().lower() or "csv"
        
        if args.input_type in ["csv", "json", "sqlite"]:
            default_path = f"data/processed/Cleaned_Spotify_Data.{'db' if args.input_type=='sqlite' else args.input_type}"
            args.input_path = input(f"Enter the path to the {args.input_type.upper()} file [default: {default_path}]: ").strip() or default_path
        elif args.input_type == "postgres":
            args.db_uri = input("Enter PostgreSQL URI: ").strip()
            
        save = input("Do you want to save the trained model? (y/n) [default: y]: ").strip().lower()
        args.save_model = (save != 'n')
        
    return args

def load_cleaned_data(args):
    """Loads data from the chosen database in memory-efficient chunks."""
    print(f"Loading data from {args.input_type}...")
    compressed_chunks = []
    
    if args.input_type == "csv":
        master_df = pd.read_csv(args.input_path)
        
    elif args.input_type == "json":
        master_df = pd.read_json(args.input_path)
        
    elif args.input_type == "sqlite":
        conn = sqlite3.connect(args.input_path)
        # Assuming the SQLite database is small enough to load entirely for feature eng, 
        # but let's emulate the chunking for consistency with the notebook
        for chunk in pd.read_sql_query("SELECT * FROM streaming_history", conn, chunksize=10000):
            genre_columns = [col for col in chunk.columns if col.startswith("genre_")]
            cols_to_compress = genre_columns + ["shuffle", "skipped"]
            cols_to_compress = [c for c in cols_to_compress if c in chunk.columns]
            chunk[cols_to_compress] = chunk[cols_to_compress].astype("int8")
            compressed_chunks.append(chunk)
        conn.close()
        master_df = pd.concat(compressed_chunks, ignore_index=True)
        
    elif args.input_type == "postgres":
        engine = create_engine(args.db_uri)
        for chunk in pd.read_sql_table("streaming_history", engine, chunksize=10000):
            genre_columns = [col for col in chunk.columns if col.startswith("genre_")]
            cols_to_compress = genre_columns + ["shuffle", "skipped"]
            cols_to_compress = [c for c in cols_to_compress if c in chunk.columns]
            chunk[cols_to_compress] = chunk[cols_to_compress].astype("int8")
            compressed_chunks.append(chunk)
        master_df = pd.concat(compressed_chunks, ignore_index=True)
    master_df["time_stamp"] = pd.to_datetime(master_df["time_stamp"])
    print("Database loaded with maximum RAM efficiency!")
    return master_df

def feature_engineering(master_df):
    """Applies Dynamic Target Encoding and Micro-Mood Tracking"""
    print("Applying Feature Engineering...")
    
    # 0. CREATE THE GROUND TRUTH SKIP COLUMN
    # Using your discovery that 'fwdbtn' is the only reliable skip indicator
    if 'reason_end' in master_df.columns:
        master_df['is_skip'] = (master_df['reason_end'] == 'fwdbtn').astype(int)
    else:
        # Fallback to the 'skipped' column if reason_end is dropped
        master_df['is_skip'] = master_df['skipped']

    # 1. DYNAMIC TARGET ENCODING WITH SMOOTHING
    # Sort chronologically to prevent data leakage
    master_df = master_df.sort_values('time_stamp').reset_index(drop=True)

    # Get running count of plays and skips FOR EACH ARTIST
    master_df['artist_past_plays'] = master_df.groupby('artist_name').cumcount()
    master_df['artist_past_skips'] = master_df.groupby('artist_name')['is_skip'].cumsum() - master_df['is_skip']

    # Set smoothing parameters
    global_skip_rate = master_df['is_skip'].mean() 
    smoothing_weight = 20 

    # Calculate the Smoothed Dynamic Rate for Artists
    master_df['artist_smoothed_skip_rate'] = (master_df['artist_past_skips'] + (smoothing_weight * global_skip_rate)) / (master_df['artist_past_plays'] + smoothing_weight)

    # Repeat for Songs
    master_df['song_past_plays'] = master_df.groupby('song_name').cumcount()
    master_df['song_past_skips'] = master_df.groupby('song_name')['is_skip'].cumsum() - master_df['is_skip']
    master_df['song_smoothed_skip_rate'] = (master_df['song_past_skips'] + (smoothing_weight * global_skip_rate)) / (master_df['song_past_plays'] + smoothing_weight)

    # Clean up temporary columns
    master_df = master_df.drop(columns=['artist_past_plays', 'artist_past_skips', 'song_past_plays', 'song_past_skips'])

    # 2. MICRO-MOOD TRACKING (LAG & SESSION)
    # --- FEATURE A: Time Since Last Skip ---
    skips_only = master_df[master_df['is_skip'] == 1][['time_stamp']]

    master_df['last_skip_time'] = pd.merge_asof(
        master_df[['time_stamp']], 
        skips_only.assign(last_skip_time=skips_only['time_stamp']), 
        on='time_stamp', 
        direction='backward', 
        allow_exact_matches=False 
    )['last_skip_time']

    master_df['seconds_since_last_skip'] = (master_df['time_stamp'] - master_df['last_skip_time']).dt.total_seconds().fillna(10000)
    master_df = master_df.drop(columns=['last_skip_time'])

    # --- FEATURE B: Skip Velocity (Skips in the last 15 minutes) ---
    master_df = master_df.set_index('time_stamp').sort_index()
    master_df['skips_last_15m'] = master_df['is_skip'].rolling('15min').sum() - master_df['is_skip'] 
    master_df = master_df.reset_index()

    # Extract basic time features
    master_df['year'] = master_df['time_stamp'].dt.year
    master_df['hour_of_day'] = master_df['time_stamp'].dt.hour
    master_df['day_of_week'] = master_df['time_stamp'].dt.dayofweek

    print("Feature Engineering Complete!")
    return master_df

def train_and_evaluate(master_df, args):
    """Splits data chronologically and trains XGBoost/RF models."""
    print("Preparing data for modeling...")

    # STRATEGY 1: Windowing. Brutally delete all ancient data before 2023
    modern_df = master_df[master_df['year'] >= 2023].copy()

    features = [
        'artist_smoothed_skip_rate', 
        'song_smoothed_skip_rate',
        'seconds_since_last_skip', 
        'skips_last_15m',
        'hour_of_day', 
        'day_of_week'
    ]
    target = 'is_skip'

    modern_df = modern_df.dropna(subset=features + [target])

    # STRICT CHRONOLOGICAL SPLIT (Train 2023-2024, Test 2025+)
    train_df = modern_df[modern_df['year'] <= 2024]
    test_df = modern_df[modern_df['year'] >= 2025]

    X_train = train_df[features]
    y_train = train_df[target]
    X_test = test_df[features]
    y_test = test_df[target]

    print(f"Training on {len(X_train)} rows (2023-2024)...")
    print(f"Testing on {len(X_test)} rows (2025+)...")

    # --- TRAIN XGBOOST ---
    print("\nTraining XGBoost...")
    imbalance_ratio = len(y_train[y_train == 0]) / len(y_train[y_train == 1])
    
    xgb_model = XGBClassifier(
        n_estimators=100, 
        scale_pos_weight=imbalance_ratio, 
        random_state=42, 
        n_jobs=-1,
        learning_rate=0.1,
        max_depth=6
    )
    xgb_model.fit(X_train, y_train)

    # Tuning
    y_probs_xgb = xgb_model.predict_proba(X_test)[:, 1]
    precisions_xgb, recalls_xgb, thresholds_xgb = precision_recall_curve(y_test, y_probs_xgb)
    f1_scores_xgb = 2 * (precisions_xgb * recalls_xgb) / (precisions_xgb + recalls_xgb + 1e-9) 
    best_threshold_idx_xgb = np.argmax(f1_scores_xgb)
    best_threshold_xgb = thresholds_xgb[best_threshold_idx_xgb]

    custom_preds_xgb = (y_probs_xgb >= best_threshold_xgb).astype(int)

    print("\n" + "="*40)
    print(f"🏆 Best Mathematical Threshold (XGB): {best_threshold_xgb:.3f}")
    print(f"🎯 Resulting Precision (XGB): {precisions_xgb[best_threshold_idx_xgb]:.2f}")
    print(f"🎣 Resulting Recall (XGB): {recalls_xgb[best_threshold_idx_xgb]:.2f}")
    print(f"📊 ROC-AUC Score (XGB): {roc_auc_score(y_test, y_probs_xgb):.3f}")
    print("="*40)

    print("\n--- Final Tuned Classification Report (XGBoost) ---")
    print(classification_report(y_test, custom_preds_xgb))

    text_cm = pd.crosstab(
        y_test, 
        custom_preds_xgb, 
        rownames=['Actual (True)'], 
        colnames=['Predicted (Model)']
    )
    print("\n--- XGBoost Confusion Matrix ---")
    print(text_cm)
    
    importances_xgb = pd.Series(xgb_model.feature_importances_, index=features).sort_values(ascending=False)
    print("\n--- Feature Importance (XGBoost) ---")
    print(importances_xgb)

    if args.save_model:
        model_path = "xgboost_skip_predictor.joblib"
        joblib.dump(xgb_model, model_path)
        print(f"\nModel saved successfully to {model_path}")

def main():
    args = parse_args()
    master_df = load_cleaned_data(args)
    master_df = feature_engineering(master_df)
    train_and_evaluate(master_df, args)
    print("\nML Modeling pipeline completed successfully!")

if __name__ == "__main__":
    main()

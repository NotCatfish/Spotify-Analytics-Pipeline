"""
Daily Model Retraining Engine & Verification State Machine
===========================================================
Executes daily model retraining at 0:00 UTC with automated retry tracking.
A persistent status flag (`data/audit/retrain_status.json`) tracks whether
the model was successfully retrained for the current UTC date.

If retraining succeeded today, the script exits immediately (clean no-op).
If retraining has not yet succeeded today (or failed), it retrains the model
using all available telemetry, validates performance against SLA guardrails,
persists the updated model artifact, and updates the status flag.
"""

import os
import sys
import json
import math
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, precision_recall_curve

# Dynamic path resolution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from path_utils import resolve_path, find_project_root

PROJECT_ROOT = find_project_root(__file__)
DEFAULT_STATUS_PATH = resolve_path("data/audit/retrain_status.json")
DEFAULT_AUDIT_PATH = resolve_path("data/audit/shadow_audit.jsonl")
DEFAULT_MODEL_PATH = resolve_path("models/spotify_skip_predictor_xgb.pkl")
DEFAULT_LOOKUP_PATH = resolve_path("data/processed/feature_store_lookup.json")
DEFAULT_BASELINE_PARQUET = resolve_path("data/processed/modern_historical_baseline.parquet")
DEFAULT_HIST_DB = resolve_path("data/processed/Engineered_Spotify_Portable.db.bak")
DEFAULT_CURR_DB = resolve_path("data/processed/Engineered_Spotify_Portable.db")

FEATURE_COLUMNS = [
    "artist_smoothed_skip_rate",
    "song_smoothed_skip_rate",
    "genre_smoothed_skip_rate",
    "album_smoothed_skip_rate",
    "reason_start_smoothed_skip_rate",
    "is_cold_start_artist",
    "seconds_since_last_skip",
    "skips_last_3m",
    "skips_last_15m",
    "previous_song_skipped",
    "consecutive_listens_streak",
    "platform_android",
    "platform_windows",
    "shuffle_mode",
    "is_session_start",
    "hour_of_day",
    "day_of_week",
    "hour_sin",
    "hour_cos"
]


def load_retrain_status(status_path: Path) -> Dict:
    """Loads the current retrain status flag if present."""
    if status_path.exists():
        try:
            with open(status_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Could not read status file: {e}")
    return {}


def save_retrain_status(status_path: Path, data: Dict):
    """Persists updated retrain status to JSON."""
    status_path.parent.mkdir(parents=True, exist_ok=True)
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def is_already_retrained_today(status: Dict, today_utc: str) -> bool:
    """Checks whether the model was already successfully retrained for today."""
    return (
        status.get("last_retrained_date") == today_utc
        and status.get("status") == "SUCCESS"
    )


def extract_features_from_audit(audit_path: Path, lookup_path: Path) -> pd.DataFrame:
    """
    Extracts structured ML features from shadow_audit.jsonl records.
    Uses feature_store_lookup.json for Bayesian skip rate lookups.
    """
    if not audit_path.exists():
        return pd.DataFrame()

    lookup_data = {"artist_lookup": {}, "song_lookup": {}}
    if lookup_path.exists():
        try:
            with open(lookup_path, "r", encoding="utf-8") as f:
                lookup_data = json.load(f)
        except Exception as e:
            print(f"[WARNING] Could not read feature lookup: {e}")

    artist_lookup = lookup_data.get("artist_lookup", {})
    song_lookup = lookup_data.get("song_lookup", {})

    records = []
    with open(audit_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("status") != "RESOLVED" and rec.get("actual_skipped") is None:
                    continue
                records.append(rec)
            except Exception:
                continue

    if not records:
        return pd.DataFrame()

    rows = []
    skip_timestamps = []
    consecutive_streak = 0
    previous_skipped = 0

    for i, t in enumerate(records):
        played_at_str = t.get("spotify_played_at") or t.get("predicted_at")
        try:
            dt = datetime.fromisoformat(played_at_str.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)

        duration = float(t.get("total_duration_sec") or 180.0)
        actual_skipped = int(t.get("actual_skipped", 0))

        # Session momentum tracking
        current_time_sec = dt.timestamp()
        valid_past_skips = [st for st in skip_timestamps if (current_time_sec - st) <= 900.0 and st < current_time_sec]
        skips_3m = len([st for st in valid_past_skips if (current_time_sec - st) <= 180.0])
        skips_15m = len(valid_past_skips)
        sec_since_skip = (current_time_sec - valid_past_skips[-1]) if valid_past_skips else 10000.0

        if actual_skipped == 1:
            skip_timestamps.append(current_time_sec)
            consecutive_streak = 0
        else:
            consecutive_streak += 1

        hour = dt.hour
        day = dt.weekday()
        artist_key = t.get("artist_name", "").strip().lower()
        song_key = t.get("song_name", "").strip().lower()

        artist_rate = artist_lookup.get(artist_key, 0.104)
        song_rate = song_lookup.get(song_key, artist_rate)
        is_cold_start = 1 if artist_key not in artist_lookup else 0

        row = {
            "artist_smoothed_skip_rate": float(artist_rate),
            "song_smoothed_skip_rate": float(song_rate),
            "genre_smoothed_skip_rate": float(artist_rate),
            "album_smoothed_skip_rate": float(artist_rate),
            "reason_start_smoothed_skip_rate": 0.025,
            "is_cold_start_artist": is_cold_start,
            "seconds_since_last_skip": min(sec_since_skip, 10000.0),
            "skips_last_3m": skips_3m,
            "skips_last_15m": skips_15m,
            "previous_song_skipped": previous_skipped,
            "consecutive_listens_streak": consecutive_streak,
            "platform_android": 0,
            "platform_windows": 1,
            "shuffle_mode": 0,
            "is_session_start": 1 if i == 0 else 0,
            "hour_of_day": hour,
            "day_of_week": day,
            "hour_sin": math.sin(2 * math.pi * hour / 24),
            "hour_cos": math.cos(2 * math.pi * hour / 24),
            "is_skip": actual_skipped,
            "time_stamp": dt
        }
        rows.append(row)
        previous_skipped = actual_skipped

    return pd.DataFrame(rows)


def run_daily_retrain(
    force: bool = False,
    min_samples: int = 50,
    status_path: Path = DEFAULT_STATUS_PATH,
    audit_path: Path = DEFAULT_AUDIT_PATH,
    model_path: Path = DEFAULT_MODEL_PATH,
    lookup_path: Path = DEFAULT_LOOKUP_PATH
) -> bool:
    """
    Main execution loop for daily model retraining.
    Returns True if retraining was successful or cleanly skipped, False on failure.
    """
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    status = load_retrain_status(status_path)

    print("=" * 70)
    print(f"DAILY MODEL RETRAINING ENGINE | UTC DATE: {today_utc}")
    print("=" * 70)

    # 1. State Machine Check: Was model already retrained today?
    if is_already_retrained_today(status, today_utc) and not force:
        print(f"[STATUS: COMPLETED] Model was already retrained successfully today ({today_utc}).")
        print(f"  - Last Retrained UTC : {status.get('last_retrained_utc')}")
        print(f"  - Records Used       : {status.get('records_evaluated')}")
        print(f"  - ROC-AUC Metric     : {status.get('roc_auc')}")
        print(f"No re-execution required. Next daily cycle triggers tomorrow at 00:00 UTC.")
        return True

    print(f"[STATUS: ACTION REQUIRED] Retraining needed for {today_utc}. Commencing pipeline...")

    try:
        # 2. Ingest available audit data
        audit_df = extract_features_from_audit(audit_path, lookup_path)
        print(f"Loaded {len(audit_df):,} resolved records from shadow audit log.")

        if len(audit_df) < min_samples:
            err_msg = f"Insufficient resolved audit records ({len(audit_df)} < {min_samples}). Cannot retrain."
            print(f"[ERROR] {err_msg}")
            save_retrain_status(status_path, {
                "last_retrained_date": status.get("last_retrained_date"),
                "last_attempt_utc": datetime.now(timezone.utc).isoformat(),
                "status": "FAILED",
                "error_message": err_msg
            })
            return False

        # 3. Combine with historical baseline if local DB exists
        # 3. Combine with historical baseline (prefer lightweight Parquet, fallback to SQLite)
        training_frames = []
        if DEFAULT_BASELINE_PARQUET.exists():
            print(f"Loading historical baseline from Parquet: {DEFAULT_BASELINE_PARQUET.name}...")
            hist_df = pd.read_parquet(DEFAULT_BASELINE_PARQUET)
            common_cols = [c for c in FEATURE_COLUMNS + ["is_skip"] if c in hist_df.columns]
            training_frames.append(hist_df[common_cols])
            print(f"Combined with {len(hist_df):,} historical modern records from Parquet.")
        elif DEFAULT_HIST_DB.exists():
            import sqlite3
            conn = sqlite3.connect(DEFAULT_HIST_DB)
            hist_df = pd.read_sql("SELECT * FROM Engineered_Spotify_Portable WHERE year >= 2023", conn)
            conn.close()
            common_cols = [c for c in FEATURE_COLUMNS + ["is_skip"] if c in hist_df.columns]
            training_frames.append(hist_df[common_cols])
            print(f"Combined with {len(hist_df):,} historical modern records from {DEFAULT_HIST_DB.name}.")
        elif DEFAULT_CURR_DB.exists():
            import sqlite3
            conn = sqlite3.connect(DEFAULT_CURR_DB)
            hist_df = pd.read_sql("SELECT * FROM Engineered_Spotify_Portable WHERE year >= 2023 AND time_stamp < '2026-09-24'", conn)
            conn.close()
            common_cols = [c for c in FEATURE_COLUMNS + ["is_skip"] if c in hist_df.columns]
            training_frames.append(hist_df[common_cols])
            print(f"Combined with {len(hist_df):,} historical modern records from {DEFAULT_CURR_DB.name}.")

        training_frames.append(audit_df[FEATURE_COLUMNS + ["is_skip"]])
        combined_df = pd.concat(training_frames, ignore_index=True)
        print(f"Total Combined Training Samples: {len(combined_df):,}")

        # 4. Train Model with Cost-Sensitive Balancing
        X = combined_df[FEATURE_COLUMNS]
        y = combined_df["is_skip"].astype(int)

        pos_count = int((y == 1).sum())
        neg_count = int((y == 0).sum())
        scale_pos_weight = float(neg_count / max(1, pos_count))

        model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.03,
            scale_pos_weight=scale_pos_weight,
            min_child_weight=5,
            subsample=0.80,
            colsample_bytree=0.65,
            reg_alpha=0.1,
            reg_lambda=5.0,
            random_state=42,
            tree_method="hist",
            device="cpu"
        )
        print("Fitting XGBoost Classifier on CPU...")
        model.fit(X, y)

        # 5. Model Evaluation & Threshold Optimization
        probs = model.predict_proba(X)[:, 1]
        auc_score = float(roc_auc_score(y, probs))
        precisions, recalls, thresholds = precision_recall_curve(y, probs)

        target_precision = 0.80
        safe_mask = precisions >= target_precision
        if np.any(safe_mask):
            best_idx = np.where(safe_mask)[0][np.argmax(recalls[safe_mask])]
            best_threshold = float(thresholds[best_idx]) if best_idx < len(thresholds) else 0.5
            guaranteed_prec = float(precisions[best_idx])
            safe_recall = float(recalls[best_idx])
        else:
            f1 = 2 * (precisions * recalls) / np.maximum(precisions + recalls, 1e-9)
            best_idx = np.argmax(f1)
            best_threshold = float(thresholds[best_idx]) if best_idx < len(thresholds) else 0.5
            guaranteed_prec = float(precisions[best_idx])
            safe_recall = float(recalls[best_idx])

        print("\n--- RETRAINING EVALUATION METRICS ---")
        print(f"ROC-AUC Score       : {auc_score:.4f}")
        print(f"Optimal Threshold   : {best_threshold:.4f}")
        print(f"Achieved Precision  : {guaranteed_prec:.4f}")
        print(f"Achieved Recall     : {safe_recall:.4f}")

        # 6. Sanity Gate: Verify model validity before updating artifact
        if auc_score < 0.60:
            raise ValueError(f"Retrained model failed sanity gate: ROC-AUC ({auc_score:.4f}) is below 0.60 baseline.")

        # 7. Persist Updated Model Artifact
        payload = {
            "model": model,
            "features": FEATURE_COLUMNS,
            "best_threshold": best_threshold,
            "target_precision": target_precision,
            "target": "is_skip",
            "last_retrained_utc": datetime.now(timezone.utc).isoformat(),
            "samples_count": len(combined_df)
        }
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(payload, str(model_path))
        file_size_kb = round(os.path.getsize(model_path) / 1024, 2)
        print(f"[ARTIFACT SAVED] Saved retrained model to: {model_path} ({file_size_kb} KB)")

        # 8. Update Retrain Status Flag to SUCCESS
        status_payload = {
            "last_retrained_date": today_utc,
            "last_retrained_utc": datetime.now(timezone.utc).isoformat(),
            "status": "SUCCESS",
            "records_evaluated": len(combined_df),
            "roc_auc": round(auc_score, 4),
            "best_threshold": round(best_threshold, 4),
            "precision": round(guaranteed_prec, 4),
            "recall": round(safe_recall, 4),
            "model_size_kb": file_size_kb
        }
        save_retrain_status(status_path, status_payload)
        print(f"[FLAG UPDATED] Marked {status_path} as SUCCESS for date {today_utc}.")
        print("Daily retraining cycle completed successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] Retraining failed with exception: {e}")
        save_retrain_status(status_path, {
            "last_retrained_date": status.get("last_retrained_date"),
            "last_attempt_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FAILED",
            "error_message": str(e)
        })
        return False


def main():
    parser = argparse.ArgumentParser(description="Daily Automated Model Retraining & Status Checker.")
    parser.add_argument("--force", action="store_true", help="Force retraining execution regardless of today's status flag")
    parser.add_argument("--min-samples", type=int, default=50, help="Minimum resolved tracks required to retrain (default: 50)")
    parser.add_argument("--status-path", type=str, default=str(DEFAULT_STATUS_PATH), help="Path to retrain status JSON flag")
    parser.add_argument("--audit-path", type=str, default=str(DEFAULT_AUDIT_PATH), help="Path to shadow audit JSONL log")
    parser.add_argument("--model-path", type=str, default=str(DEFAULT_MODEL_PATH), help="Path to model artifact .pkl")
    parser.add_argument("--lookup-path", type=str, default=str(DEFAULT_LOOKUP_PATH), help="Path to feature store lookup JSON")

    args = parser.parse_args()

    success = run_daily_retrain(
        force=args.force,
        min_samples=args.min_samples,
        status_path=Path(args.status_path),
        audit_path=Path(args.audit_path),
        model_path=Path(args.model_path),
        lookup_path=Path(args.lookup_path)
    )

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

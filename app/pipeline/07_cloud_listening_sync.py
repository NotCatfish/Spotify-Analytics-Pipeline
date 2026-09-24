"""
Headless Spotify Cloud Listening Sync Engine & Automated Model Audit
=====================================================================
Designed for 1-hour recurring cron execution (GitHub Actions / background daemons).
Polls Spotify's Recently Played endpoint, reconstructs session momentum chronologically,
runs XGBoost skip predictions, and logs ground truth outcomes into the shadow audit database.

Key Features:
- Headless Auth: Uses SPOTIPY_REFRESH_TOKEN (from GitHub Secrets or local cache) with zero browser interaction.
- Chronological Session Replay: Accurately reconstructs skips_last_3m, seconds_since_last_skip,
  and detects idle pauses (>10m) to reset listening sessions.
- Dynamic Ground Truth Resolution: Infers actual skips based on elapsed time between played tracks.
- Resilient Model Inference: Loads XGBoost model on CPU, with graceful degraded fallback if models are absent.
- Idempotent SQLite Ingestion: De-duplicates tracks using unique Spotify played_at timestamps.
"""

import os
import sys
import math
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Dynamic Project Root Discovery (Repository Standard)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from path_utils import resolve_path

import requests
import spotipy
import pandas as pd

# Path Definitions
DB_PATH = resolve_path("data/audit/production_audit.db")
FEATURE_STORE_PATH = resolve_path("data/processed/Engineered_Spotify_Portable.db")
MODEL_PATH = resolve_path("models/spotify_skip_predictor_xgb.pkl")
CACHE_PATH = resolve_path("app/api/.spotify_cache")


def get_headless_spotify_client() -> spotipy.Spotify:
    """
    Authenticates headlessly using refresh_token without requiring a browser or web server.
    Checks environment variables first (GitHub Secrets), then falls back to local cache file.
    """
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIPY_REFRESH_TOKEN")

    # Fallback to local cache if environment secret is not set
    if not refresh_token and CACHE_PATH.exists():
        import json
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                refresh_token = cache_data.get("refresh_token")
        except Exception as e:
            print(f"[WARNING] Could not read local token cache: {e}")

    if not client_id or not client_secret:
        # Load from .env if present
        from dotenv import load_dotenv
        env_file = resolve_path(".env")
        if env_file.exists():
            load_dotenv(env_file)
            client_id = os.getenv("SPOTIPY_CLIENT_ID")
            client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
            if not refresh_token:
                refresh_token = os.getenv("SPOTIPY_REFRESH_TOKEN")

    if not refresh_token:
        raise ValueError(
            "Missing SPOTIPY_REFRESH_TOKEN. Please set it as an environment variable or authenticate locally first."
        )

    # Direct token refresh via Spotify Web API
    token_url = "https://accounts.spotify.com/api/token"
    resp = requests.post(
        token_url,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=10.0
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Spotify token refresh failed ({resp.status_code}): {resp.text}")

    token_data = resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise RuntimeError("No access_token returned in Spotify refresh response.")

    return spotipy.Spotify(auth=access_token, requests_timeout=10, retries=2)


def fetch_recently_played_tracks(sp: spotipy.Spotify, limit: int = 50, hours: int = 1) -> List[Dict]:
    """
    Fetches up to 50 recently played tracks and filters to tracks played within the specified time window.
    Returns tracks in ASCENDING chronological order (earliest to latest).
    """
    res = sp.current_user_recently_played(limit=limit)
    items = res.get("items", [])
    if not items:
        return []

    cutoff_dt = datetime.now(timezone.utc) - timedelta(hours=hours)

    filtered = []
    for item in items:
        played_at_str = item.get("played_at")
        if not played_at_str:
            continue

        # Parse ISO 8601 timestamp (e.g. 2026-09-24T15:30:00.000Z)
        try:
            dt = datetime.fromisoformat(played_at_str.replace("Z", "+00:00"))
        except Exception:
            continue

        # Include if within time window or if hours=0 (fetch all available)
        if hours == 0 or dt >= cutoff_dt:
            track = item.get("track", {})
            artists = [a.get("name") for a in track.get("artists", []) if a.get("name")]
            artist_name = artists[0] if artists else "Unknown Artist"
            song_name = track.get("name", "Unknown Track")
            album_name = track.get("album", {}).get("name", "Unknown Album")
            duration_ms = track.get("duration_ms", 180000)
            track_id = track.get("id", f"{song_name}::{artist_name}")

            filtered.append({
                "played_at_str": played_at_str,
                "played_at_dt": dt,
                "track_id": track_id,
                "song_name": song_name,
                "artist_name": artist_name,
                "album_name": album_name,
                "duration_sec": round(duration_ms / 1000.0, 1),
            })

    # Spotify returns most recent first -> reverse to get chronological sequence
    filtered.reverse()
    return filtered


def load_model_artifacts() -> Dict:
    """
    Loads XGBoost model and Feature Store lookup dictionaries.
    Gracefully degrades if files are absent in CI/CD environments.
    """
    artifacts = {
        "is_ready": False,
        "model": None,
        "features": [],
        "threshold": 0.45,
        "artist_lookup": {},
        "song_lookup": {}
    }

    if not MODEL_PATH.exists():
        print(f"[INFO] Model file not found at {MODEL_PATH}. Running in degraded telemetry mode.")
        return artifacts

    try:
        import joblib
        import __main__
        # Inject dummy focal_loss_objective to resolve training pickle dependencies
        def focal_loss_objective(y_true, y_pred):
            pass
        __main__.focal_loss_objective = focal_loss_objective

        payload = joblib.load(MODEL_PATH)
        model = payload["model"]
        try:
            model.set_params(device="cpu")
        except Exception:
            pass

        artifacts["model"] = model
        artifacts["features"] = payload.get("features", [])
        artifacts["threshold"] = float(payload.get("best_threshold", 0.45))
        artifacts["is_ready"] = True
    except Exception as e:
        print(f"[WARNING] Failed to load XGBoost model: {e}")

    # Load feature store lookups if SQLite DB is available
    if FEATURE_STORE_PATH.exists():
        try:
            conn = sqlite3.connect(FEATURE_STORE_PATH)
            artist_df = pd.read_sql("SELECT artist_name, artist_smoothed_skip_rate FROM Engineered_Spotify_Portable ORDER BY time_stamp DESC", conn)
            artifacts["artist_lookup"] = {
                name.lower().strip(): rate for name, rate in artist_df.drop_duplicates("artist_name").values
            }
            song_df = pd.read_sql("SELECT song_name, song_smoothed_skip_rate FROM Engineered_Spotify_Portable ORDER BY time_stamp DESC", conn)
            artifacts["song_lookup"] = {
                name.lower().strip(): rate for name, rate in song_df.drop_duplicates("song_name").values
            }
            conn.close()
        except Exception as e:
            print(f"[WARNING] Could not load feature store lookups: {e}")

    return artifacts


def replay_session_and_predict(tracks: List[Dict], artifacts: Dict) -> List[Dict]:
    """
    Replays the listening history chronologically to reconstruct session momentum
    (skips_last_3m, seconds_since_last_skip, session idle gaps) and evaluate predictions.
    """
    if not tracks:
        return []

    now_utc = datetime.now(timezone.utc)
    skip_timestamps = []
    consecutive_streak = 0
    previous_skipped = False
    reason_start = "trackdone"

    evaluated_records = []

    for i, t in enumerate(tracks):
        dt = t["played_at_dt"]
        duration = t["duration_sec"]
        cutoff = max(10.0, duration - 10.0) if duration > 15.0 else 30.0

        # Determine elapsed time to next song
        if i + 1 < len(tracks):
            next_dt = tracks[i + 1]["played_at_dt"]
            delta_sec = max(0.0, (next_dt - dt).total_seconds())
        else:
            # For the most recent song, compare against current time
            delta_sec = max(0.0, (now_utc - dt).total_seconds())

        # Check for idle pause (> 10 minutes between songs resets session)
        is_idle_break = (i > 0 and delta_sec > 600.0)
        if is_idle_break:
            skip_timestamps.clear()
            consecutive_streak = 0
            previous_skipped = False
            reason_start = "trackdone"

        # 1. Calculate past session momentum (Strictly PAST events, ZERO lookahead)
        current_time_sec = dt.timestamp()
        valid_past_skips = [st for st in skip_timestamps if (current_time_sec - st) <= 900.0 and st < current_time_sec]
        skips_3m = len([st for st in valid_past_skips if (current_time_sec - st) <= 180.0])
        skips_15m = len(valid_past_skips)
        sec_since_skip = (current_time_sec - valid_past_skips[-1]) if valid_past_skips else 10000.0

        # 2. Feature preparation for XGBoost (Only uses information available at song start)
        hour = dt.hour
        day = dt.weekday()
        hour_sin = math.sin(2 * math.pi * hour / 24)
        hour_cos = math.cos(2 * math.pi * hour / 24)

        reason_map = {"trackdone": 0.025, "clickrow": 0.120, "fwdbtn": 0.604, "backbtn": 0.400, "playbtn": 0.050}
        reason_risk = reason_map.get(reason_start, 0.104)

        artist_key = t["artist_name"].strip().lower()
        song_key = t["song_name"].strip().lower()
        is_cold_start = 1 if artist_key not in artifacts["artist_lookup"] else 0
        artist_rate = artifacts["artist_lookup"].get(artist_key, 0.104)
        song_rate = artifacts["song_lookup"].get(song_key, artist_rate)

        # 19 Model Input Features (Completely blind to whether this song will be skipped)
        feature_dict = {
            "artist_smoothed_skip_rate": float(artist_rate),
            "song_smoothed_skip_rate": float(song_rate),
            "genre_smoothed_skip_rate": float(artist_rate),
            "album_smoothed_skip_rate": float(artist_rate),
            "is_cold_start_artist": is_cold_start,
            "reason_start_smoothed_skip_rate": reason_risk,
            "platform_android": 0,
            "platform_windows": 1,
            "hour_of_day": hour,
            "day_of_week": day,
            "hour_sin": hour_sin,
            "hour_cos": hour_cos,
            "seconds_since_last_skip": min(sec_since_skip, 10000.0),
            "skips_last_3m": skips_3m,
            "skips_last_15m": skips_15m,
            "previous_song_skipped": int(previous_skipped),
            "consecutive_listens_streak": consecutive_streak,
            "shuffle_mode": 0,
            "is_session_start": 1 if consecutive_streak == 0 else 0
        }

        # 3. Model Skip Prediction (Locked in BEFORE knowing the outcome)
        if artifacts["is_ready"]:
            try:
                input_df = pd.DataFrame([feature_dict])[artifacts["features"]]
                prob = float(artifacts["model"].predict_proba(input_df)[0][1])
            except Exception:
                prob = 0.35
        else:
            prob = 0.35

        threshold = artifacts["threshold"]
        pred_skip_int = 1 if prob >= threshold else 0
        risk_tier = "CRITICAL" if prob >= threshold else ("LOW" if prob < 0.35 else "MODERATE")

        # 4. Ground Truth Evaluation (Teacher grading: what actually happened later?)
        if i + 1 < len(tracks):
            was_skipped = (delta_sec < cutoff)
            actual_played_sec = round(min(delta_sec, duration), 1)
        else:
            if delta_sec >= cutoff:
                was_skipped = False
                actual_played_sec = duration
            else:
                was_skipped = False
                actual_played_sec = duration

        actual_skip_int = 1 if was_skipped else 0

        # Confusion Matrix Resolution
        if pred_skip_int == 1 and actual_skip_int == 1:
            eval_result = "TRUE_POSITIVE"
        elif pred_skip_int == 0 and actual_skip_int == 0:
            eval_result = "TRUE_NEGATIVE"
        elif pred_skip_int == 1 and actual_skip_int == 0:
            eval_result = "FALSE_POSITIVE"
        else:
            eval_result = "FALSE_NEGATIVE"

        # CDN Bandwidth Saving Formula
        mb_saved = 1.00 if (actual_skip_int == 1 and pred_skip_int == 1 and actual_played_sec < 45.0) else 0.00

        # 5. Advance session state for FUTURE songs
        if was_skipped:
            skip_timestamps.append(current_time_sec)
            previous_skipped = True
            reason_start = "fwdbtn"
            consecutive_streak = 0
        else:
            previous_skipped = False
            reason_start = "trackdone"
            consecutive_streak += 1

        evaluated_records.append({
            "spotify_played_at": t["played_at_str"],
            "predicted_at": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": (dt + timedelta(seconds=actual_played_sec)).strftime("%Y-%m-%d %H:%M:%S"),
            "track_id": t["track_id"],
            "song_name": t["song_name"],
            "artist_name": t["artist_name"],
            "album_name": t["album_name"],
            "predicted_prob": round(prob, 4),
            "predicted_skip": pred_skip_int,
            "risk_tier": risk_tier,
            "actual_played_sec": actual_played_sec,
            "total_duration_sec": duration,
            "actual_skipped": actual_skip_int,
            "evaluation_result": eval_result,
            "cdn_mb_saved": mb_saved,
            "status": "RESOLVED"
        })

    return evaluated_records


def init_and_migrate_db(conn: sqlite3.Connection):
    """Initializes schema and adds spotify_played_at index for idempotent syncing."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shadow_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            predicted_at TIMESTAMP NOT NULL,
            resolved_at TIMESTAMP,
            track_id TEXT NOT NULL,
            song_name TEXT NOT NULL,
            artist_name TEXT NOT NULL,
            album_name TEXT NOT NULL,
            predicted_prob REAL NOT NULL,
            predicted_skip INTEGER NOT NULL,
            risk_tier TEXT NOT NULL,
            actual_played_sec REAL,
            total_duration_sec REAL,
            actual_skipped INTEGER,
            evaluation_result TEXT,
            cdn_mb_saved REAL DEFAULT 0.0,
            status TEXT DEFAULT 'PENDING'
        )
    """)
    # Add missing columns if migrating an older database schema
    cursor.execute("PRAGMA table_info(shadow_audit)")
    columns = [col[1] for col in cursor.fetchall()]
    if "album_name" not in columns:
        cursor.execute("ALTER TABLE shadow_audit ADD COLUMN album_name TEXT")
    if "spotify_played_at" not in columns:
        cursor.execute("ALTER TABLE shadow_audit ADD COLUMN spotify_played_at TEXT")

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_shadow_played_at ON shadow_audit(spotify_played_at)")
    conn.commit()


JSONL_PATH = resolve_path("data/audit/shadow_audit.jsonl")


def save_evaluated_records_to_db(records: List[Dict]) -> Tuple[int, int]:
    """
    Saves records to SQLite shadow_audit table, ignoring duplicate played_at timestamps.
    Guarantees zero duplicates on stateless GitHub runners by checking existing timestamps
    in data/audit/shadow_audit.jsonl.
    Returns (inserted_count, skipped_duplicates_count).
    """
    if not records:
        return 0, 0

    # 1. Load existing timestamps from shadow_audit.jsonl (stateless runner guard)
    existing_timestamps = set()
    if JSONL_PATH.exists():
        import json
        try:
            with open(JSONL_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str:
                        try:
                            obj = json.loads(line_str)
                            if "spotify_played_at" in obj:
                                existing_timestamps.add(obj["spotify_played_at"])
                        except Exception:
                            pass
        except Exception as e:
            print(f"[WARNING] Could not read existing timestamps from JSONL: {e}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    init_and_migrate_db(conn)
    cursor = conn.cursor()

    inserted = 0
    duplicates = 0
    new_records = []

    for r in records:
        # Prevent duplicates across overlapping cron runs
        if r["spotify_played_at"] in existing_timestamps:
            duplicates += 1
            continue
        try:
            cursor.execute("""
                INSERT INTO shadow_audit (
                    spotify_played_at, predicted_at, resolved_at, track_id,
                    song_name, artist_name, album_name, predicted_prob,
                    predicted_skip, risk_tier, actual_played_sec, total_duration_sec,
                    actual_skipped, evaluation_result, cdn_mb_saved, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["spotify_played_at"], r["predicted_at"], r["resolved_at"], r["track_id"],
                r["song_name"], r["artist_name"], r["album_name"], r["predicted_prob"],
                r["predicted_skip"], r["risk_tier"], r["actual_played_sec"], r["total_duration_sec"],
                r["actual_skipped"], r["evaluation_result"], r["cdn_mb_saved"], r["status"]
            ))
            inserted += 1
            new_records.append(r)
        except sqlite3.IntegrityError:
            duplicates += 1

    conn.commit()
    conn.close()

    # Append new unique records to shadow_audit.jsonl
    if new_records:
        import json
        JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(JSONL_PATH, "a", encoding="utf-8") as f:
            for rec in new_records:
                f.write(json.dumps(rec) + "\n")

    return inserted, duplicates


def get_overall_audit_metrics() -> Dict:
    """Computes total online shadow evaluation confusion matrix and bandwidth savings."""
    if not DB_PATH.exists():
        return {}

    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    cursor.execute("SELECT evaluation_result, cdn_mb_saved FROM shadow_audit WHERE status = 'RESOLVED'")
    rows = cursor.fetchall()
    conn.close()

    total = len(rows)
    tp = sum(1 for r in rows if r[0] == "TRUE_POSITIVE")
    tn = sum(1 for r in rows if r[0] == "TRUE_NEGATIVE")
    fp = sum(1 for r in rows if r[0] == "FALSE_POSITIVE")
    fn = sum(1 for r in rows if r[0] == "FALSE_NEGATIVE")
    mb_saved = round(sum(r[1] for r in rows), 2)

    precision = round((tp / (tp + fp)) * 100, 1) if (tp + fp) > 0 else 0.0
    recall = round((tp / (tp + fn)) * 100, 1) if (tp + fn) > 0 else 0.0
    accuracy = round(((tp + tn) / total) * 100, 1) if total > 0 else 0.0

    return {
        "total": total,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "mb_saved": mb_saved
    }


def main():
    parser = argparse.ArgumentParser(description="Headless Spotify Cloud Listening Sync Engine")
    parser.add_argument("--hours", type=int, default=1, help="Fetch tracks played in past N hours (0 for all recent)")
    parser.add_argument("--limit", type=int, default=50, help="Max tracks to fetch from Spotify API (1-50)")
    args = parser.parse_args()

    print("=" * 76)
    print("[*] SPOTIFY CLOUD LISTENING SYNC & SHADOW EVALUATION ENGINE")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Target: Past {args.hours} hour(s)")
    print("=" * 76)

    try:
        sp = get_headless_spotify_client()
        print("[+] Headless Spotify authentication successful.")
    except Exception as e:
        print(f"[FATAL] Authentication failed: {e}")
        sys.exit(1)

    try:
        raw_tracks = fetch_recently_played_tracks(sp, limit=args.limit, hours=args.hours)
        print(f"[+] Retrieved {len(raw_tracks)} track(s) from Spotify recently-played history.")
    except Exception as e:
        print(f"[ERROR] Failed to fetch Spotify playback history: {e}")
        sys.exit(1)

    if not raw_tracks:
        print("[INFO] No playback detected in the specified time window. Exiting cleanly.")
        sys.exit(0)

    artifacts = load_model_artifacts()
    evaluated = replay_session_and_predict(raw_tracks, artifacts)
    inserted, duplicates = save_evaluated_records_to_db(evaluated)

    print(f"[+] Database Sync: {inserted} new record(s) inserted, {duplicates} duplicate(s) skipped.")

    # Print summary table of processed tracks
    print("\n--- SYNCED TRACKS EVALUATION ---")
    for r in evaluated:
        status_sym = "SKIP" if r["actual_skipped"] == 1 else "PLAY"
        eval_tag = f"[{r['evaluation_result']}]"
        print(f"  {r['predicted_at']} | {status_sym:5} | {r['song_name'][:25]:25} by {r['artist_name'][:20]:20} | Prob: {r['predicted_prob']*100:4.1f}% | {eval_tag}")

    # Print cumulative audit metrics
    metrics = get_overall_audit_metrics()
    if metrics:
        print("\n--- CUMULATIVE SHADOW AUDIT SCOREBOARD ---")
        print(f"  Total Evaluated: {metrics['total']} tracks")
        print(f"  Confusion Matrix: TP: {metrics['tp']} | TN: {metrics['tn']} | FP: {metrics['fp']} | FN: {metrics['fn']}")
        print(f"  Empirical Precision: {metrics['precision']}% | Recall: {metrics['recall']}% | Accuracy: {metrics['accuracy']}%")
        print(f"  Conserved CDN Bandwidth: {metrics['mb_saved']} MB")
    print("=" * 76)


if __name__ == "__main__":
    main()

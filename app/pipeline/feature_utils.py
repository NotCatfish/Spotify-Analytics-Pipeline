"""
Unified Feature Extraction & Causal Session Momentum Engine
===========================================================
Shared utility ensuring zero train-serve feature skew between
live cloud listening sync (`07_cloud_listening_sync.py`) and
daily model retraining (`08_daily_model_retrain.py`).
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any

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

REASON_MAP = {
    "trackdone": 0.025,
    "clickrow": 0.120,
    "fwdbtn": 0.604,
    "backbtn": 0.400,
    "playbtn": 0.050
}


def build_single_feature_vector(
    track_start_dt: datetime,
    artist_name: str,
    song_name: str,
    artist_lookup: Dict[str, float],
    song_lookup: Dict[str, float],
    reason_start: str,
    previous_skipped: bool,
    consecutive_streak: int,
    is_idle_break: bool,
    skip_timestamps: List[float],
    track_start_sec: float,
    platform_android: int = 0,
    platform_windows: int = 1,
    shuffle_mode: int = 0,
    default_rate: float = 0.104
) -> Dict[str, Any]:
    """
    Constructs an identical 19-dimensional feature dictionary for XGBoost.
    Guarantees that train and inference features match with zero skew.
    """
    # 1. Temporal signals
    hour = track_start_dt.hour
    day = track_start_dt.weekday()
    hour_sin = math.sin(2 * math.pi * hour / 24)
    hour_cos = math.cos(2 * math.pi * hour / 24)

    # 2. Reason start risk
    reason_risk = REASON_MAP.get(reason_start, default_rate)

    # 3. Content Bayesian skip rates
    artist_key = artist_name.strip().lower()
    song_key = song_name.strip().lower()
    is_cold_start = 1 if artist_key not in artist_lookup else 0
    artist_rate = artist_lookup.get(artist_key, default_rate)
    song_rate = song_lookup.get(song_key, artist_rate)

    # 4. Strictly causal session momentum (relative to track_start_sec)
    valid_past_skips = [
        st for st in skip_timestamps
        if (track_start_sec - st) <= 900.0 and st <= track_start_sec
    ]
    skips_3m = len([st for st in valid_past_skips if (track_start_sec - st) <= 180.0])
    skips_15m = len(valid_past_skips)
    sec_since_skip = (track_start_sec - valid_past_skips[-1]) if valid_past_skips else 10000.0

    return {
        "artist_smoothed_skip_rate": float(artist_rate),
        "song_smoothed_skip_rate": float(song_rate),
        "genre_smoothed_skip_rate": float(artist_rate),
        "album_smoothed_skip_rate": float(artist_rate),
        "is_cold_start_artist": is_cold_start,
        "reason_start_smoothed_skip_rate": float(reason_risk),
        "platform_android": int(platform_android),
        "platform_windows": int(platform_windows),
        "hour_of_day": int(hour),
        "day_of_week": int(day),
        "hour_sin": float(hour_sin),
        "hour_cos": float(hour_cos),
        "seconds_since_last_skip": float(min(sec_since_skip, 10000.0)),
        "skips_last_3m": int(skips_3m),
        "skips_last_15m": int(skips_15m),
        "previous_song_skipped": int(previous_skipped),
        "consecutive_listens_streak": int(consecutive_streak),
        "shuffle_mode": int(shuffle_mode),
        "is_session_start": 1 if (is_idle_break or consecutive_streak == 0) else 0
    }

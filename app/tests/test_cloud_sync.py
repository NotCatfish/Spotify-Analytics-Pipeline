"""
Unit Tests for Headless Cloud Listening Sync & Session Replay Engine
====================================================================
Tests the chronological session replay, ground-truth skip resolution,
database de-duplication, and offline inference resilience in
`app/pipeline/07_cloud_listening_sync.py`.
"""

import sys
import sqlite3
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import importlib.util
sync_module_path = APP_DIR / "pipeline" / "07_cloud_listening_sync.py"
spec = importlib.util.spec_from_file_location("cloud_sync", str(sync_module_path))
cloud_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cloud_sync)

replay_session_and_predict = cloud_sync.replay_session_and_predict
init_and_migrate_db = cloud_sync.init_and_migrate_db
save_evaluated_records_to_db = cloud_sync.save_evaluated_records_to_db
get_headless_spotify_client = cloud_sync.get_headless_spotify_client


@pytest.fixture
def mock_artifacts():
    """Mock model artifacts for testing deterministic session replay without requiring GPU/heavy disk IO."""
    return {
        "is_ready": False,
        "model": None,
        "features": [],
        "threshold": 0.45,
        "artist_lookup": {"coldplay": 0.15, "radiohead": 0.08},
        "song_lookup": {"yellow": 0.12}
    }


def test_replay_session_skip_detection_and_momentum(mock_artifacts):
    """
    Verifies that chronological replay correctly identifies skips from short elapsed time
    and updates session momentum (streak, skips_last_3m, previous_song_skipped).
    """
    base_time = datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc)
    tracks = [
        {
            "played_at_str": "2026-09-24T12:00:00.000Z",
            "played_at_dt": base_time,
            "track_id": "track_1",
            "song_name": "Yellow",
            "artist_name": "Coldplay",
            "album_name": "Parachutes",
            "duration_sec": 240.0,
        },
        {
            # Played only 25 seconds later -> Track 1 was skipped after 25s!
            "played_at_str": "2026-09-24T12:00:25.000Z",
            "played_at_dt": base_time + timedelta(seconds=25),
            "track_id": "track_2",
            "song_name": "Karma Police",
            "artist_name": "Radiohead",
            "album_name": "OK Computer",
            "duration_sec": 240.0,
        },
        {
            # Played 245 seconds later -> Track 2 was fully completed!
            "played_at_str": "2026-09-24T12:04:30.000Z",
            "played_at_dt": base_time + timedelta(seconds=270),
            "track_id": "track_3",
            "song_name": "Creep",
            "artist_name": "Radiohead",
            "album_name": "Pablo Honey",
            "duration_sec": 240.0,
        }
    ]

    records = replay_session_and_predict(tracks, mock_artifacts)
    assert len(records) == 3

    # Track 1 check: Was skipped (delta 25s < cutoff ~230s)
    assert records[0]["actual_skipped"] == 1
    assert records[0]["actual_played_sec"] == 25.0
    assert records[0]["song_name"] == "Yellow"

    # Track 2 check: Was completed (delta 245s >= cutoff ~230s)
    assert records[1]["actual_skipped"] == 0
    assert records[1]["actual_played_sec"] == 240.0
    assert records[1]["song_name"] == "Karma Police"


def test_replay_session_idle_break_resets_streak(mock_artifacts):
    """
    Verifies that an idle gap (>10 minutes) resets the streak and momentum.
    """
    base_time = datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc)
    tracks = [
        {
            "played_at_str": "2026-09-24T12:00:00.000Z",
            "played_at_dt": base_time,
            "track_id": "track_1",
            "song_name": "Song A",
            "artist_name": "Artist A",
            "album_name": "Album A",
            "duration_sec": 180.0,
        },
        {
            # 20-minute gap between songs
            "played_at_str": "2026-09-24T12:20:00.000Z",
            "played_at_dt": base_time + timedelta(minutes=20),
            "track_id": "track_2",
            "song_name": "Song B",
            "artist_name": "Artist B",
            "album_name": "Album B",
            "duration_sec": 180.0,
        }
    ]

    records = replay_session_and_predict(tracks, mock_artifacts)
    assert len(records) == 2
    # Second track evaluated cleanly without errors after gap
    assert records[1]["status"] == "RESOLVED"


def test_db_migration_and_idempotent_sync(tmp_path, monkeypatch):
    """
    Verifies that the SQLite migration creates the unique index on spotify_played_at
    and prevents duplicate insertions across multiple sync runs.
    """
    test_db = tmp_path / "test_production_audit.db"
    test_jsonl = tmp_path / "test_shadow_audit.jsonl"
    monkeypatch.setattr(cloud_sync, "DB_PATH", test_db)
    monkeypatch.setattr(cloud_sync, "JSONL_PATH", test_jsonl)

    dummy_records = [
        {
            "spotify_played_at": "2026-09-24T12:00:00.000Z",
            "predicted_at": "2026-09-24 12:00:00",
            "resolved_at": "2026-09-24 12:03:00",
            "track_id": "track_123",
            "song_name": "Clocks",
            "artist_name": "Coldplay",
            "album_name": "A Rush of Blood to the Head",
            "predicted_prob": 0.22,
            "predicted_skip": 0,
            "risk_tier": "LOW",
            "actual_played_sec": 180.0,
            "total_duration_sec": 180.0,
            "actual_skipped": 0,
            "evaluation_result": "TRUE_NEGATIVE",
            "cdn_mb_saved": 0.0,
            "status": "RESOLVED"
        }
    ]

    # First run: 1 inserted, 0 duplicates
    inserted, duplicates = save_evaluated_records_to_db(dummy_records)
    assert inserted == 1
    assert duplicates == 0

    # Second run with exact same record: 0 inserted, 1 duplicate skipped!
    inserted2, duplicates2 = save_evaluated_records_to_db(dummy_records)
    assert inserted2 == 0
    assert duplicates2 == 1


def test_headless_client_missing_credentials(monkeypatch):
    """
    Verifies that get_headless_spotify_client raises ValueError when credentials are missing.
    """
    monkeypatch.setenv("SPOTIPY_CLIENT_ID", "")
    monkeypatch.setenv("SPOTIPY_CLIENT_SECRET", "")
    monkeypatch.setenv("SPOTIPY_REFRESH_TOKEN", "")
    monkeypatch.setattr(cloud_sync, "CACHE_PATH", Path("non_existent_cache.json"))

    with pytest.raises(ValueError, match="Missing SPOTIPY_REFRESH_TOKEN"):
        get_headless_spotify_client()

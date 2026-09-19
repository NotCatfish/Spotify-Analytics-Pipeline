import pytest
from unittest.mock import patch


def test_healthcheck_endpoint(api_client):
    """
    Verifies that the GET /health endpoint returns HTTP 200 and healthy payload.
    """
    response = api_client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "threshold" in data
    assert "features_count" in data
    assert data["features_count"] > 0



def test_predict_skip_endpoint_success(api_client):
    """
    Verifies that POST /predict-skip returns valid SkipPredictionResponse JSON.
    """
    payload = {
        "song_name": "Yellow",
        "artist_name": "Coldplay",
        "album_name": "Parachutes",
        "genre": "rock",
        "platform": "windows",
        "shuffle_mode": False,
        "reason_start": "trackdone",
        "skips_last_3m": 0,
        "skips_last_15m": 0,
        "seconds_since_last_skip": 1000.0,
        "consecutive_listens_streak": 2,
        "previous_song_skipped": False
    }
    
    response = api_client.post("/predict-skip", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert "song_name" in data
    assert data["song_name"] == "Yellow"
    assert "skip_probability" in data
    assert 0.0 <= data["skip_probability"] <= 1.0
    assert "is_skip_predicted" in data
    assert isinstance(data["is_skip_predicted"], bool)
    assert "risk_tier" in data
    assert "actions" in data
    assert "cdn_buffer_policy" in data["actions"]
    assert "recommender_policy" in data["actions"]


def test_predict_skip_validation_error(api_client):
    """
    Verifies that POST /predict-skip rejects invalid inputs (e.g. negative skips count) with HTTP 422.
    """
    invalid_payload = {
        "song_name": "Test",
        "artist_name": "Test Artist",
        "skips_last_3m": -5  # Violation: Field(ge=0)
    }
    
    response = api_client.post("/predict-skip", json=invalid_payload)
    assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"


@patch("main.get_live_spotify_data")
@patch("main.get_lastfm_tags")
def test_predict_live_queue_endpoint_mocked(mock_tags, mock_spotify, api_client):
    """
    Verifies GET /predict/live-queue with mocked Spotify/Last.fm network responses for fast, deterministic unit testing.
    """
    mock_spotify.return_value = {
        "status": "ACTIVE",
        "device": {"type": "windows"},
        "shuffle_mode": False,
        "current_track": {"song_name": "Yellow", "artist_name": "Coldplay", "album_name": "Parachutes"},
        "next_queued_tracks": [
            {"song_name": "Karma Police", "artist_name": "Radiohead", "album_name": "OK Computer"},
            {"song_name": "Fix You", "artist_name": "Coldplay", "album_name": "X&Y"},
        ]
    }
    mock_tags.return_value = ["alternative", "rock"]
    
    response = api_client.get("/predict/live-queue?queue_limit=2")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ACTIVE"
    assert "upcoming_queue_forecast" in data or "predictions" in data
    predictions = data.get("upcoming_queue_forecast", data.get("predictions", []))
    assert len(predictions) == 2
    assert predictions[0]["song_name"] == "Karma Police"
    assert 0.0 <= predictions[0]["skip_probability"] <= 1.0

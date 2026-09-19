import pytest
import pandas as pd
import numpy as np


def test_model_artifact_structure(model_payload):
    """
    Verifies that the serialized model artifact dictionary contains all required components.
    """
    assert "model" in model_payload, "Missing 'model' key in payload"
    assert "features" in model_payload, "Missing 'features' key in payload"
    assert "best_threshold" in model_payload, "Missing 'best_threshold' key in payload"
    
    assert isinstance(model_payload["features"], list)
    assert len(model_payload["features"]) > 0, f"Expected non-empty features list, got {len(model_payload['features'])}"
    assert isinstance(model_payload["best_threshold"], (float, int))



def test_model_inference_probability_bounds(model_payload):
    """
    Verifies that the model outputs valid probabilities in [0.0, 1.0] for sample inputs.
    """
    model = model_payload["model"]
    features = model_payload["features"]
    
    # Construct a sample single-row input DataFrame with valid 19 features
    sample_data = {
        "artist_smoothed_skip_rate": 0.15,
        "song_smoothed_skip_rate": 0.15,
        "genre_smoothed_skip_rate": 0.15,
        "album_smoothed_skip_rate": 0.15,
        "is_cold_start_artist": 0,
        "reason_start_smoothed_skip_rate": 0.12,
        "platform_android": 0,
        "platform_windows": 1,
        "hour_of_day": 14,
        "day_of_week": 2,
        "hour_sin": 0.5,
        "hour_cos": -0.866,
        "seconds_since_last_skip": 1000.0,
        "skips_last_3m": 0,
        "skips_last_15m": 0,
        "previous_song_skipped": 0,
        "consecutive_listens_streak": 3,
        "shuffle_mode": 0,
        "is_session_start": 0,
    }
    
    input_df = pd.DataFrame([sample_data])[features]
    
    # Run prediction
    probs = model.predict_proba(input_df)[:, 1]
    
    assert len(probs) == 1
    assert 0.0 <= probs[0] <= 1.0, f"Probability {probs[0]} outside [0.0, 1.0] bound"


def test_high_risk_vs_low_risk_predictions(model_payload):
    """
    Verifies that the model correctly assigns higher skip probability to a high-risk micro-mood spree.
    """
    model = model_payload["model"]
    features = model_payload["features"]
    
    # Low-risk baseline profile (calm listening spree)
    low_risk = {
        "artist_smoothed_skip_rate": 0.05,
        "song_smoothed_skip_rate": 0.05,
        "genre_smoothed_skip_rate": 0.05,
        "album_smoothed_skip_rate": 0.05,
        "is_cold_start_artist": 0,
        "reason_start_smoothed_skip_rate": 0.025,  # trackdone
        "platform_android": 0,
        "platform_windows": 1,
        "hour_of_day": 20,
        "day_of_week": 5,
        "hour_sin": -0.866,
        "hour_cos": 0.5,
        "seconds_since_last_skip": 10000.0,
        "skips_last_3m": 0,
        "skips_last_15m": 0,
        "previous_song_skipped": 0,
        "consecutive_listens_streak": 5,
        "shuffle_mode": 0,
        "is_session_start": 0,
    }
    
    # High-risk profile (skip spree + manual skip start)
    high_risk = {
        "artist_smoothed_skip_rate": 0.60,
        "song_smoothed_skip_rate": 0.60,
        "genre_smoothed_skip_rate": 0.60,
        "album_smoothed_skip_rate": 0.60,
        "is_cold_start_artist": 0,
        "reason_start_smoothed_skip_rate": 0.604,  # fwdbtn
        "platform_android": 1,
        "platform_windows": 0,
        "hour_of_day": 2,
        "day_of_week": 1,
        "hour_sin": 0.5,
        "hour_cos": 0.866,
        "seconds_since_last_skip": 10.0,
        "skips_last_3m": 4,
        "skips_last_15m": 8,
        "previous_song_skipped": 1,
        "consecutive_listens_streak": 0,
        "shuffle_mode": 1,
        "is_session_start": 1,
    }
    
    df_low = pd.DataFrame([low_risk])[features]
    df_high = pd.DataFrame([high_risk])[features]
    
    prob_low = model.predict_proba(df_low)[:, 1][0]
    prob_high = model.predict_proba(df_high)[:, 1][0]
    
    assert prob_high > prob_low, f"Expected high risk ({prob_high:.3f}) > low risk ({prob_low:.3f})"

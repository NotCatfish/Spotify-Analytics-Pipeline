import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
import joblib

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from path_utils import find_project_root, resolve_path

PROJECT_ROOT = find_project_root(__file__)
API_DIR = resolve_path("app/api")
PIPELINE_DIR = resolve_path("app/pipeline")

for path in [PROJECT_ROOT, API_DIR, PIPELINE_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


# Dummy objective injection for XGBoost serialized model loading compatibility
import __main__
def focal_loss_objective(y_true, y_pred):
    pass
__main__.focal_loss_objective = focal_loss_objective


@pytest.fixture(scope="session")
def project_paths():
    """Provides path anchors to key directories and files."""
    return {
        "root": PROJECT_ROOT,
        "model_path": PROJECT_ROOT / "models" / "spotify_skip_predictor_xgb.pkl",
        "db_path": PROJECT_ROOT / "data" / "processed" / "Engineered_Spotify_Portable.db",
    }


@pytest.fixture(scope="session")
def model_payload(project_paths):
    """Loads the serialized XGBoost model artifact once across the test session."""
    model_path = project_paths["model_path"]
    if not model_path.exists():
        pytest.skip(f"Model file missing at {model_path}. Skipping model tests.")
    payload = joblib.load(model_path)
    return payload


@pytest.fixture
def synthetic_streaming_df():
    """Generates a synthetic chronological streaming dataset for testing zero-leakage feature engineering."""
    np.random.seed(42)
    n_rows = 50
    timestamps = pd.date_range(start="2025-01-01 00:00:00", periods=n_rows, freq="3min")
    artists = ["Coldplay", "Radiohead", "Daft Punk", "Coldplay", "Radiohead"] * 10
    songs = [f"Track_{i}" for i in range(n_rows)]
    skips = [1 if i % 3 == 0 else 0 for i in range(n_rows)]

    df = pd.DataFrame({
        "time_stamp": timestamps,
        "artist_name": artists,
        "song_name": songs,
        "skipped": skips,
        "reason_start": ["fwdbtn" if s == 1 else "trackdone" for s in skips],
        "platform": ["windows" if i % 2 == 0 else "android" for i in range(n_rows)],
    })
    return df


@pytest.fixture
def api_client():
    """FastAPI TestClient fixture with lifespan context management."""
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as client:
        yield client

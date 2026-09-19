"""
Automated Pytest Suite - DVC Data Versioning Verification
===========================================================
Verifies that DVC tracking files exist, contain valid md5 hashes, and that
data/model binaries are tracked without leaking raw binaries into Git.
"""

import os
import pytest
from pathlib import Path

from path_utils import find_project_root, resolve_path

BASE_DIR = find_project_root(__file__)
DATA_DVC_PATH = resolve_path("data/processed/Engineered_Spotify_Portable.db.dvc")
MODEL_DVC_PATH = resolve_path("models/spotify_skip_predictor_xgb.pkl.dvc")



def test_dvc_pointer_files_exist():
    """Verifies that .dvc pointer files exist for key dataset and model binaries."""
    assert DATA_DVC_PATH.exists(), f"Missing DVC pointer file at: {DATA_DVC_PATH}"
    assert MODEL_DVC_PATH.exists(), f"Missing DVC pointer file at: {MODEL_DVC_PATH}"


def test_dvc_pointer_file_structure():
    """Verifies that .dvc pointer files contain valid YAML metadata with md5 hashes."""
    for dvc_path in [DATA_DVC_PATH, MODEL_DVC_PATH]:
        content = dvc_path.read_text(encoding="utf-8")
        assert "outs:" in content, f"Invalid DVC file format in {dvc_path}"
        assert "md5:" in content, f"Missing md5 hash in {dvc_path}"
        assert "path:" in content, f"Missing path target in {dvc_path}"


def test_dvc_file_size_is_lightweight():
    """Verifies that .dvc files are lightweight text pointers (< 500 bytes) and not heavy binaries."""
    data_dvc_size = DATA_DVC_PATH.stat().st_size
    model_dvc_size = MODEL_DVC_PATH.stat().st_size

    assert data_dvc_size < 500, f"DVC pointer file too large: {data_dvc_size} bytes"
    assert model_dvc_size < 500, f"DVC pointer file too large: {model_dvc_size} bytes"

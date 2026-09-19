"""
Automated Pytest Suite - A/B Testing & Business Utility Simulation
====================================================================
Tests for Phase 4 / Priority 4 A/B Business Utility Simulation, verifying financial cost
equations, model artifact presence, and threshold optimum logic.
"""

import pytest
from pathlib import Path
import importlib
import pandas as pd
import numpy as np

from path_utils import find_project_root, resolve_path

BASE_DIR = find_project_root(__file__)
HIGH_RECALL_MODEL_PATH = resolve_path("models/spotify_skip_predictor_high_recall.pkl")

ab_sim = importlib.import_module("app.pipeline.06_ab_testing_simulation")
compute_business_utility = ab_sim.compute_business_utility



def test_high_recall_model_artifact_exists():
    """Verifies that the trained High-Recall candidate model artifact exists on disk."""
    assert HIGH_RECALL_MODEL_PATH.exists(), f"Missing model artifact at: {HIGH_RECALL_MODEL_PATH}"


def test_compute_business_utility_formula():
    """
    Verifies the financial utility calculation logic:
    Net Utility = (TP * 1.00 MB * $0.08/1024) - (FP * $0.05)
    """
    y_true = np.array([1, 1, 0, 0, 1])
    probs = np.array([0.9, 0.8, 0.7, 0.2, 0.1])
    threshold = 0.5

    # Preds at 0.5: [1, 1, 1, 0, 0]
    # TP: 2 (indices 0, 1)
    # TN: 1 (index 3)
    # FP: 1 (index 2)
    # FN: 1 (index 4)

    res = compute_business_utility(y_true, probs, threshold)

    assert res["tp"] == 2
    assert res["tn"] == 1
    assert res["fp"] == 1
    assert res["fn"] == 1

    expected_mb = 2.0  # 2 TP * 1.00 MB
    expected_cdn_usd = (expected_mb / 1024.0) * 0.08  # $0.00015625
    expected_fp_usd = 1 * 0.05  # $0.05
    expected_net_usd = expected_cdn_usd - expected_fp_usd

    assert abs(res["mb_saved"] - expected_mb) < 1e-5
    assert abs(res["cdn_savings_usd"] - expected_cdn_usd) < 1e-5
    assert abs(res["ux_penalty_usd"] - expected_fp_usd) < 1e-5
    assert abs(res["net_utility_usd"] - expected_net_usd) < 1e-5


def test_champion_beats_high_recall_net_utility():
    """
    Verifies that the Champion model produces higher Net Financial Utility than an unconstrained
    High-Recall model due to lower False Positives.
    """
    y_true = np.array([1] * 100 + [0] * 1000)
    
    # Champion Probs: High precision, lower recall (TP=50, FP=10)
    champ_probs = np.array([0.9]*50 + [0.1]*50 + [0.8]*10 + [0.1]*990)
    
    # High-Recall Probs: High recall, terrible precision (TP=90, FP=300)
    hr_probs = np.array([0.9]*90 + [0.1]*10 + [0.8]*300 + [0.1]*700)

    champ_res = compute_business_utility(y_true, champ_probs, threshold=0.5)
    hr_res = compute_business_utility(y_true, hr_probs, threshold=0.5)

    assert champ_res["net_utility_usd"] > hr_res["net_utility_usd"], \
        f"Champion net ({champ_res['net_utility_usd']}) should beat High-Recall net ({hr_res['net_utility_usd']})"

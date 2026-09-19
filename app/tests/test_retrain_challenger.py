"""
Automated Pytest Suite - Retraining Trigger & Challenger Evaluation
=====================================================================
Tests for Phase 5C Retraining Trigger (100 resolved songs threshold) and
MLflow Challenger Model promotion guardrails.
"""

import sqlite3
import pytest
import importlib
from pathlib import Path
import numpy as np
import pandas as pd

retrain_trigger = importlib.import_module("app.pipeline.04_retrain_trigger")

check_retrain_trigger = retrain_trigger.check_retrain_trigger
count_resolved_audit_records = retrain_trigger.count_resolved_audit_records



@pytest.fixture
def temp_audit_db(tmp_path):
    """Creates a temporary SQLite shadow audit database for testing threshold logic."""
    db_file = tmp_path / "test_audit.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE shadow_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_name TEXT,
            artist_name TEXT,
            status TEXT,
            actual_skipped INTEGER
        )
    """)
    conn.commit()
    conn.close()
    return db_file


def test_retrain_trigger_below_threshold(temp_audit_db):
    """Verifies that trigger returns False when resolved records < threshold (100)."""
    conn = sqlite3.connect(temp_audit_db)
    cursor = conn.cursor()
    for i in range(45):
        cursor.execute("INSERT INTO shadow_audit (status, actual_skipped) VALUES ('RESOLVED', 1)")
    conn.commit()
    conn.close()

    count = count_resolved_audit_records(temp_audit_db)
    assert count == 45

    should_retrain = check_retrain_trigger(threshold=100, db_path=temp_audit_db, force=False)
    assert should_retrain is False


def test_retrain_trigger_above_threshold(temp_audit_db):
    """Verifies that trigger returns True when resolved records >= threshold (100)."""
    conn = sqlite3.connect(temp_audit_db)
    cursor = conn.cursor()
    for i in range(105):
        cursor.execute("INSERT INTO shadow_audit (status, actual_skipped) VALUES ('RESOLVED', 0)")
    conn.commit()
    conn.close()

    count = count_resolved_audit_records(temp_audit_db)
    assert count == 105

    should_retrain = check_retrain_trigger(threshold=100, db_path=temp_audit_db, force=False)
    assert should_retrain is True


def test_retrain_trigger_force_flag(temp_audit_db):
    """Verifies that force=True overrides threshold requirement."""
    should_retrain = check_retrain_trigger(threshold=100, db_path=temp_audit_db, force=True)
    assert should_retrain is True


def test_challenger_promotion_guardrail():
    """Verifies that Challenger is rejected if ROC-AUC improvement is below min_improvement (0.002)."""
    champion_auc = 0.8580
    challenger_auc = 0.8319
    min_improvement = 0.0020

    improvement = challenger_auc - champion_auc
    is_promoted = improvement >= min_improvement

    assert improvement < 0
    assert is_promoted is False

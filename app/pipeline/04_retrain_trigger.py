"""
Automated Retraining Trigger Module
====================================
Monitors the production shadow audit log (`data/production_audit.db`) for resolved song outcomes.
If the number of newly resolved predictions reaches or exceeds the configured threshold (default: 100 songs),
it fires a trigger signal to execute candidate model retraining and challenger evaluation.

Usage:
    python pipeline/04_retrain_trigger.py --threshold 100
    python pipeline/04_retrain_trigger.py --force
"""

import sys
import argparse
import sqlite3
from pathlib import Path

# Default paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from path_utils import find_project_root, resolve_path

BASE_DIR = find_project_root(__file__)
DEFAULT_DB = resolve_path("data/audit/production_audit.db")



def count_resolved_audit_records(db_path: Path) -> int:
    """Queries SQLite shadow audit log for resolved track outcomes."""
    if not db_path.exists():
        print(f"[WARNING] Audit database does not exist at: {db_path}")
        return 0

    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM shadow_audit WHERE status = 'RESOLVED' OR actual_skipped IS NOT NULL")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"[ERROR] Failed to query audit DB: {e}")
        return 0


def check_retrain_trigger(threshold: int = 100, db_path: Path = DEFAULT_DB, force: bool = False) -> bool:
    """
    Evaluates whether the automated retraining condition is met.
    
    Returns:
        bool: True if retraining should execute, False otherwise.
    """
    resolved_count = count_resolved_audit_records(db_path)
    
    print("\n--- RETRAINING TRIGGER AUDIT CHECK ---")
    print(f"Database Path       : {db_path}")
    print(f"Resolved Songs      : {resolved_count}")
    print(f"Retrain Threshold   : {threshold} songs")
    print(f"Force Flag Override : {force}")
    
    if force:
        print("[TRIGGER FIRED] '--force' flag provided. Executing model retraining pipeline.")
        return True
    
    if resolved_count >= threshold:
        print(f"[TRIGGER FIRED] Threshold satisfied ({resolved_count} >= {threshold}). Triggering model retraining.")
        return True
    else:
        remaining = threshold - resolved_count
        print(f"[TRIGGER SKIPPED] Insufficient data ({resolved_count} < {threshold}). Need {remaining} more resolved songs.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Automated Retraining Trigger for Spotify Skip Predictor.")
    parser.add_argument("--threshold", type=int, default=100, help="Minimum resolved songs required to trigger retraining (default: 100)")
    parser.add_argument("--db-path", type=str, default=str(DEFAULT_DB), help="Path to shadow audit SQLite database")
    parser.add_argument("--force", action="store_true", help="Force retraining trigger execution regardless of resolved song count")
    
    args = parser.parse_args()
    db_path = Path(args.db_path)
    
    should_retrain = check_retrain_trigger(threshold=args.threshold, db_path=db_path, force=args.force)
    
    if should_retrain:
        sys.exit(0)  # Exit code 0 indicates retrain trigger fired
    else:
        sys.exit(1)  # Exit code 1 indicates threshold not met


if __name__ == "__main__":
    main()

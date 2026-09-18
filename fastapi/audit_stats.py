"""
Shadow Mode Production Audit Statistics Viewer
==============================================
Prints the empirical online performance metrics of the Spotify Skip Predictor
derived from real-world natural listening sessions.

Usage:
    python fastapi/audit_stats.py
"""

import sys
import sqlite3
from pathlib import Path

# Ensure UTF-8 printing on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from audit_logger import get_audit_metrics, DB_PATH

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def main():
    metrics = get_audit_metrics()
    total = metrics["total_evaluated"]

    print("\n" + "=" * 76)
    print(f"{BOLD}{CYAN}📊 SPOTIFY SKIP PREDICTOR - REAL-WORLD SHADOW EVALUATION AUDIT{RESET}")
    print("=" * 76)
    print(f"Audit Database: {DIM}{DB_PATH}{RESET}\n")

    if total == 0:
        print(f"{YELLOW}No streaming sessions resolved yet.{RESET}")
        print("Start 'python fastapi/live_monitor.py' and listen naturally to accumulate data.\n")
        print("=" * 76)
        return

    print(f"{BOLD}1. EMPIRICAL ONLINE METRICS ({total} Total Streaming Sessions):{RESET}")
    print(f"   • {BOLD}Online Precision:{RESET}  {GREEN if metrics['precision'] >= 75 else YELLOW}{metrics['precision']}%{RESET} (Target SLA: >=75.0%)")
    print(f"   • {BOLD}Online Recall:{RESET}     {GREEN if metrics['recall'] >= 60 else YELLOW}{metrics['recall']}%{RESET}")
    print(f"   • {BOLD}Online Accuracy:{RESET}   {GREEN}{metrics['accuracy']}%{RESET}")
    print(f"   • {BOLD}Egress Saved:{RESET}      {GREEN}{BOLD}{metrics['mb_saved']} MB{RESET} of CDN audio prefetch conserved\n")

    print(f"{BOLD}2. ONLINE CONFUSION MATRIX:{RESET}")
    print("   ┌───────────────────────────────┬───────────────────────────────┐")
    print("   │                               │       ACTUAL: SKIPPED         │       ACTUAL: COMPLETED       │")
    print("   ├───────────────────────────────┼───────────────────────────────┼───────────────────────────────┤")
    print(f"   │ PREDICTED: SKIP (Risk >=0.45) │ True Positive (TP):  {GREEN}{BOLD}{metrics['tp']:<4}{RESET}    │ False Positive (FP): {RED}{BOLD}{metrics['fp']:<4}{RESET}    │")
    print(f"   │ PREDICTED: SAFE (Risk < 0.45) │ False Negative (FN): {YELLOW}{BOLD}{metrics['fn']:<4}{RESET}    │ True Negative (TN):  {GREEN}{BOLD}{metrics['tn']:<4}{RESET}    │")
    print("   └───────────────────────────────┴───────────────────────────────┴───────────────────────────────┘\n")

    print(f"{BOLD}3. RECENT RESOLVED SESSIONS (Last 10 Events):{RESET}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT resolved_at, song_name, artist_name, predicted_prob, 
               actual_played_sec, total_duration_sec, evaluation_result, cdn_mb_saved
        FROM shadow_audit WHERE status = 'RESOLVED'
        ORDER BY resolved_at DESC LIMIT 10
    """)
    rows = cursor.fetchall()
    conn.close()

    for r in rows:
        ts, song, artist, prob, played, dur, eval_res, mb = r
        if eval_res == "TRUE_POSITIVE":
            tag = f"{GREEN}[TP]{RESET}"
        elif eval_res == "TRUE_NEGATIVE":
            tag = f"{GREEN}[TN]{RESET}"
        elif eval_res == "FALSE_POSITIVE":
            tag = f"{RED}[FP]{RESET}"
        else:
            tag = f"{YELLOW}[FN]{RESET}"

        print(f"   {tag} {song[:22]:<22} by {artist[:16]:<16} | P(skip)={prob*100:.1f}% | Played: {played:.0f}s/{dur:.0f}s | Saved: {mb:.2f}MB")

    print("=" * 76 + "\n")


if __name__ == "__main__":
    main()

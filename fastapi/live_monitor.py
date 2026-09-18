"""
Spotify Live Queue Continuous Skip Monitor (Dynamic In-Place Dashboard)
=======================================================================
Runs continuously in the terminal. Polls the user's real-time Spotify session
every 2.5 seconds and renders an in-place dynamic dashboard (like htop) without
scrolling the terminal or generating duplicate messages.

Features:
- In-Place Terminal Rendering: ANSI cursor positioning (\033[H\033[J) prevents scrolling.
- Real-Time Progress Ticker: Seconds elapsed and cutoff limits update live.
- Continuous Mood Decay: Restless skip momentum decays as songs play past 45s.
- Shadow Evaluation Audit: Locks in queue predictions and resolves ground truth (TP/TN/FP/FN).

Usage:
    python fastapi/live_monitor.py
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
import requests

# Enable ANSI escape sequences on Windows console
if sys.platform == "win32":
    os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure local imports work whether run from repo root or fastapi/ dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_logger import init_audit_db, log_queue_predictions, resolve_track_outcome, get_audit_metrics

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")
HEALTH_URL = f"{FASTAPI_URL}/health"
BASE_QUEUE_URL = f"{FASTAPI_URL}/predict/live-queue"
POLL_INTERVAL_SECONDS = 0.9

# ANSI Color codes for clean terminal display
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def clear_screen():
    """Moves cursor to top-left and clears screen so the dashboard updates in place without scrolling."""
    os.system('clear')
    sys.stdout.write("\033c\033[H\033[J")
    sys.stdout.flush()


def format_bar(prob: float, length: int = 12) -> str:
    """Generates an ASCII/Unicode progress bar representing skip probability."""
    filled = int(round(prob * length))
    empty = length - filled
    if prob >= 0.776:
        bar_color = RED
    elif prob >= 0.35:
        bar_color = YELLOW
    else:
        bar_color = GREEN
    return f"{bar_color}[{'█' * filled}{'░' * empty}]{RESET}"


def display_dashboard(data: dict, session_stats: dict):
    """Formats and prints the live Spotify status, session mood, and queue predictions in-place."""
    clear_screen()
    now = datetime.now().strftime("%H:%M:%S")
    cur = data.get("currently_playing", {})
    dev = data.get("device", {})
    shuffle = data.get("shuffle_mode", False)
    forecast = data.get("upcoming_queue_forecast", [])
    high_risk = data.get("high_risk_tracks_detected", 0)

    skips_3m = session_stats.get("skips_last_3m", 0)
    sec_since_skip = session_stats.get("seconds_since_last_skip", 10000.0)
    mood = session_stats.get("mood", "CALM_FLOW")
    last_event = session_stats.get("last_event", "SESSION_START")

    prog = cur.get("progress_seconds", 0.0)
    dur = cur.get("duration_seconds", 0.0)
    cutoff = max(10.0, dur - 10.0) if dur > 15.0 else 30.0

    print("=" * 78)
    print(f"{BOLD}{CYAN}▶ SPOTIFY REAL-TIME QUEUE SKIP MONITOR{RESET}  {DIM}[Live: {now}]{RESET}")
    print("=" * 78)

    # Device & Active State
    device_info = f"{dev.get('type', 'Device')}: {dev.get('name', 'Unknown')}"
    shuffle_info = f"Shuffle: {'ON' if shuffle else 'OFF'}"
    print(f"{BOLD}Device:{RESET} {device_info} | {shuffle_info}")

    # Session Mood context
    if mood == "SKIP_SPREE":
        mood_badge = f"{RED}{BOLD}⚡ SKIP SPREE ({skips_3m} skips in 3m | High Restlessness){RESET}"
    elif mood == "RESTLESS":
        mood_badge = f"{YELLOW}{BOLD}⚠️ RESTLESS (Cooling down... {int(sec_since_skip)}s since last skip){RESET}"
    else:
        mood_badge = f"{GREEN}{BOLD}✓ CALM FLOW (Deep Listening State | Mood Settled){RESET}"

    print(f"{BOLD}Session State:{RESET} {mood_badge}")
    print(f"{BOLD}Last Action:{RESET}   {last_event}")
    print(f"{BOLD}Now Playing:{RESET}   {GREEN}{cur.get('song_name', 'Unknown')}{RESET} by {BOLD}{cur.get('artist_name', 'Unknown')}{RESET}")
    print(f"{DIM}Album: {cur.get('album_name', 'Unknown')} | Progress: {prog:.1f}s / {dur:.1f}s (Skip Cutoff: <{cutoff:.1f}s){RESET}")
    print("-" * 78)

    # Queue Forecast
    print(f"{BOLD}UPCOMING QUEUE FORECAST (Next {len(forecast)} Tracks):{RESET}")
    if not forecast:
        print(f"  {DIM}No upcoming tracks in queue.{RESET}")
    else:
        for item in forecast:
            pos = item.get("queue_position", 0)
            song = item.get("song_name", "Unknown")
            artist = item.get("artist_name", "Unknown")
            prob = item.get("skip_probability", 0.0)
            bar = format_bar(prob)
            tags = ", ".join(item.get("live_genre_tags", [])[:3]) or "No Tags"

            # Granular risk labeling aligned with human perception
            if prob >= 0.776:
                tier_str = f"{RED}{BOLD}CRITICAL SKIP (Purge Candidate){RESET}"
            elif prob >= 0.45:
                tier_str = f"{RED}HIGH SKIP RISK{RESET}"
            elif prob >= 0.35:
                tier_str = f"{YELLOW}MODERATE (Likely Skip / Watchlist){RESET}"
            else:
                tier_str = f"{GREEN}SAFE (Low Risk){RESET}"

            print(f"\n  {BOLD}#{pos}  {song}{RESET} - {artist}")
            print(f"      Tags: {DIM}{tags}{RESET}")
            print(f"      Skip Prob: {bar} {prob * 100:.1f}%  |  Status: {tier_str}")
            print(f"      CDN Policy: {item.get('cdn_policy', 'N/A')}")
            print(f"      Action:     {item.get('recommender_policy', 'N/A')}")

    print("-" * 78)
    if high_risk > 0:
        print(f"{RED}{BOLD}⚠ OVERALL DIRECTIVE:{RESET} {RED}Detected {high_risk} track(s) exceeding SLA threshold. JIT buffer throttling active.{RESET}")
    else:
        print(f"{GREEN}{BOLD}✓ OVERALL DIRECTIVE:{RESET} {GREEN}Queue flow is optimal. Standard 30s audio prefetch authorized.{RESET}")

    # Mini Shadow Evaluation Audit Scoreboard
    try:
        metrics = get_audit_metrics()
        tot = metrics.get("total_evaluated", 0)
        prec = metrics.get("precision", 0.0)
        rec = metrics.get("recall", 0.0)
        mb = metrics.get("mb_saved", 0.0)
        tp = metrics.get("tp", 0)
        tn = metrics.get("tn", 0)
        fp = metrics.get("fp", 0)
        fn = metrics.get("fn", 0)
        print("-" * 78)
        print(f"{BOLD}📊 SHADOW AUDIT METRICS:{RESET} {tot} Evaluated | Precision: {BOLD}{GREEN if prec>=75 else YELLOW}{prec}%{RESET} | Recall: {BOLD}{rec}%{RESET}")
        print(f"   Confusion Matrix: [TP: {tp} | TN: {tn} | FP: {fp} | FN: {fn}]")
        print(f"\n{BOLD}🟢 GUARDRAIL 4 (CDN BUFFER OPTIMIZATION):{RESET}")
        print(f"   {GREEN}Total Bandwidth Saved: {BOLD}{mb} MB{RESET} {DIM}(320kbps audio not prefetched for True Positives){RESET}")
    except Exception:
        pass

    print("=" * 78)
    print(f"{DIM}Updating in-place every 2.5s... (Press Ctrl+C to exit){RESET}")


def display_idle():
    """Displays a clean in-place message when Spotify is idle or paused."""
    clear_screen()
    now = datetime.now().strftime("%H:%M:%S")
    print("=" * 78)
    print(f"{BOLD}{CYAN}▶ SPOTIFY REAL-TIME QUEUE SKIP MONITOR{RESET}  {DIM}[Status: IDLE | {now}]{RESET}")
    print("=" * 78)
    print(f"\n  {YELLOW}Spotify playback is currently paused or idle.{RESET}")
    print(f"  Play any track on your phone or PC to activate real-time queue prediction.\n")
    print("=" * 78)
    print(f"{DIM}Waiting for playback to resume... (Press Ctrl+C to exit){RESET}")


def check_fastapi_connection():
    """Verifies that the FastAPI microservice is running and accessible."""
    try:
        r = requests.get(HEALTH_URL, timeout=3.0)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False


def main():
    # Initialize shadow audit SQLite database
    init_audit_db()

    # Check connection
    if not check_fastapi_connection():
        print(f"{YELLOW}[WARN] FastAPI server is not responding at {FASTAPI_URL}.{RESET}")
        print(f"Please make sure the server is running with:")
        print(f"    uvicorn main:app --reload --app-dir fastapi\n")
        print("Waiting for server to become available...")
        while not check_fastapi_connection():
            time.sleep(2.0)

    last_track_id = None
    last_track_name = ""
    last_artist_name = ""
    last_album_name = ""
    last_status = None
    last_progress = 0.0
    last_duration = 0.0
    skip_timestamps = []
    previous_song_skipped = False
    reason_start = "trackdone"
    last_event_desc = "Session Connected"
    
    backoff = 2.0

    try:
        while True:
            try:
                # Fast poll to inspect active playback state
                peek_resp = requests.get(f"{BASE_QUEUE_URL}?queue_limit=1", timeout=8.0)
                if peek_resp.status_code == 200:
                    payload = peek_resp.json()
                    status = payload.get("status")

                    if status == "ACTIVE":
                        current_track = payload.get("currently_playing", {})
                        current_id = current_track.get("id")
                        curr_progress = current_track.get("progress_seconds", 0.0)
                        curr_duration = current_track.get("duration_seconds", 180.0)
                        curr_name = current_track.get("song_name", "Unknown")
                        curr_artist = current_track.get("artist_name", "Unknown")
                        curr_album = current_track.get("album_name", "Unknown")

                        now = time.time()
                        # A track change happens if the ID changes, or if the same track restarts from the beginning
                        is_track_change = (current_id != last_track_id) or (current_id == last_track_id and curr_progress < last_progress - 5.0)

                        # Handle track change event
                        if is_track_change:
                            if last_track_id is not None:
                                cutoff = max(10.0, last_duration - 10.0) if last_duration > 15.0 else 30.0
                                was_skipped = (last_progress < cutoff)
                                if was_skipped:
                                    skip_timestamps.append(now)
                                    previous_song_skipped = True
                                    reason_start = "fwdbtn"
                                else:
                                    previous_song_skipped = False
                                    reason_start = "trackdone"

                                # Resolve previous track in Shadow Audit DB!
                                resolution = resolve_track_outcome(
                                    last_track_name, last_artist_name, last_album_name, last_progress, last_duration, was_skipped
                                )
                                if resolution:
                                    res_tag = resolution["evaluation"]
                                    mb_tag = f" (+{resolution['mb_saved']}MB saved)" if resolution["mb_saved"] > 0 else ""
                                    if was_skipped:
                                        last_event_desc = f"{RED}⚡ SKIPPED '{last_track_name}' ({last_progress:.0f}s/{last_duration:.0f}s) -> [{res_tag}]{mb_tag}{RESET}"
                                    else:
                                        last_event_desc = f"{GREEN}✓ Completed '{last_track_name}' ({last_progress:.0f}s/{last_duration:.0f}s) -> [{res_tag}]{RESET}"
                            else:
                                last_event_desc = "Listening Session Active"

                        # Handle active listening progress (decay restlessness past 45s)
                        if not is_track_change and curr_progress >= 45.0:
                            previous_song_skipped = False
                            reason_start = "trackdone"
                            last_event_desc = f"{GREEN}✓ Settled into '{curr_name}' ({curr_progress:.1f}s played) | Restlessness Decayed{RESET}"

                        # Prune skip timestamps older than 15 minutes
                        skip_timestamps = [t for t in skip_timestamps if now - t <= 900]
                        skips_3m = len([t for t in skip_timestamps if now - t <= 180])
                        skips_15m = len(skip_timestamps)
                        sec_since_skip = (now - skip_timestamps[-1]) if skip_timestamps else 10000.0

                        # Determine mood
                        if skips_3m >= 2 and curr_progress < 45.0:
                            current_mood = "SKIP_SPREE"
                        elif (skips_3m >= 1 or sec_since_skip < 45.0) and curr_progress < 60.0:
                            current_mood = "RESTLESS"
                        else:
                            current_mood = "CALM_FLOW"

                        # Query predictions for full 5-track upcoming queue
                        forecast_params = {
                            "queue_limit": 5,
                            "previous_song_skipped": previous_song_skipped,
                            "skips_last_3m": skips_3m,
                            "skips_last_15m": skips_15m,
                            "seconds_since_last_skip": round(sec_since_skip, 1),
                            "reason_start": reason_start
                        }
                        full_resp = requests.get(BASE_QUEUE_URL, params=forecast_params, timeout=10.0)
                        if full_resp.status_code == 200:
                            full_payload = full_resp.json()
                            # Lock in shadow predictions for upcoming queue tracks
                            log_queue_predictions(full_payload.get("upcoming_queue_forecast", []))
                        else:
                            full_payload = payload

                        session_stats = {
                            "skips_last_3m": skips_3m,
                            "skips_last_15m": skips_15m,
                            "seconds_since_last_skip": sec_since_skip,
                            "mood": current_mood,
                            "last_event": last_event_desc
                        }

                        # Display updated dashboard in-place
                        display_dashboard(full_payload, session_stats)

                        last_track_id = current_id
                        last_track_name = curr_name
                        last_artist_name = curr_artist
                        last_album_name = curr_album
                        last_status = "ACTIVE"
                        last_progress = curr_progress
                        last_duration = curr_duration

                    elif status == "IDLE":
                        if last_status != "IDLE":
                            display_idle()
                            last_status = "IDLE"
                            # BUG FIX: Do NOT wipe last_track_id and progress!
                            # If the user pauses Spotify, the session goes IDLE. When they unpause, 
                            # we need to remember the track so we can resolve its outcome properly.

                    elif status == "ERROR":
                        msg = payload.get("message", "Unknown error")
                        clear_screen()
                        print(f"\n{RED}[SPOTIFY ERROR]{RESET} {msg}\n")

                elif peek_resp.status_code == 401 or "auth_url" in peek_resp.text:
                    clear_screen()
                    print(f"\n{YELLOW}[AUTH NEEDED]{RESET} Please visit {FASTAPI_URL}/login to authenticate your Spotify account.\n")
                    time.sleep(5.0)

            except requests.exceptions.Timeout:
                clear_screen()
                print(f"\n{YELLOW}[WARN]{RESET} FastAPI server request timed out. Retrying in {backoff:.1f}s...\n")
                time.sleep(backoff)
                backoff = min(10.0, backoff * 1.5)
            except requests.exceptions.ConnectionError:
                clear_screen()
                print(f"\n{RED}[ERROR]{RESET} Lost connection to FastAPI server. Retrying in {backoff:.1f}s...\n")
                time.sleep(backoff)
                backoff = min(10.0, backoff * 1.5)
            except Exception as ex:
                clear_screen()
                print(f"\n{RED}[FATAL ERROR]{RESET} Unexpected exception in live_monitor: {ex}\n")
                import traceback
                traceback.print_exc()
                time.sleep(backoff)
                backoff = min(10.0, backoff * 1.5)
            else:
                backoff = 2.0
                try:
                    Path("/app/data/heartbeat.txt").touch(exist_ok=True)
                except Exception:
                    pass

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print(f"\n{CYAN}Live Monitor stopped by user. Goodbye!{RESET}")


if __name__ == "__main__":
    main()

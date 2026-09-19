import streamlit as st
import requests
import sqlite3
import os
import time

st.set_page_config(page_title="Spotify ML Queue", page_icon="🎵", layout="centered")

API_URL = os.getenv("FASTAPI_URL", "http://api:8000")
DB_PATH = "/app/data/production_audit.db"

def get_live_data():
    try:
        r = requests.get(f"{API_URL}/predict/live-queue", params={"queue_limit": 5}, timeout=5.0)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
    return {"status": "ERROR", "message": "API Not Responding"}

def get_audit_metrics():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM shadow_audit WHERE status='RESOLVED'")
        total = c.fetchone()[0]
        
        c.execute("SELECT evaluation_result, COUNT(*) FROM shadow_audit WHERE status='RESOLVED' GROUP BY evaluation_result")
        results = dict(c.fetchall())
        
        tp = results.get("TRUE_POSITIVE", 0)
        tn = results.get("TRUE_NEGATIVE", 0)
        fp = results.get("FALSE_POSITIVE", 0)
        fn = results.get("FALSE_NEGATIVE", 0)
        
        prec = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0.0
        rec = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0.0
        
        return {"total": total, "tp": tp, "tn": tn, "fp": fp, "fn": fn, "precision": prec, "recall": rec}
    except Exception:
        return {"total": 0, "tp": 0, "tn": 0, "fp": 0, "fn": 0, "precision": 0.0, "recall": 0.0}

def main():
    st.title("🎵 Live Queue Monitor")
    
    data = get_live_data()
    status = data.get("status", "ERROR")
    
    if status == "IDLE":
        st.warning("Spotify playback is currently paused or idle. Play a track on your phone/PC to start monitoring.")
    elif status == "ERROR":
        st.error(f"Error fetching data: {data.get('message')}")
    elif status == "ACTIVE":
        cur = data.get("currently_playing", {})
        
        # Now Playing
        st.markdown("### Now Playing")
        st.markdown(f"**{cur.get('song_name', 'Unknown')}** by {cur.get('artist_name', 'Unknown')}")
        prog = cur.get("progress_seconds", 0)
        dur = cur.get("duration_seconds", 100)
        
        # Progress bar
        pct = min(prog / dur if dur > 0 else 0, 1.0)
        st.progress(pct, text=f"Progress: {prog:.0f}s / {dur:.0f}s")
        
        st.markdown("---")
        st.markdown("### Upcoming Queue Forecast")
        forecast = data.get("upcoming_queue_forecast", [])
        if not forecast:
            st.info("No upcoming tracks in queue.")
        else:
            for i, item in enumerate(forecast):
                song = item.get("song_name")
                artist = item.get("artist_name")
                prob = item.get("skip_probability", 0.0)
                
                if prob >= 0.776:
                    color = "red"
                    tier = "CRITICAL SKIP"
                elif prob >= 0.45:
                    color = "orange"
                    tier = "HIGH SKIP RISK"
                elif prob >= 0.35:
                    color = "yellow"
                    tier = "MODERATE"
                else:
                    color = "green"
                    tier = "SAFE"
                
                st.markdown(f"**#{i+1} {song}** - {artist} | :{color}[{tier}]")
                st.progress(prob, text=f"Skip Probability: {prob*100:.1f}%")
        
    st.markdown("---")
    st.markdown("### Shadow Audit Metrics")
    metrics = get_audit_metrics()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Evaluated", metrics["total"])
    col2.metric("Precision", f"{metrics['precision']:.1f}%")
    col3.metric("Recall", f"{metrics['recall']:.1f}%")
    
    st.caption(f"**TP:** {metrics['tp']} | **TN:** {metrics['tn']} | **FP:** {metrics['fp']} | **FN:** {metrics['fn']}")
    
    # Auto-refresh every 2 seconds
    time.sleep(2)
    st.rerun()

if __name__ == "__main__":
    main()

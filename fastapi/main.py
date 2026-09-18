from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import joblib
from schemas import SkipPredictionResponse, TrackPredictRequest, DualPolicyAction
from spotify_client import get_spotify_oauth, get_live_spotify_data, get_lastfm_tags, control_playback, change_volume
import math
from datetime import datetime
import pandas as pd
import sqlite3
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "spotify_skip_predictor_xgb.pkl"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "Engineered_Spotify_Portable.db"

ml_artifacts=dict()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if MODEL_PATH.exists()==False:
        raise FileNotFoundError(f"Model artifact not found at {MODEL_PATH}")
    
    # Inject dummy focal_loss_objective into __main__ to fix joblib load error
    # (XGBoost saves the custom objective reference from training, but it's only needed for training)
    import __main__
    def focal_loss_objective(y_true, y_pred):
        pass
    __main__.focal_loss_objective = focal_loss_objective
    
    payload=joblib.load(MODEL_PATH)


    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        # 1. Artist skip rates (case-insensitive)
        artist_df = pd.read_sql("SELECT artist_name, artist_smoothed_skip_rate FROM Engineered_Spotify_Portable ORDER BY time_stamp DESC", conn)
        ml_artifacts["artist_lookup"] = {
            name.lower().strip(): rate 
            for name, rate in artist_df.drop_duplicates("artist_name").values
        }
        
        # 2. Song skip rates (case-insensitive)
        song_df = pd.read_sql("SELECT song_name, song_smoothed_skip_rate FROM Engineered_Spotify_Portable ORDER BY time_stamp DESC", conn)
        ml_artifacts["song_lookup"] = {
            name.lower().strip(): rate 
            for name, rate in song_df.drop_duplicates("song_name").values
        }
        conn.close()
        print(f"[STARTUP] Feature Store loaded: {len(ml_artifacts['artist_lookup'])} artists, {len(ml_artifacts['song_lookup'])} songs.")
    else:
        ml_artifacts["artist_lookup"] = {}
        ml_artifacts["song_lookup"] = {}

    
    ml_artifacts["model"] = payload["model"]
    try:
        ml_artifacts["model"].set_params(device="cpu")
    except Exception:
        pass
    ml_artifacts["features"] = payload["features"]
    ml_artifacts["threshold"] = payload["best_threshold"]
    ml_artifacts["is_ready"] = True
    print("[STARTUP] Spotify Model loaded into RAM successfully (CPU mode)!")

    yield

    ml_artifacts.clear()
    print("[SHUTDOWN] Cleared model from RAM.")

app=FastAPI(title="Spotify Skip Prediction Microservice", version="1.0.0", lifespan=lifespan)

static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health")
def healthcheck():
    if not ml_artifacts.get("is_ready"):
        raise HTTPException(status_code=503, detail="Service is Unavaliable")
    
    return {
        "status":"healthy",
        "model": "XGBoost Classifier",
        "threshold": ml_artifacts["threshold"],
        "features_count": len(ml_artifacts["features"])
    }


@app.post("/predict-skip", response_model=SkipPredictionResponse)
def model_call(data:TrackPredictRequest):
    now=datetime.now()
    hour=now.hour
    day=now.weekday()
    hour_sin = math.sin(2 * math.pi * hour / 24)
    hour_cos = math.cos(2 * math.pi * hour / 24)

    platform_str = data.platform.lower()
    if "android" in platform_str:
        platform_android = 1
        platform_windows = 0
    elif "windows" in platform_str or "win" in platform_str:
        platform_android = 0
        platform_windows = 1
    else:
        platform_android = 0
        platform_windows = 0

    reason_map={
        "trackdone":0.025,
        "clickrow":0.120,
        "fwdbtn":0.604,
        "backbtn":0.400,
        "playbtn":0.050
    }
    reason_start_risk = reason_map.get(data.reason_start.lower(), 0.104)


    artist_key = data.artist_name.strip().lower()
    is_cold_start = 1 if artist_key not in ml_artifacts["artist_lookup"] else 0
    artist_rate = ml_artifacts["artist_lookup"].get(artist_key, 0.104)
    song_key = data.song_name.strip().lower()
    song_rate = ml_artifacts["song_lookup"].get(song_key, artist_rate)


    features_dict={
        "artist_smoothed_skip_rate": float(artist_rate),
        "song_smoothed_skip_rate": float(song_rate),
        "genre_smoothed_skip_rate": float(artist_rate), 
        "album_smoothed_skip_rate": float(artist_rate),
        "is_cold_start_artist": is_cold_start,
        "reason_start_smoothed_skip_rate": reason_start_risk,
        "platform_android": platform_android,
        "platform_windows": platform_windows,
        "hour_of_day": hour,
        "day_of_week": day,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "seconds_since_last_skip": data.seconds_since_last_skip,
        "skips_last_3m": data.skips_last_3m,
        "skips_last_15m": data.skips_last_15m,
        "previous_song_skipped": int(data.previous_song_skipped),
        "consecutive_listens_streak": data.consecutive_listens_streak,
        "shuffle_mode": int(data.shuffle_mode),
        "is_session_start": 1 if data.consecutive_listens_streak == 0 else 0
    }

    input_df = pd.DataFrame([features_dict])[ml_artifacts["features"]]
    
    model=ml_artifacts["model"]
    prob = float(model.predict_proba(input_df)[0][1])
    threshold = float(ml_artifacts["threshold"])
    is_skip = prob >= threshold

    if is_skip:
        risk_tier = "CRITICAL"
        cdn_policy = "JIT_3SEC_CHUNKING (Stop 30s prefetch to save bandwidth)"
        rec_policy = "SILENT_AUTOPLAY_PURGE (Silently drop track before playback)"
        explanation = f"High skip probability ({prob * 100:.1f}%) exceeds SLA threshold ({threshold * 100:.1f}%)."

    else:
        risk_tier = "LOW" if prob < 0.35 else "MODERATE"
        cdn_policy = "STANDARD_PREFETCH"
        rec_policy = "KEEP_IN_QUEUE"
        explanation = f"Safe skip probability ({prob * 100:.1f}%). User is in flow state."
    
    return SkipPredictionResponse(
        song_name=data.song_name,
        artist_name=data.artist_name,
        skip_probability=round(prob, 4),
        is_skip_predicted=is_skip,
        decision_threshold=threshold,
        risk_tier=risk_tier,
        actions=DualPolicyAction(
            cdn_buffer_policy=cdn_policy,
            recommender_policy=rec_policy,
            explanation=explanation
        )
    )


@app.get("/login")
def spotify_login():
    """Redirects the user to Spotify's official OAuth authorization page."""
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)


@app.get("/callback")
def spotify_callback(code: str):
    """Handles Spotify OAuth redirect and securely caches the user session token."""
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_access_token(code)
    if token_info:
        return RedirectResponse("/static/dashboard.html")
    raise HTTPException(status_code=400, detail="Failed to retrieve access token from Spotify.")


@app.get("/predict/live-queue")
def predict_live_queue(
    queue_limit: int = 5,
    previous_song_skipped: bool = False,
    skips_last_3m: int = 0,
    skips_last_15m: int = 0,
    seconds_since_last_skip: float = 10000.0,
    reason_start: str = "trackdone"
):
    """Predicts skip probabilities for the next 5 upcoming songs in your active Spotify queue."""
    data = get_live_spotify_data(queue_limit=queue_limit)
    if data.get("status") != "ACTIVE":
        return data

    upcoming_tracks = data.get("next_queued_tracks", [])
    predictions = []
    high_risk_count = 0

    if upcoming_tracks:
        for idx, track in enumerate(upcoming_tracks, start=1):
            live_tags = get_lastfm_tags(track["artist_name"], track["song_name"])
            top_genre = live_tags[0] if live_tags else "Unknown"

            synthetic_req = TrackPredictRequest(
                song_name=track["song_name"],
                artist_name=track["artist_name"],
                album_name=track.get("album_name", "Unknown"),
                genre=top_genre,
                platform=data["device"]["type"],
                shuffle_mode=data["shuffle_mode"],
                reason_start=reason_start,
                skips_last_3m=skips_last_3m,
                skips_last_15m=skips_last_15m,
                seconds_since_last_skip=seconds_since_last_skip,
                previous_song_skipped=previous_song_skipped
            )
            pred = model_call(synthetic_req)
            if pred.is_skip_predicted:
                high_risk_count += 1

            predictions.append({
                "queue_position": idx,
                "song_name": track["song_name"],
                "artist_name": track["artist_name"],
                "album_name": track.get("album_name", "Unknown"),
                "live_genre_tags": live_tags,
                "skip_probability": pred.skip_probability,
                "is_skip_predicted": pred.is_skip_predicted,
                "risk_tier": pred.risk_tier,
                "cdn_policy": pred.actions.cdn_buffer_policy,
                "recommender_policy": pred.actions.recommender_policy,
                "explanation": pred.actions.explanation
            })
    else:
        # Fallback to currently playing song if queue is empty
        cur = data["current_track"]
        live_tags = get_lastfm_tags(cur["artist_name"], cur["song_name"])
        synthetic_req = TrackPredictRequest(
            song_name=cur["song_name"],
            artist_name=cur["artist_name"],
            album_name=cur.get("album_name", "Unknown"),
            genre=live_tags[0] if live_tags else "Unknown",
            platform=data["device"]["type"],
            shuffle_mode=data["shuffle_mode"],
            reason_start="clickrow"
        )
        pred = model_call(synthetic_req)
        predictions.append({
            "queue_position": 0,
            "evaluation_target": "CURRENTLY_PLAYING (No queued tracks available)",
            "song_name": cur["song_name"],
            "artist_name": cur["artist_name"],
            "album_name": cur.get("album_name", "Unknown"),
            "live_genre_tags": live_tags,
            "skip_probability": pred.skip_probability,
            "is_skip_predicted": pred.is_skip_predicted,
            "risk_tier": pred.risk_tier,
            "cdn_policy": pred.actions.cdn_buffer_policy,
            "recommender_policy": pred.actions.recommender_policy,
            "explanation": pred.actions.explanation
        })

    # Overall queue directive
    if high_risk_count > 0:
        overall_action = f"ACTION_REQUIRED: Detected {high_risk_count} high-risk tracks in upcoming queue. Triggering JIT buffer throttling and silent purge."
    else:
        overall_action = "OPTIMAL_FLOW: All upcoming tracks below skip threshold. Safe for full 30s CDN pre-fetch."

    return {
        "status": "ACTIVE",
        "currently_playing": data["current_track"],
        "device": data["device"],
        "shuffle_mode": data["shuffle_mode"],
        "queue_tracks_evaluated": len(predictions),
        "high_risk_tracks_detected": high_risk_count,
        "overall_directive": overall_action,
        "upcoming_queue_forecast": predictions
    }

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Spotify ML Dashboard</title>
        <style>
            body { background-color: #121212; color: #FFFFFF; font-family: 'Inter', sans-serif; padding: 20px; }
            .card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1, h2, h3 { color: #1DB954; margin-top: 0; }
            .progress-bg { background-color: #333; border-radius: 5px; width: 100%; height: 20px; margin-top: 5px; }
            .progress-fill { height: 100%; border-radius: 5px; transition: width 0.5s ease-in-out; }
            .badge-red { background-color: #E22134; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
            .badge-orange { background-color: #FF9800; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
            .badge-yellow { background-color: #FFC107; color: black; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
            .badge-green { background-color: #1DB954; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
            .metrics-row { display: flex; justify-content: space-between; }
            .metric-box { text-align: center; background-color: #2A2A2A; padding: 10px; border-radius: 10px; flex: 1; margin: 0 5px; }
            .metric-val { font-size: 24px; font-weight: bold; color: #1DB954; }
            .loader { text-align: center; color: #888; font-size: 14px; margin-bottom: 15px; }
        </style>
        <script>
            function fetchData() {
                fetch('/dashboard/data')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'ERROR' || data.status === 'IDLE') {
                            document.getElementById('content').innerHTML = '<div class="card"><h3>Status: ' + data.status + '</h3><p>' + (data.message || 'Waiting for Spotify playback...') + '</p></div>';
                        } else {
                            renderDashboard(data);
                        }
                        setTimeout(fetchData, 1000); // Auto refresh every 1s
                    })
                    .catch(error => {
                        console.error('Error fetching data:', error);
                        setTimeout(fetchData, 2000);
                    });
            }

            function getBadge(prob) {
                if(prob >= 0.776) return '<span class="badge-red">CRITICAL SKIP</span>';
                if(prob >= 0.45) return '<span class="badge-orange">HIGH RISK</span>';
                if(prob >= 0.35) return '<span class="badge-yellow">MODERATE</span>';
                return '<span class="badge-green">SAFE</span>';
            }

            function getColor(prob) {
                if(prob >= 0.776) return '#E22134';
                if(prob >= 0.45) return '#FF9800';
                if(prob >= 0.35) return '#FFC107';
                return '#1DB954';
            }

            function renderDashboard(data) {
                let cur = data.currently_playing || {};
                let dur = cur.duration_seconds || 100;
                let prog = cur.progress_seconds || 0;
                let pct = Math.min(prog / dur, 1.0) * 100;

                let html = `
                    <div class="card">
                        <h3>Now Playing</h3>
                        <p style="margin:5px 0; font-size: 18px;"><strong>${cur.song_name || 'Unknown'}</strong> by ${cur.artist_name || 'Unknown'}</p>
                        <div style="font-size: 12px; color: #aaa; margin-bottom: 5px;">Progress: ${Math.round(prog)}s / ${Math.round(dur)}s</div>
                        <div class="progress-bg">
                            <div class="progress-fill" style="width: ${pct}%; background-color: #1DB954;"></div>
                        </div>
                    </div>
                `;

                html += `<h3>Upcoming Queue Forecast</h3>`;
                let forecast = data.upcoming_queue_forecast || [];
                if(forecast.length === 0) {
                    html += `<div class="card"><p style="color:#aaa;">No upcoming tracks in queue.</p></div>`;
                } else {
                    forecast.forEach((item, idx) => {
                        let prob = item.skip_probability || 0;
                        let pPct = prob * 100;
                        html += `
                            <div class="card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <div style="font-size: 16px;"><strong>#${idx+1} ${item.song_name || 'Unknown'}</strong></div>
                                    <div>${getBadge(prob)}</div>
                                </div>
                                <div style="font-size: 13px; color: #ccc; margin-bottom: 8px;">Artist: ${item.artist_name || 'Unknown'} &nbsp;|&nbsp; Skip Prob: ${pPct.toFixed(1)}%</div>
                                <div class="progress-bg">
                                    <div class="progress-fill" style="width: ${pPct}%; background-color: ${getColor(prob)};"></div>
                                </div>
                            </div>
                        `;
                    });
                }
                
                let metrics = data.metrics || {total:0, tp:0, fp:0, tn:0, fn:0, prec:0, rec:0};
                html += `
                    <h3 style="margin-top:20px;">Shadow Audit Metrics</h3>
                    <div class="metrics-row">
                        <div class="metric-box"><div>Evaluated</div><div class="metric-val">${metrics.total}</div></div>
                        <div class="metric-box"><div>Precision</div><div class="metric-val">${metrics.prec.toFixed(1)}%</div></div>
                        <div class="metric-box"><div>Recall</div><div class="metric-val">${metrics.rec.toFixed(1)}%</div></div>
                    </div>
                    <div class="card" style="margin-top: 15px; text-align: center; font-size: 14px; color: #aaa; background-color: #1E1E1E;">
                        <span style="color:#1DB954;">TP: ${metrics.tp}</span> | TN: ${metrics.tn} | <span style="color:#E22134;">FP: ${metrics.fp}</span> | FN: ${metrics.fn}
                    </div>
                `;

                document.getElementById('content').innerHTML = html;
            }

            window.onload = fetchData;
        </script>
    </head>
    <body>
        <h2>🎵 Spotify ML Dashboard</h2>
        <div class="loader">Live sync every 1.0s...</div>
        <div id="content">
            <div class="card" style="text-align: center; color: #888;">Connecting to Spotify API...</div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/dashboard/data")
def get_dashboard_data():
    data = predict_live_queue(queue_limit=5)
    
    try:
        audit_db_path = Path(__file__).resolve().parent.parent / "data" / "production_audit.db"
        conn = sqlite3.connect(audit_db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM shadow_audit WHERE status='RESOLVED'")
        row = c.fetchone()
        total = row[0] if row else 0
        
        c.execute("SELECT evaluation_result, COUNT(*) FROM shadow_audit WHERE status='RESOLVED' GROUP BY evaluation_result")
        results = dict(c.fetchall())
        tp = results.get("TRUE_POSITIVE", 0)
        tn = results.get("TRUE_NEGATIVE", 0)
        fp = results.get("FALSE_POSITIVE", 0)
        fn = results.get("FALSE_NEGATIVE", 0)
        
        prec = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0.0
        rec = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0.0
        conn.close()
        
        data["metrics"] = {"total": total, "tp": tp, "tn": tn, "fp": fp, "fn": fn, "prec": prec, "rec": rec}
    except Exception as e:
        data["metrics"] = {"total": 0, "tp": 0, "tn": 0, "fp": 0, "fn": 0, "prec": 0.0, "rec": 0.0}
        
    return data



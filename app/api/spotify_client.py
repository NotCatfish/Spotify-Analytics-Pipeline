import os
from pathlib import Path
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from path_utils import resolve_path

ENV_PATH = resolve_path(".env")
load_dotenv(ENV_PATH)

CACHE_PATH = str(resolve_path("app/api/.spotify_cache"))


def get_spotify_oauth():
    """Returns the Spotify OAuth manager configured with project credentials."""
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8000/callback"),
        scope="user-read-playback-state user-read-currently-playing user-read-recently-played",
        cache_path=CACHE_PATH,
        open_browser=False,
        show_dialog=True
    )


_TAG_CACHE = {}

def get_lastfm_tags(artist_name: str, song_name: str = "") -> list:
    """Queries Last.fm API to fetch top genre tags for a track, with artist fallback and in-memory cache."""
    cache_key = f"{artist_name.strip().lower()}|||{song_name.strip().lower()}"
    if cache_key in _TAG_CACHE:
        return _TAG_CACHE[cache_key]

    api_key = os.getenv("LASTFM_API_KEY")
    base_url = os.getenv("LASTFM_BASE_URL", "http://ws.audioscrobbler.com/2.0/")
    if not api_key:
        return []

    # 1. Try track-level top tags
    if song_name:
        params = {
            "method": "track.getTopTags",
            "artist": artist_name,
            "track": song_name,
            "api_key": api_key,
            "format": "json"
        }
        try:
            res = requests.get(base_url, params=params, timeout=3.0)
            if res.status_code == 200:
                tags = res.json().get("toptags", {}).get("tag", [])
                extracted = [t["name"].lower().strip() for t in tags if isinstance(t, dict) and "name" in t]
                if extracted:
                    _TAG_CACHE[cache_key] = extracted[:5]
                    return extracted[:5]
        except Exception:
            pass

    # 2. Fallback to artist-level top tags
    params_artist = {
        "method": "artist.getTopTags",
        "artist": artist_name,
        "api_key": api_key,
        "format": "json"
    }
    try:
        res = requests.get(base_url, params=params_artist, timeout=3.0)
        if res.status_code == 200:
            tags = res.json().get("toptags", {}).get("tag", [])
            extracted = [t["name"].lower().strip() for t in tags if isinstance(t, dict) and "name" in t]
            if extracted:
                _TAG_CACHE[cache_key] = extracted[:5]
                return extracted[:5]
    except Exception:
        pass

    _TAG_CACHE[cache_key] = []
    return []


_LIVE_SPOTIFY_CACHE = {"timestamp": 0, "data": None}

def get_live_spotify_data(queue_limit: int = 5):
    """Fetches real-time playback and upcoming queued songs using Spotipy with 3.5s in-memory caching to prevent 429 Rate Limiting."""
    import time
    now = time.time()
    
    # Return cached data if fresh (less than 0.9s old)
    if _LIVE_SPOTIFY_CACHE["data"] is not None and (now - _LIVE_SPOTIFY_CACHE["timestamp"]) < 0.9:
        return _LIVE_SPOTIFY_CACHE["data"]

    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.validate_token(sp_oauth.cache_handler.get_cached_token())

    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        return {
            "status": "AUTH_REQUIRED",
            "message": "Spotify account not authorized yet. Please visit /login to authenticate.",
            "auth_url": auth_url
        }

    sp = spotipy.Spotify(auth=token_info["access_token"], requests_timeout=2, retries=0)

    try:
        playback = sp.current_playback()
    except Exception as e:
        # If rate limited (429) or transient error, serve last cached data if available
        if _LIVE_SPOTIFY_CACHE["data"] is not None:
            return _LIVE_SPOTIFY_CACHE["data"]
        return {"status": "ERROR", "message": f"Spotify API request failed: {str(e)}"}

    if not playback or not playback.get("item"):
        res_idle = {
            "status": "IDLE",
            "message": "No active playback detected. Please play a track on your Spotify app first."
        }
        _LIVE_SPOTIFY_CACHE["timestamp"] = now
        _LIVE_SPOTIFY_CACHE["data"] = res_idle
        return res_idle

    # Extract current track
    item = playback["item"]
    track_id = item.get("id", "")
    current_song = item.get("name", "Unknown Track")
    artists = [a.get("name") for a in item.get("artists", []) if a.get("name")]
    current_artist = artists[0] if artists else "Unknown Artist"
    current_album = item.get("album", {}).get("name", "Unknown Album")
    device_type = playback.get("device", {}).get("type", "Computer")
    device_name = playback.get("device", {}).get("name", "Unknown Device")
    shuffle_state = bool(playback.get("shuffle_state", False))
    progress_sec = round(playback.get("progress_ms", 0) / 1000.0, 1)
    duration_sec = round(item.get("duration_ms", 0) / 1000.0, 1)

    # Extract upcoming queued tracks (up to queue_limit)
    next_tracks = []
    try:
        queue_data = sp.queue()
        if queue_data and queue_data.get("queue"):
            for q_item in queue_data["queue"][:queue_limit]:
                q_song = q_item.get("name", "Unknown Track")
                q_artists = [a.get("name") for a in q_item.get("artists", []) if a.get("name")]
                q_artist = q_artists[0] if q_artists else "Unknown Artist"
                q_album = q_item.get("album", {}).get("name", "Unknown Album")
                next_tracks.append({
                    "song_name": q_song,
                    "artist_name": q_artist,
                    "album_name": q_album
                })
    except Exception:
        pass

    res_active = {
        "status": "ACTIVE",
        "current_track": {
            "id": track_id,
            "song_name": current_song,
            "artist_name": current_artist,
            "album_name": current_album,
            "progress_seconds": progress_sec,
            "duration_seconds": duration_sec
        },
        "next_queued_tracks": next_tracks,
        "next_queued_track": next_tracks[0] if next_tracks else None,
        "device": {
            "type": device_type,
            "name": device_name
        },
        "shuffle_mode": shuffle_state
    }
    _LIVE_SPOTIFY_CACHE["timestamp"] = now
    _LIVE_SPOTIFY_CACHE["data"] = res_active
    return res_active

def control_playback(action: str):
    """Controls Spotify playback (play, pause, next, previous)."""
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.validate_token(sp_oauth.cache_handler.get_cached_token())
    if not token_info:
        return {"status": "ERROR", "message": "Not authenticated"}
    
    sp = spotipy.Spotify(auth=token_info["access_token"], requests_timeout=5, retries=1)
    try:
        if action == "play":
            sp.start_playback()
        elif action == "pause":
            sp.pause_playback()
        elif action == "next":
            sp.next_track()
        elif action == "previous":
            sp.previous_track()
        return {"status": "SUCCESS"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def change_volume(volume_percent: int):
    """Changes the volume of the active Spotify device."""
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.validate_token(sp_oauth.cache_handler.get_cached_token())
    if not token_info:
        return {"status": "ERROR", "message": "Not authenticated"}
    
    sp = spotipy.Spotify(auth=token_info["access_token"], requests_timeout=5, retries=1)
    try:
        sp.volume(volume_percent)
        return {"status": "SUCCESS"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
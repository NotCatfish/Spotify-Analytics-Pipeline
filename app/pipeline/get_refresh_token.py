"""
One-Time Spotify Refresh Token Generator
=========================================
Generates an updated SPOTIPY_REFRESH_TOKEN containing:
- user-read-playback-state
- user-read-currently-playing
- user-read-recently-played

Usage:
    python app/pipeline/get_refresh_token.py
"""

import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from path_utils import resolve_path

import spotipy
from app.api.spotify_client import get_spotify_oauth

auth_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urlparse(self.path).query
        params = parse_qs(query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Successful!</h1><p>You can close this tab and return to your terminal.</p>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Failed!</h1>")

    def log_message(self, format, *args):
        pass  # Suppress default server logs


def main():
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()

    print("=" * 70)
    print("▶ SPOTIFY REFRESH TOKEN GENERATOR")
    print("=" * 70)
    print("\n1. Opening your browser to authorize Spotify with recent history scope...")
    print(f"\nIf your browser does not open automatically, visit this URL:\n\n{auth_url}\n")

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    server = HTTPServer(("127.0.0.1", 8000), OAuthCallbackHandler)
    print("Waiting for authorization callback on http://127.0.0.1:8000/callback ...")
    
    server.handle_request()  # Wait for single callback request

    if auth_code:
        token_info = sp_oauth.get_access_token(auth_code, as_dict=True)
        refresh_token = token_info.get("refresh_token")

        print("\n" + "=" * 70)
        print("✓ SUCCESS! REFRESH TOKEN OBTAINED")
        print("=" * 70)
        print(f"\nYour SPOTIPY_REFRESH_TOKEN:\n\n{refresh_token}\n")
        print("Copy this token and add it to your GitHub Repository Secrets:")
        print("  Repo -> Settings -> Secrets and variables -> Actions -> New repository secret")
        print("  Name:  SPOTIPY_REFRESH_TOKEN")
        print("  Value: (paste the token above)")
        print("=" * 70)
    else:
        print("\n[ERROR] Did not receive authorization code.")


if __name__ == "__main__":
    main()

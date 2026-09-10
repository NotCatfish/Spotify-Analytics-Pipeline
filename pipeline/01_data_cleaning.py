# =====================================================================
# STAGE 1: SPOTIFY STREAMING DATA INGESTION & CLEANING PIPELINE
# =====================================================================

# 1. Standard Library (Inbuilt)
import csv
import glob
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time

# 2. Third-Party Libraries
from dotenv import find_dotenv, load_dotenv
import pandas as pd
import requests
from sklearn.preprocessing import MultiLabelBinarizer
from sqlalchemy import create_engine

# --- Initializations & Environment Discovery ---
env_path = find_dotenv(usecwd=True)
if not env_path:
    for candidate in [
        Path.cwd() / "ML_Roadmap" / ".env",
        Path.cwd().parent / "ML_Roadmap" / ".env",
        Path.cwd().parent / ".env"
    ]:
        if candidate.exists():
            env_path = str(candidate)
            break
if env_path:
    load_dotenv(env_path)

if Path.cwd().name == "notebooks" or Path.cwd().name == "pipeline":
    PROJECT_ROOT = Path.cwd().parent
else:
    PROJECT_ROOT = Path.cwd() / "ML_Roadmap" if (Path.cwd() / "ML_Roadmap").exists() else Path.cwd()

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_BASE_NAME = "Cleaned_Spotify_Portable"
DEFAULT_PG_URI = os.getenv("POSTGRES_URI", "postgresql://postgres:password@localhost:5432/postgres")


def load_raw_json(raw_dir=None):
    """Recursively locates and concatenates Spotify Streaming_History_Audio_*.json files."""
    if raw_dir is None:
        search_dirs = [
            DATA_DIR / "raw",
            PROJECT_ROOT / "data" / "raw",
            PROJECT_ROOT.parent,
            PROJECT_ROOT
        ]
        file_paths = []
        for d in search_dirs:
            if d.exists():
                file_paths = glob.glob(str(d / "**/Streaming_History_Audio_*.json"), recursive=True)
                if file_paths:
                    break
    else:
        file_paths = glob.glob(str(Path(raw_dir) / "**/Streaming_History_Audio_*.json"), recursive=True)

    if not file_paths:
        raise FileNotFoundError(
            "Could not locate any 'Streaming_History_Audio_*.json' files. "
            "Please ensure raw Spotify JSON files exist in 'data/raw/'."
        )

    print(f"Found {len(file_paths)} raw streaming history file(s). Ingesting...")
    dfs = [pd.read_json(f) for f in file_paths]
    master_df = pd.concat(dfs, ignore_index=True)
    print(f"Ingested {len(master_df):,} raw stream records.")
    return master_df


def clean_base_dataframe(df):
    """Standardizes columns, converts units, and drops duplicates."""
    print("Standardizing column names and types...")
    df = df.copy()

    # Skip Indicator based on ground truth forward button
    if "reason_end" in df.columns:
        df["skipped"] = (df["reason_end"] == "fwdbtn").astype(int)
    else:
        df["skipped"] = 0

    # Convert ms_played to sec_played
    if "ms_played" in df.columns:
        df["sec_played"] = (df["ms_played"] / 1000).astype(int)
        df = df.drop(columns=["ms_played"])

    rename_map = {
        "master_metadata_track_name": "song_name",
        "master_metadata_album_artist_name": "artist_name",
        "master_metadata_album_album_name": "album_name",
        "ts": "time_stamp",
        "conn_country": "country"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Drop podcast episodes where song_name is null
    df = df.dropna(subset=["song_name", "artist_name"]).reset_index(drop=True)

    # Drop non-music, podcast, audiobook, and privacy-sensitive IP columns
    cols_to_drop = [
        "ip_addr",
        "episode_name",
        "episode_show_name",
        "spotify_episode_uri",
        "audiobook_title",
        "audiobook_uri",
        "audiobook_chapter_uri",
        "audiobook_chapter_title"
    ]
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    # Standardize platform names to clean categories (android, windows, linux, ios, etc.)
    def standardize_platform(val):
        if not isinstance(val, str) or not val.strip():
            return "unknown"
        v = val.lower()
        if "android" in v:
            return "android"
        elif "window" in v:
            return "windows"
        elif "ios" in v or "iphone" in v or "ipad" in v:
            return "ios"
        elif "mac" in v or "darwin" in v or "osx" in v:
            return "macos"
        elif "linux" in v:
            return "linux"
        elif "web" in v:
            return "web"
        elif "unknown" in v:
            return "unknown"
        return "other"

    if "platform" in df.columns:
        df["platform"] = df["platform"].apply(standardize_platform)

    return df


def enrich_with_genres(df):
    """Enriches streaming history with cached Last.fm metadata or API tags."""
    track_cache_path = PROCESSED_DIR / "track_metadata.json"
    artist_cache_path = PROCESSED_DIR / "artist_metadata.json"

    track_cache = {}
    artist_cache = {}

    if track_cache_path.exists():
        with open(track_cache_path, "r", encoding="utf-8") as f:
            try:
                raw_tracks = json.load(f)
                if isinstance(raw_tracks, list):
                    track_cache = {f"{item.get('artist_name', '')}|||{item.get('song_name', '')}": item for item in raw_tracks}
                elif isinstance(raw_tracks, dict):
                    track_cache = raw_tracks
            except Exception:
                track_cache = {}

    if artist_cache_path.exists():
        with open(artist_cache_path, "r", encoding="utf-8") as f:
            try:
                artist_cache = json.load(f)
            except Exception:
                artist_cache = {}

    print(f"Loaded {len(track_cache):,} cached track records and {len(artist_cache):,} cached artist records.")

    # Match genres
    def get_genres(row):
        key = f"{row['artist_name']}|||{row['song_name']}"
        if key in track_cache and track_cache[key].get("genres"):
            return track_cache[key]["genres"]
        if row["artist_name"] in artist_cache and artist_cache[row["artist_name"]]:
            return artist_cache[row["artist_name"]]
        return []

    df["genres"] = df.apply(get_genres, axis=1)

    # MultiLabelBinarizer for genres
    print("Applying MultiLabelBinarizer on genres...")
    df["genres"] = df["genres"].apply(lambda x: x if isinstance(x, list) else [])
    mlb = MultiLabelBinarizer()
    binary_matrix = mlb.fit_transform(df["genres"])
    genres_df = pd.DataFrame(binary_matrix, columns=mlb.classes_).add_prefix("genre_")

    # Combine
    combined_df = pd.concat([df, genres_df], axis=1)

    # Convert booleans
    bool_cols = combined_df.select_dtypes(include=["bool"]).columns
    combined_df[bool_cols] = combined_df[bool_cols].astype(int)

    # Fill NA and compress
    genre_columns = [col for col in combined_df.columns if col.startswith("genre_")]
    compress_cols = genre_columns + [c for c in ["shuffle", "skipped"] if c in combined_df.columns]
    combined_df[compress_cols] = combined_df[compress_cols].fillna(0).astype("int8")

    # Stringify genres column for clean SQL storage
    combined_df["genres"] = combined_df["genres"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    combined_df.drop_duplicates(inplace=True)

    print(f"Cleaned dataset shape: {combined_df.shape[0]:,} rows x {combined_df.shape[1]} columns.")
    return combined_df


def psql_insert_copy(table, conn, keys, data_iter):
    """Streams data into PostgreSQL using high-speed native COPY protocol."""
    dbapi_conn = conn.connection.dbapi_connection
    with dbapi_conn.cursor() as cur:
        s_buf = io.StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)
        columns = ", ".join([f'"{k}"' for k in keys])
        t_name = f'"{table.name}"'
        sql = f"COPY {t_name} ({columns}) FROM STDIN WITH (FORMAT CSV)"
        cur.copy_expert(sql=sql, file=s_buf)


def interactive_export(df):
    """Interactive 2-step prompt for file/table name and storage destination."""
    print("\n--- DATA EXPORT SETUP ---")
    print(f"Directory: {PROCESSED_DIR}")

    # Step 1: File & Table Name
    base_name = None
    while True:
        try:
            name_input = input(f"Enter name for file and table [press Enter for default: {DEFAULT_BASE_NAME}]: ").strip()
            raw_name = name_input or DEFAULT_BASE_NAME
            base_name = raw_name[:-3] if raw_name.lower().endswith(".db") else raw_name
            break
        except (KeyboardInterrupt, EOFError):
            print("\nExport cancelled by user (Escape pressed).")
            return

    db_filename = f"{base_name}.db"
    table_name = base_name
    print(f"File Name : '{db_filename}'")
    print(f"Table Name: '{table_name}'")

    # Step 2: Storage Destination
    print("\nWhere do you want to save the data?")
    print("1: sql (SQLite .db)")
    print("2: postgres (PostgreSQL)")
    print("3: both")

    export_choice = None
    while True:
        try:
            choice_input = input("Where do you want to save the data? (1: sql, 2: postgres, 3: both) [press Enter for default: 1]: ").strip()
            choice = choice_input or "1"
            if choice in ["1", "2", "3"]:
                export_choice = choice
                break
            print("Invalid choice! You must enter 1, 2, or 3. Please try again (or press Esc to cancel).")
        except (KeyboardInterrupt, EOFError):
            print("\nExport cancelled by user (Escape pressed).")
            return

    # SQLite Export
    if export_choice in ["1", "3"]:
        sqlite_path = PROCESSED_DIR / db_filename
        print(f"\nWriting to SQLite at: {sqlite_path} (table: '{table_name}')...")
        try:
            local_conn = sqlite3.connect(sqlite_path)
            local_conn.execute("PRAGMA synchronous = OFF")
            local_conn.execute("PRAGMA journal_mode = MEMORY")
            df.to_sql(table_name, local_conn, if_exists="replace", index=False, chunksize=10000)
            local_conn.execute("VACUUM")
            local_conn.close()
            print(f"Portable SQLite Backup Rebuilt Successfully at: {sqlite_path}")
        except Exception as e:
            print(f"[ERROR] Failed to export to SQLite: {e}")

    # PostgreSQL Export
    if export_choice in ["2", "3"]:
        masked_default = re.sub(r":([^@:/]+)@", ":****@", DEFAULT_PG_URI)
        print("\n--- PostgreSQL Server Export ---")
        print(f"Default URI: {masked_default}")
        print("Press Enter to use default URI, or enter custom URI (or press Esc to cancel).")

        while True:
            try:
                uri_input = input(f"Enter PostgreSQL Connection URI [press Enter for default: {masked_default}]: ").strip()
                postgres_uri = uri_input or DEFAULT_PG_URI
                masked_uri = re.sub(r":([^@:/]+)@", ":****@", postgres_uri)

                print(f"\nConnecting to: {masked_uri}")
                print(f"Writing to PostgreSQL table '{table_name}' using COPY stream...")

                engine = create_engine(postgres_uri)
                df.to_sql(table_name, engine, if_exists="replace", index=False, method=psql_insert_copy)
                engine.dispose()
                print(f"PostgreSQL Server Table '{table_name}' Rebuilt Successfully!")
                break
            except (KeyboardInterrupt, EOFError):
                print("\nPostgreSQL export cancelled by user (Escape pressed).")
                break
            except Exception as e:
                print(f"\n[ERROR] Failed to connect or write to PostgreSQL: {e}")
                print("Tip: Press Enter without typing anything to use the default local PostgreSQL server.")
                print("Format required: postgresql://user:password@localhost:5432/dbname")
                print("Please try again (or press Esc to cancel).\n")


def main():
    print("=" * 70)
    print("STAGE 1: SPOTIFY DATA INGESTION & CLEANING PIPELINE")
    print("=" * 70)

    raw_df = load_raw_json()
    clean_df = clean_base_dataframe(raw_df)
    final_df = enrich_with_genres(clean_df)
    interactive_export(final_df)
    print("\nStage 1 Pipeline Completed Successfully!")


if __name__ == "__main__":
    main()

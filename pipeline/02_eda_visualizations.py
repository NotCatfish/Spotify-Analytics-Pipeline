# =====================================================================
# STAGE 2: SPOTIFY COMPREHENSIVE EDA & REPORT GENERATION PIPELINE
# =====================================================================

# 1. Standard Library
import calendar
import csv
from datetime import datetime
import io
import os
from pathlib import Path
import re
import sqlite3
import sys
import warnings
warnings.filterwarnings("ignore")

# 2. Third-Party Libraries
from dotenv import find_dotenv, load_dotenv
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless file generation
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from sqlalchemy import create_engine, text

# --- Environment & Directory Setup ---
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

REPORTS_DIR = PROJECT_ROOT / "reports"
IMAGES_DIR = REPORTS_DIR / "images"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_BASE_NAME = "Cleaned_Spotify_Portable"
DEFAULT_PG_URI = os.getenv("POSTGRES_URI", "postgresql://postgres:password@localhost:5432/postgres")


def format_time(seconds):
    """Formats raw seconds into human-readable duration strings."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {minutes}m {seconds}s"
    days, hours = divmod(hours, 24)
    if days < 30:
        return f"{days}d {hours}m"
    months, days = divmod(days, 30)
    if months < 12:
        return f"{months}mo {days}d {hours}h"
    year, months = divmod(months, 12)
    return f"{year}y {months}m {days}d"


def get_season(month):
    """Categorizes month into climatic listening seasons."""
    if month in [3, 4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Monsoon"
    else:
        return "Winter"


def categorize_time(time_val):
    """Slices decimal hour into 5 intuitive human quadrants."""
    if 5 <= time_val < 12:
        return "Morning"
    elif 12 <= time_val < 17:
        return "Afternoon"
    elif 17 <= time_val < 19.5:
        return "Evening"
    elif 19.5 <= time_val < 24:
        return "Night"
    else:
        return "Midnight"


def df_to_markdown_fallback(df):
    """Fallback Markdown table generator if tabulate is unavailable."""
    cols = [str(c) for c in df.columns]
    header = "| " + " | ".join(cols) + " |"
    separator = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, r in df.iterrows():
        rows.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join([header, separator] + rows) + "\n"


def log_table(report_file, title, df, top_n=None):
    """Formats DataFrame as a Markdown section and appends to the report file."""
    with open(report_file, "a", encoding="utf-8") as f:
        f.write(f"\n#### {title}\n\n")
        if top_n is not None and len(df) > top_n:
            df_slice = df.head(top_n)
        else:
            df_slice = df
        try:
            f.write(df_slice.to_markdown(index=False) + "\n\n")
        except Exception:
            f.write(df_to_markdown_fallback(df_slice) + "\n\n")


def log_text(report_file, text):
    """Appends Markdown text snippet to report."""
    with open(report_file, "a", encoding="utf-8") as f:
        f.write(f"{text}\n\n")


def log_section(report_file, title, level=2):
    """Appends markdown section header."""
    hashes = "#" * level
    with open(report_file, "a", encoding="utf-8") as f:
        f.write(f"\n{hashes} {title}\n\n")


def apply_japanese_winter_night():
    """Configures matplotlib styling for Japanese Winter Night Aesthetic."""
    plt.rcParams.update({
        "figure.facecolor": "#0D1321",
        "axes.facecolor": "#0D1321",
        "axes.edgecolor": "#3E5C76",
        "axes.labelcolor": "#F0EBD8",
        "xtick.color": "#F0EBD8",
        "ytick.color": "#F0EBD8",
        "grid.color": "#1D2D44",
        "text.color": "#F0EBD8"
    })


def ingest_cleaned_data():
    """Interactive ingestion of cleaned streaming data from SQLite or PostgreSQL."""
    print("\n--- DATA INGESTION SETUP ---")
    print(f"Directory: {PROCESSED_DIR}")

    base_name = None
    is_default_name = False
    while True:
        try:
            name_input = input(f"Enter name of file / table to load [press Enter for default: {DEFAULT_BASE_NAME}]: ").strip()
            if not name_input:
                base_name = DEFAULT_BASE_NAME
                is_default_name = True
            else:
                base_name = name_input[:-3] if name_input.lower().endswith(".db") else name_input
                is_default_name = False
            break
        except (KeyboardInterrupt, EOFError):
            print("\nData loading cancelled by user (Escape pressed).")
            return None

    db_filename = f"{base_name}.db"
    table_name = base_name
    print(f"Target File : '{db_filename}'")
    print(f"Target Table: '{table_name}'")

    print("\nWhere do you want to load data from?")
    print("1: sql (SQLite .db)")
    print("2: postgres (PostgreSQL)")

    source_choice = None
    while True:
        try:
            choice_input = input("Where do you want to load data from? (1: sql, 2: postgres) [press Enter for default: 1]: ").strip()
            choice = choice_input or "1"
            if choice in ["1", "2"]:
                source_choice = choice
                break
            print("Invalid choice! You must enter 1 or 2. Please try again (or press Esc to cancel).")
        except (KeyboardInterrupt, EOFError):
            print("\nData loading cancelled by user (Escape pressed).")
            return None

    master_df = None
    if source_choice == "1":
        while True:
            try:
                db_file = PROCESSED_DIR / db_filename
                if not db_file.exists():
                    if is_default_name and (PROCESSED_DIR / "Cleaned_Spotify_Portable.db").exists():
                        db_file = PROCESSED_DIR / "Cleaned_Spotify_Portable.db"
                    else:
                        print(f"\n[ERROR] File '{db_filename}' does not exist in: {PROCESSED_DIR}")
                        avail = [f.name for f in PROCESSED_DIR.glob("*.db")]
                        if avail:
                            print(f"Available files in directory: {avail}")
                        retry = input(f"Enter valid file name [press Enter for default: {DEFAULT_BASE_NAME}.db]: ").strip()
                        raw = retry or DEFAULT_BASE_NAME
                        base_name = raw[:-3] if raw.lower().endswith(".db") else raw
                        is_default_name = (not retry)
                        db_filename = f"{base_name}.db"
                        table_name = base_name
                        continue

                print(f"\nLoading from SQLite: {db_file}...")
                conn = sqlite3.connect(db_file)
                sqlite_tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

                if table_name in sqlite_tables:
                    target_tbl = table_name
                elif is_default_name and "streaming_history" in sqlite_tables:
                    target_tbl = "streaming_history"
                elif is_default_name and sqlite_tables:
                    target_tbl = sqlite_tables[0]
                else:
                    conn.close()
                    print(f"\n[ERROR] Table '{table_name}' does not exist in '{db_file.name}'! Available: {sqlite_tables}")
                    retry_tbl = input(f"Enter valid table name [press Enter for default: {sqlite_tables[0]}]: ").strip()
                    table_name = retry_tbl or sqlite_tables[0]
                    continue

                master_df = pd.read_sql_query(f'SELECT * FROM "{target_tbl}"', conn)
                conn.close()
                print(f"Loaded {len(master_df):,} rows successfully from SQLite (table: '{target_tbl}')!")
                break
            except (KeyboardInterrupt, EOFError):
                print("\nSQLite load cancelled by user (Escape pressed).")
                return None
            except Exception as e:
                print(f"\n[ERROR] Error reading SQLite database: {e}. Please try again (or press Esc to cancel).\n")

    elif source_choice == "2":
        masked_default = re.sub(r":([^@:/]+)@", ":****@", DEFAULT_PG_URI)
        print("\n--- PostgreSQL Connection Setup ---")
        print(f"Default URI: {masked_default}")
        print("Press Enter to use default URI, or enter custom URI (or press Esc to cancel).")
        while True:
            try:
                uri_input = input(f"Enter PostgreSQL Connection URI [press Enter for default: {DEFAULT_PG_URI}]: ").strip()
                postgres_uri = uri_input or DEFAULT_PG_URI
                masked_uri = re.sub(r":([^@:/]+)@", ":****@", postgres_uri)

                print(f"Connecting to PostgreSQL: {masked_uri}...")
                engine = create_engine(postgres_uri)
                with engine.connect() as check_conn:
                    pg_tables = [r[0] for r in check_conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()]

                if table_name in pg_tables:
                    actual_table = table_name
                elif is_default_name and "streaming_history" in pg_tables:
                    actual_table = "streaming_history"
                else:
                    engine.dispose()
                    def_pg = "streaming_history" if "streaming_history" in pg_tables else (pg_tables[0] if pg_tables else "")
                    print(f"\n[ERROR] Table '{table_name}' does not exist in PostgreSQL public schema! Available: {pg_tables}")
                    retry_tbl = input(f"Enter valid table name [press Enter for default: {def_pg}]: ").strip()
                    table_name = retry_tbl or def_pg
                    is_default_name = (not retry_tbl)
                    continue

                master_df = pd.read_sql_table(actual_table, engine)
                engine.dispose()
                print(f"Loaded {len(master_df):,} rows successfully from PostgreSQL (table: '{actual_table}')!")
                break
            except (KeyboardInterrupt, EOFError):
                print("\nPostgreSQL load cancelled by user (Escape pressed).")
                return None
            except Exception as e:
                print(f"\n[ERROR] Failed to connect: {e}. Please try again (or press Esc to cancel).\n")

    if master_df is not None:
        master_df["time_stamp"] = pd.to_datetime(master_df["time_stamp"])
        if master_df["time_stamp"].dt.tz is None:
            master_df["time_stamp"] = master_df["time_stamp"].dt.tz_localize("UTC")
        master_df["time_stamp"] = master_df["time_stamp"].dt.tz_convert("Asia/Kolkata")
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
        master_df = master_df.drop(columns=[c for c in cols_to_drop if c in master_df.columns])
    return master_df


def ask_top_n():
    """Prompts user ONCE for the top N ranking parameter (artists, songs, genres, albums)."""
    print("\n--- REPORT METRICS CONFIGURATION ---")
    while True:
        try:
            n_input = input("How many top items (artists, songs, genres, albums) do you want in the report? [press Enter for default: 10]: ").strip()
            if not n_input:
                return 10
            n_val = int(n_input)
            if n_val <= 0:
                print("Please enter a positive integer greater than 0.")
                continue
            return n_val
        except ValueError:
            print("Invalid input! Please enter an integer (e.g. 5, 10, 20) or press Enter for default (10).")
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.")
            return None


def run_eda_pipeline(master_df, top_n):
    """Executes Phase 1 Tabular EDA & Phase 2 Visualizations, outputting directly to reports/EDA_Report.md."""
    report_file = REPORTS_DIR / "EDA_Report.md"

    # Initialize Markdown Report
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Comprehensive Spotify Streaming Analysis & Behavioral Insights\n\n")
        f.write(f"> **Generated On:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"> **Total Streams Analyzed:** {len(master_df):,}  \n")
        f.write(f"> **Date Range:** {master_df['time_stamp'].min().strftime('%Y-%m-%d')} to {master_df['time_stamp'].max().strftime('%Y-%m-%d')}  \n")
        f.write(f"> **Top Ranking Filter (N):** {top_n}\n\n")
        f.write("---\n\n")
        f.write("## Table of Contents\n\n")
        f.write("- [Section 1: Core Ranking Charts](#section-1-core-ranking-charts)\n")
        f.write("- [Section 2: Temporal & Behavioral Habits](#section-2-temporal--behavioral-habits)\n")
        f.write("- [Section 3: Engagement & Skip Behavior](#section-3-engagement--skip-behavior)\n")
        f.write("- [Section 4: Technical & Geographic Metrics](#section-4-technical--geographic-metrics)\n")
        f.write("- [Section 5: Niche & Advanced Metrics](#section-5-niche--advanced-metrics)\n")
        f.write("- [Section 6: Visualizations & Analytics Suite](#section-6-visualizations--analytics-suite)\n\n")
        f.write("---\n\n")

    print("\n--- GENERATING COMPREHENSIVE EDA REPORT (MARKDOWN) ---")

    # Ensure Season is present
    master_df["Season"] = master_df["time_stamp"].dt.month.apply(get_season)

    # -------------------------------------------------------------
    # SECTION 1: CORE RANKING CHARTS
    # -------------------------------------------------------------
    print(f"[1/5] Compiling Top Ranking Charts (Artists, Songs, Albums, Genres) (Top {top_n})...")
    log_section(report_file, "Section 1: Core Ranking Charts", level=2)

    # Top Artists
    top_artist_alltime = (
        master_df.groupby("artist_name")
        .agg({'sec_played': 'sum', 'song_name': 'count'})
        .rename(columns={'sec_played': 'total_sec_played', 'song_name': 'play_counts'})
        .reset_index()
    )
    top_artist_alltime["total_time_formatted"] = top_artist_alltime["total_sec_played"].apply(format_time)

    log_table(report_file, f"Top {top_n} Artists of All Time (by Play Counts)", 
              top_artist_alltime.sort_values(by="play_counts", ascending=False)[["artist_name", "play_counts", "total_time_formatted"]], top_n=top_n)
    log_table(report_file, f"Top {top_n} Artists of All Time (by Total Listening Time)", 
              top_artist_alltime.sort_values(by="total_sec_played", ascending=False)[["artist_name", "total_time_formatted", "play_counts"]], top_n=top_n)

    top_artist_yearly = (
        master_df.groupby(["artist_name", master_df["time_stamp"].dt.year])
        .agg({'sec_played': 'sum', 'song_name': 'count'})
        .rename(columns={'sec_played': 'total_sec_played', 'song_name': 'play_counts'})
        .reset_index()
    )
    top_artist_yearly["total_time_formatted"] = top_artist_yearly["total_sec_played"].apply(format_time)
    log_table(report_file, f"Top {top_n} Artists by Year (by Play Counts)",
              top_artist_yearly.sort_values(by=['time_stamp', 'play_counts'], ascending=[True, False]).groupby('time_stamp').head(top_n)[['time_stamp', 'artist_name', 'play_counts', 'total_time_formatted']])

    top_artist_monthly = (
        master_df.groupby(["artist_name", master_df["time_stamp"].dt.to_period("M").rename("Period")])
        .agg({'sec_played': 'sum', 'song_name': 'count'})
        .rename(columns={'sec_played': 'total_sec_played', 'song_name': 'play_counts'})
        .reset_index()
    )
    top_artist_monthly["total_time_formatted"] = top_artist_monthly["total_sec_played"].apply(format_time)

    top_artist_daily = (
        master_df.groupby(["artist_name", master_df["time_stamp"].dt.to_period("D").rename("Period")])
        .agg({'sec_played': 'sum', 'song_name': 'count'})
        .rename(columns={'sec_played': 'total_sec_played', 'song_name': 'play_counts'})
        .reset_index()
    )
    top_artist_daily["total_time_formatted"] = top_artist_daily["total_sec_played"].apply(format_time)

    top_artist_season_year = (
        master_df.groupby(["artist_name", master_df["time_stamp"].dt.year.rename("Year"), "Season"])
        .agg({'sec_played': 'sum', 'song_name': 'count'})
        .rename(columns={'sec_played': 'total_sec_played', 'song_name': 'play_counts'})
        .reset_index()
    )
    top_artist_season_year["total_time_formatted"] = top_artist_season_year["total_sec_played"].apply(format_time)
    log_table(report_file, f"Top {top_n} Artists by Season and Year",
              top_artist_season_year.sort_values(by=["Year", "Season", "play_counts"], ascending=[True, True, False]).groupby(["Year", "Season"]).head(top_n)[["Year", "Season", "artist_name", "play_counts", "total_time_formatted"]])

    # Top Songs
    top_song_alltime = (
        master_df.groupby(["song_name", "artist_name"])
        .agg(total_sec_played=("sec_played", "sum"), play_counts=("song_name", "count"))
        .reset_index()
    )
    top_song_alltime["total_time_formatted"] = top_song_alltime["total_sec_played"].apply(format_time)
    log_table(report_file, f"Top {top_n} Songs of All Time (by Play Counts)",
              top_song_alltime.sort_values(by="play_counts", ascending=False)[["song_name", "artist_name", "play_counts", "total_time_formatted"]], top_n=top_n)

    top_song_yearly = (
        master_df.groupby(["song_name", "artist_name", master_df["time_stamp"].dt.year.rename("Year")])
        .agg(total_sec_played=("sec_played", "sum"), play_counts=("song_name", "count"))
        .reset_index()
    )
    top_song_yearly["total_time_formatted"] = top_song_yearly["total_sec_played"].apply(format_time)
    log_table(report_file, f"Top Songs by Year (Top {top_n})",
              top_song_yearly.sort_values(by=["Year", "play_counts"], ascending=[True, False]).groupby("Year").head(top_n)[["Year", "song_name", "artist_name", "play_counts", "total_time_formatted"]])

    # Top Albums
    top_album_alltime = (
        master_df.groupby(["album_name", "artist_name"])
        .agg(total_sec_played=("sec_played", "sum"), play_counts=("album_name", "count"))
        .reset_index()
    )
    top_album_alltime["total_time_formatted"] = top_album_alltime["total_sec_played"].apply(format_time)
    log_table(report_file, f"Top {top_n} Albums of All Time",
              top_album_alltime.sort_values(by="play_counts", ascending=False)[["album_name", "artist_name", "play_counts", "total_time_formatted"]], top_n=top_n)

    # Most Explored & Most Listened Genres (Dot Product)
    genre_data = [c for c in master_df.columns if c.startswith("genre_")]
    if genre_data:
        genre_alltime = pd.DataFrame({
            "total_seconds": master_df[genre_data].T.dot(master_df["sec_played"]),
            "total_plays": master_df[genre_data].sum(axis=0)
        }).reset_index().rename(columns={"index": "genre"})
        genre_alltime["genre"] = genre_alltime["genre"].str.replace("genre_", "")
        genre_alltime["total_time"] = genre_alltime["total_seconds"].apply(format_time)
        genre_alltime = genre_alltime.sort_values(by="total_seconds", ascending=False)
        log_table(report_file, f"Most Listened Genres All Time (Top {top_n})",
                  genre_alltime[["genre", "total_time", "total_plays"]], top_n=top_n)

    # -------------------------------------------------------------
    # SECTION 2: TEMPORAL & BEHAVIORAL HABITS
    # -------------------------------------------------------------
    print("[2/5] Compiling Temporal & Behavioral Habits...")
    log_section(report_file, "Section 2: Temporal & Behavioral Habits", level=2)

    total_lifetime_sec = master_df["sec_played"].sum()
    log_text(report_file, f"**Total Lifetime Music Listened:** {format_time(total_lifetime_sec)} ({total_lifetime_sec / 3600:,.1f} hours across {len(master_df):,} tracks)")

    # Hours Listened Yearly
    yearly_hours = (
        master_df.groupby(master_df["time_stamp"].dt.year.rename("Year"))
        .agg(total_sec=("sec_played", "sum"), tracks=("song_name", "count"))
        .reset_index()
        .assign(
            total_hours=lambda df: (df["total_sec"] / 3600).round(1),
            total_duration=lambda df: df["total_sec"].apply(format_time)
        )
    )
    log_table(report_file, "Total Listening Volume by Year", yearly_hours[["Year", "total_hours", "total_duration", "tracks"]])

    # Day of Week Distribution
    day_dict = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    dow_df = (
        master_df.groupby(master_df["time_stamp"].dt.day_of_week.rename("Day_Num"))
        .agg(play_counts=("song_name", "count"), total_sec=("sec_played", "sum"))
        .reset_index()
        .assign(Day=lambda df: df["Day_Num"].map(day_dict),
                Hours=lambda df: (df["total_sec"] / 3600).round(1))
    )
    log_table(report_file, "Weekly Listening Distribution (Mon-Sun)", dow_df[["Day", "play_counts", "Hours"]])

    # Days of No Stream & Listening Streaks
    calendar_days = pd.date_range(start=master_df["time_stamp"].min().date(), end=master_df["time_stamp"].max().date()).date
    active_days = set(master_df["time_stamp"].dt.date.unique())
    silent_days = sorted(list(set(calendar_days) - active_days))
    log_text(report_file, f"**Silent Days (No Spotify Activity):** {len(silent_days)} days out of {len(calendar_days)} calendar days ({len(silent_days) / len(calendar_days) * 100:.1f}%)")

    # -------------------------------------------------------------
    # SECTION 3: ENGAGEMENT & SKIP BEHAVIOR
    # -------------------------------------------------------------
    print("[3/5] Compiling Skip & Engagement Patterns...")
    log_section(report_file, "Section 3: Engagement & Skip Behavior", level=2)

    most_skipped_artist = (
        master_df.groupby("artist_name")
        .agg(skip_count=("skipped", "sum"), total_plays=("artist_name", "count"))
        .reset_index()
        .query("total_plays >= 15")
        .assign(skip_percentage=lambda df: (df["skip_count"] / df["total_plays"] * 100).round(1))
        .sort_values(by="skip_percentage", ascending=False)
    )
    log_table(report_file, f"Most Skipped Artists (Min 15 Plays, Top {top_n})", 
              most_skipped_artist[["artist_name", "skip_percentage", "skip_count", "total_plays"]], top_n=top_n)

    # Start and End Reasons
    start_reasons = master_df["reason_start"].value_counts().reset_index()
    start_reasons.columns = ["reason_start", "count"]
    start_reasons["percentage"] = (start_reasons["count"] / len(master_df) * 100).round(2)
    log_table(report_file, "Track Initiation Triggers (reason_start)", start_reasons)

    end_reasons = master_df["reason_end"].value_counts().reset_index()
    end_reasons.columns = ["reason_end", "count"]
    end_reasons["percentage"] = (end_reasons["count"] / len(master_df) * 100).round(2)
    log_table(report_file, "Track Termination Triggers (reason_end)", end_reasons)

    # -------------------------------------------------------------
    # SECTION 4: TECHNICAL & GEOGRAPHIC METRICS
    # -------------------------------------------------------------
    print("[4/5] Compiling Technical & Platform Metrics...")
    log_section(report_file, "Section 4: Technical & Geographic Metrics", level=2)

    platform_stats = (
        master_df.assign(platform_clean=lambda df: df["platform"].astype(str).apply(lambda x: x.split(' ')[0].capitalize()))
        .groupby("platform_clean")
        .agg(plays=("song_name", "count"), total_sec=("sec_played", "sum"))
        .reset_index()
        .assign(hours=lambda df: (df["total_sec"] / 3600).round(1),
                percentage=lambda df: (df["plays"] / len(master_df) * 100).round(1))
        .sort_values(by="plays", ascending=False)
    )
    log_table(report_file, "Device & Platform Market Share", platform_stats[["platform_clean", "plays", "percentage", "hours"]])

    country_col = "country" if "country" in master_df.columns else ("conn_country" if "conn_country" in master_df.columns else None)
    if country_col:
        country_stats = (
            master_df.groupby(country_col)
            .agg(plays=("song_name", "count"))
            .reset_index()
            .rename(columns={country_col: "country"})
            .assign(share=lambda df: (df["plays"] / len(master_df) * 100).round(2))
            .sort_values(by="plays", ascending=False)
        )
        log_table(report_file, f"Geographic Distribution (Top {top_n} Countries)", country_stats, top_n=top_n)

    # -------------------------------------------------------------
    # SECTION 5: NICHE & ADVANCED METRICS
    # -------------------------------------------------------------
    print("[5/5] Compiling Niche & Advanced Metrics...")
    log_section(report_file, "Section 5: Niche & Advanced Metrics", level=2)

    # Monthly Streaks
    artist_months = (
        master_df.assign(year_month=master_df["time_stamp"].dt.to_period("M"))
        .groupby(["artist_name", "year_month"])
        .size()
        .reset_index(name="monthly_plays")
        .sort_values(["artist_name", "year_month"])
    )
    artist_months["prev_month"] = artist_months.groupby("artist_name")["year_month"].shift(1)
    artist_months["is_consecutive"] = (artist_months["year_month"] - artist_months["prev_month"]).apply(lambda x: x.n if pd.notnull(x) else 1) == 1
    artist_months["streak_id"] = (~artist_months["is_consecutive"]).groupby(artist_months["artist_name"]).cumsum()
    longest_artist_streaks = (
        artist_months.groupby(["artist_name", "streak_id"])
        .agg(consecutive_months=("year_month", "count"), start_month=("year_month", "min"), end_month=("year_month", "max"))
        .reset_index()
        .sort_values(by="consecutive_months", ascending=False)
    )
    log_table(report_file, f"Longest Uninterrupted Monthly Artist Streaks (Top {top_n})",
              longest_artist_streaks[["artist_name", "consecutive_months", "start_month", "end_month"]], top_n=top_n)

    # One-Hit Wonders
    one_hit_wonders = (
        master_df.groupby("artist_name")
        .agg(unique_songs=("song_name", "nunique"), total_plays=("artist_name", "count"))
        .reset_index()
        .query("unique_songs == 1")
        .sort_values(by="total_plays", ascending=False)
    )
    log_table(report_file, f"Top {top_n} One-Hit Wonders (Single Track Looped to Death)", one_hit_wonders, top_n=top_n)

    # Quickest Skipped Artists
    attention_span = (
        master_df.assign(skipped_sec_played=lambda x: x["sec_played"].where(x["skipped"] == 1))
        .groupby("artist_name")
        .agg(median_skip_sec=("skipped_sec_played", "median"), total_skips=("skipped", "sum"))
        .reset_index()
        .query("total_skips >= 15")
        .sort_values(by="median_skip_sec", ascending=True)
    )
    log_table(report_file, f"Quickest Skipped Artists (Shortest Median Seconds Before Skip, Top {top_n})", attention_span, top_n=top_n)

    # Listening Marathons (30-min inactivity session definition)
    marathons = (
        master_df.sort_values(by="time_stamp")
        .assign(
            time_gap=lambda x: x["time_stamp"].diff(),
            new_session=lambda x: x["time_gap"] > pd.Timedelta(minutes=30),
            session_id=lambda x: x["new_session"].cumsum()
        )
        .groupby("session_id")
        .agg(
            session_start=("time_stamp", "min"),
            session_end=("time_stamp", "max"),
            total_sec_played=("sec_played", "sum"),
            songs_played=("song_name", "count")
        )
        .assign(total_hours_listened=lambda x: (x["total_sec_played"] / 3600).round(2))
        .sort_values(by="total_hours_listened", ascending=False)
    )
    log_table(report_file, f"Top {top_n} Longest Continuous Listening Marathons",
              marathons[["session_start", "session_end", "total_hours_listened", "songs_played"]], top_n=top_n)

    print(f"EDA tabular sections compiled successfully into: {report_file}")

    # Return variables needed for Phase 2 Visualizations
    return {
        "top_artist_yearly": top_artist_yearly,
        "top_artist_season_year": top_artist_season_year,
        "one_hit_wonders": one_hit_wonders,
        "longest_artist_streaks": longest_artist_streaks
    }


def run_visualizations_pipeline(master_df, eda_vars):
    """Generates all 21 aesthetic figures and embeds them with commentary in reports/EDA_Report.md."""
    report_file = REPORTS_DIR / "EDA_Report.md"
    log_section(report_file, "Section 6: Visualizations & Analytics Suite", level=2)
    log_text(report_file, "*All 21 charts below have been rendered using the Japanese Winter Night aesthetic palette (`#0D1321` midnight indigo, electric cyan `#38bdf8`, icy mint `#81C784`, and coral `#FCA5A5`).*")

    apply_japanese_winter_night()

    print("\n--- GENERATING VISUALIZATIONS (21 PLOTS) ---")

    top_artist_yearly = eda_vars["top_artist_yearly"]
    top_artist_season_year = eda_vars["top_artist_season_year"]
    one_hit_wonders = eda_vars["one_hit_wonders"]
    longest_artist_streaks = eda_vars["longest_artist_streaks"]

    # -------------------------------------------------------------
    # 1. Phases of Listening Over The Years
    # -------------------------------------------------------------
    print("[01/21] Generating: Phases of Listening Over The Years...")
    top_3_artist_each_year = (
        top_artist_yearly
        .sort_values(by=["time_stamp", "play_counts"], ascending=[True, False])
        .groupby("time_stamp")
        .head(3)
        .rename(columns={"time_stamp": "Year"})
    )
    g = sns.catplot(
        data=top_3_artist_each_year,
        kind="bar",
        col="Year",
        col_wrap=3,
        y="artist_name",
        x="play_counts",
        hue="artist_name",
        sharey=False,
        sharex=False,
        height=3,
        aspect=1.5,
        palette="cool"
    )
    g.set_titles("{col_name}", size=12, weight="bold")
    g.set_axis_labels("", "")
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_01_phases_of_listening.png"
    g.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close(g.fig)
    log_section(report_file, "1. Phases of Listening Over The Years", level=3)
    log_text(report_file, f"![Phases of Listening Over The Years](images/{img_path.name})\n\n*Mini-podiums highlighting the top 3 artists defining each year of your listening journey.*")

    # -------------------------------------------------------------
    # 2. Artist Discovery Funnel
    # -------------------------------------------------------------
    print("[02/21] Generating: Artist Discovery Funnel...")
    discovery_method = (
        master_df[["time_stamp", "artist_name", "reason_start"]]
        .sort_values(by="time_stamp")
        .groupby("artist_name")
        .first()
        .reset_index()
        .assign(
            discovery_quarter=lambda df: df["time_stamp"].dt.year.astype(str) + "-Q" + df["time_stamp"].dt.quarter.astype(str)
        )
        .groupby(["discovery_quarter", "reason_start"])["artist_name"]
        .count()
        .reset_index(name="new_artists")
        .query("reason_start in ['clickrow', 'trackdone', 'fwdbtn']")
    )
    plt.figure(figsize=(15, 6))
    sns.lineplot(
        data=discovery_method, 
        x="discovery_quarter", 
        y="new_artists", 
        hue="reason_start", 
        linewidth=3,
        palette={"clickrow": "#38bdf8", "trackdone": "#FCA5A5", "fwdbtn": "#FCD34D"}
    )
    plt.title("Artist Discovery Funnel: How New Music Enters Your Library Across Quarters", pad=15, fontsize=14)
    plt.xlabel("Quarter", fontsize=12)
    plt.ylabel("New Artists Discovered", fontsize=12)
    plt.xticks(rotation=45)
    plt.legend(title="Discovery Trigger", frameon=False)
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_02_artist_discovery_funnel.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "2. Artist Discovery Funnel", level=3)
    log_text(report_file, f"![Artist Discovery Funnel](images/{img_path.name})\n\n*Tracks the very first time new artists entered your life across quarters (Active search vs. Algorithmic autoplay).*")

    # -------------------------------------------------------------
    # 3. The 5 Quadrants of Listening
    # -------------------------------------------------------------
    print("[03/21] Generating: The 5 Quadrants of Listening...")
    time_float = master_df["time_stamp"].dt.hour + master_df["time_stamp"].dt.minute / 60
    bar_chart_data = time_float.apply(categorize_time).value_counts().reset_index()
    bar_chart_data.columns = ["time_category", "play_counts"]

    plt.figure(figsize=(10, 6))
    ax = sns.barplot(
        data=bar_chart_data, 
        x="time_category", 
        y="play_counts", 
        hue="time_category",
        legend=False,
        palette="twilight_shifted",
        order=["Morning", "Afternoon", "Evening", "Night", "Midnight"],
        edgecolor="#111827",
        linewidth=1.2
    )
    for container in ax.containers:
        ax.bar_label(container, fmt='%d', padding=4, color='white', fontweight='bold')
    plt.title("Circadian Rhythms: Total Listening Volume Across 5 Day-Quadrants", pad=15, fontsize=14)
    plt.xlabel("Time of Day", fontsize=12)
    plt.ylabel("Total Plays", fontsize=12)
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_03_5_quadrants_of_listening.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "3. The 5 Quadrants of Listening", level=3)
    log_text(report_file, f"![The 5 Quadrants of Listening](images/{img_path.name})\n\n*Listening volume segmented into circadian quadrants (Morning, Afternoon, Evening, Night, Midnight).*")

    # -------------------------------------------------------------
    # 4. Seasonal Vibes
    # -------------------------------------------------------------
    print("[04/21] Generating: Seasonal Vibes...")
    all_years = sorted(top_artist_season_year["Year"].unique())
    month_weights = {"Summer": 3, "Monsoon": 4, "Winter": 5}
    n_years = len(all_years)
    fig, axes = plt.subplots(1, n_years, figsize=(6 * n_years, 5), sharey=False)
    if n_years == 1:
        axes = [axes]
    for ax, year in zip(axes, all_years):
        year_df = top_artist_season_year[top_artist_season_year["Year"] == year]
        top_artists = year_df.groupby("artist_name")["play_counts"].sum().nlargest(5).index.tolist()
        filtered_year_df = (
            year_df[year_df["artist_name"].isin(top_artists)]
            .assign(normalized_plays=lambda df: df["play_counts"] / df["Season"].map(month_weights))
        )
        pivot_grid = (
            filtered_year_df.pivot(index="artist_name", columns="Season", values="normalized_plays")
            .reindex(columns=["Summer", "Monsoon", "Winter"])
            .fillna(0)
        )
        sns.heatmap(
            data=pivot_grid, 
            cmap="mako", 
            annot=True, 
            fmt=".1f",
            linewidths=0.5,
            linecolor="#111827",
            cbar_kws={'label': 'Avg Plays / Month'},
            ax=ax
        )
        ax.set_title(f"Seasonal Vibes ({year})", pad=12, fontsize=12)
        ax.set_xlabel("Season", fontsize=10)
        ax.set_ylabel("")
    plt.tight_layout()
    img_path = IMAGES_DIR / "chart_04_seasonal_vibes.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "4. Seasonal Vibes Heatmaps", level=3)
    log_text(report_file, f"![Seasonal Vibes Heatmaps](images/{img_path.name})\n\n*Normalized monthly intensity across Summer, Monsoon, and Winter for each year.*")

    # -------------------------------------------------------------
    # 5. The One-Hit Wonder Wall of Fame
    # -------------------------------------------------------------
    print("[05/21] Generating: The One-Hit Wonder Wall of Fame...")
    top_15_one_hits = one_hit_wonders.sort_values(by="total_plays", ascending=False).head(15)
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(
        data=top_15_one_hits, 
        x="total_plays", 
        y="artist_name", 
        hue="artist_name", 
        palette="magma",
        legend=False,
        edgecolor="#111827",
        linewidth=1.2
    )
    for container in ax.containers:
        ax.bar_label(container, fmt='%d plays', padding=6, color='white', fontweight='bold')
    plt.title("The One-Hit Wonder Wall of Fame: Highest Plays on Exactly 1 Unique Track", pad=15, fontsize=14)
    plt.xlabel("Total Times Played", fontsize=12)
    plt.ylabel("")
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_05_one_hit_wonder_wall_of_fame.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "5. The One-Hit Wonder Wall of Fame", level=3)
    log_text(report_file, f"![One-Hit Wonder Wall of Fame](images/{img_path.name})\n\n*Artists where a single track was looped excessively without exploring any other songs by the artist.*")

    # -------------------------------------------------------------
    # 6. Artist Loyalty Streaks
    # -------------------------------------------------------------
    print("[06/21] Generating: Artist Loyalty Streaks...")
    top_streaks = longest_artist_streaks.head(15)
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(
        data=top_streaks, 
        x="consecutive_months", 
        y="artist_name", 
        hue="artist_name", 
        palette="crest",
        legend=False,
        edgecolor="#111827",
        linewidth=1.2
    )
    for container in ax.containers:
        ax.bar_label(container, fmt='%d mos', padding=6, color='white', fontweight='bold')
    plt.title("Ultimate Loyalty: Longest Consecutive Monthly Listening Streaks", pad=15, fontsize=14)
    plt.xlabel("Consecutive Months Listened", fontsize=12)
    plt.ylabel("")
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_06_artist_loyalty_streaks.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "6. Artist Loyalty Streaks", level=3)
    log_text(report_file, f"![Artist Loyalty Streaks](images/{img_path.name})\n\n*Unbroken consecutive monthly listening streaks representing unwavering artist loyalty.*")

    # -------------------------------------------------------------
    # 7. Weekend vs. Weekday Shift
    # -------------------------------------------------------------
    print("[07/21] Generating: The Weekend vs. Weekday Shift...")
    day_counts = master_df['time_stamp'].dt.day_name().value_counts().reset_index()
    day_counts.columns = ['day_name', 'play_counts']
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    custom_palette = {
        "Monday": "#374151", "Tuesday": "#374151", "Wednesday": "#374151",
        "Thursday": "#374151", "Friday": "#374151", "Saturday": "#00B4D8", "Sunday": "#00B4D8"
    }
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(
        data=day_counts, 
        x="day_name", 
        y="play_counts", 
        order=day_order,
        hue="day_name", 
        palette=custom_palette, 
        legend=False,
        edgecolor="#111827",
        linewidth=1.2
    )
    for container in ax.containers:
        ax.bar_label(container, fmt='%d', padding=5, color='white', fontweight='bold')
    plt.title("The Weekend Surge: Total Play Volume Across the Week", pad=15, fontsize=14)
    plt.ylabel("Total Songs Played", fontsize=12)
    plt.xlabel("")
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_07_weekend_vs_weekday_shift.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "7. Weekend vs. Weekday Shift", level=3)
    log_text(report_file, f"![Weekend vs Weekday Shift](images/{img_path.name})\n\n*Contrasting daily listening load between workday focus and weekend leisure surges.*")

    # -------------------------------------------------------------
    # 8. The Attention Span Decay
    # -------------------------------------------------------------
    print("[08/21] Generating: The Attention Span Decay...")
    attention_decay = (
        master_df.loc[(master_df['reason_end'] == 'fwdbtn') & (master_df['sec_played'] <= 630)]
        .groupby(master_df['time_stamp'].dt.year)['sec_played']
        .agg(total_sec='sum', skip_count='count')
        .reset_index()
        .assign(avg_seconds_before_skip=lambda df: df['total_sec'] / df['skip_count'])
    )
    plt.figure(figsize=(12, 6))
    sns.lineplot(
        data=attention_decay,
        x="time_stamp",
        y="avg_seconds_before_skip",
        color="#00B4D8",
        linewidth=4,
        marker="o",
        markersize=10,
        markerfacecolor="#00B4D8",
        markeredgecolor="white",
        markeredgewidth=1.5
    )
    plt.title("The Attention Span Decay: How Many Seconds You Give a Song Before Hitting 'Next'", pad=15, fontsize=14)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Avg Seconds Before Skip", fontsize=12)
    plt.xticks(attention_decay["time_stamp"])
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_08_attention_span_decay.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "8. The Attention Span Decay", level=3)
    log_text(report_file, f"![Attention Span Decay](images/{img_path.name})\n\n*Tracking shrinking patience and faster skip triggers over the years.*")

    # -------------------------------------------------------------
    # 9. The Skip-Trigger Heatmap
    # -------------------------------------------------------------
    print("[09/21] Generating: The Skip-Trigger Heatmap...")
    skip_heatmap_data = (
        pd.crosstab(
            master_df.loc[master_df['reason_end'] == 'fwdbtn', 'time_stamp'].dt.day_name().rename("Day"), 
            master_df.loc[master_df['reason_end'] == 'fwdbtn', 'time_stamp'].dt.hour.rename("Hour"),
            normalize='index'
        ) * 100
    ).reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    plt.figure(figsize=(14, 7))
    sns.heatmap(skip_heatmap_data, cmap="rocket", annot=False, cbar_kws={'label': '% of Daily Skips'})
    plt.title("The Skip-Trigger Heatmap: At What Hour Are You Most Impatient with Music?", pad=15, fontsize=14)
    plt.xlabel("Hour of the Day (0-23)", fontsize=12)
    plt.ylabel("")
    plt.yticks(rotation=0)
    img_path = IMAGES_DIR / "chart_09_skip_trigger_heatmap.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "9. The Skip-Trigger Heatmap", level=3)
    log_text(report_file, f"![Skip-Trigger Heatmap](images/{img_path.name})\n\n*Hourly skip rate intensity across the week, pinpointing moments of musical impatience.*")

    # -------------------------------------------------------------
    # 10. The Binge Metric (Piecewise Scale)
    # -------------------------------------------------------------
    print("[10/21] Generating: The Binge Metric (Piecewise Scale)...")
    binge_sessions = (
        master_df[["time_stamp", "sec_played"]]
        .sort_values("time_stamp")
        .assign(
            gap=lambda df: (df["time_stamp"] - pd.to_timedelta(df["sec_played"], unit="s")) - df["time_stamp"].shift(1),
            is_new_session=lambda df: df["gap"] > pd.Timedelta(minutes=15)
        )
        .assign(session_id=lambda df: df["is_new_session"].cumsum())
        .groupby("session_id")
        .agg(session_hours=("sec_played", lambda x: x.sum() / 3600))
        .query("session_hours >= 1")
    )
    binge_discrete = binge_sessions.assign(rounded_hours=lambda df: df["session_hours"].round().astype(int))
    counts = binge_discrete['rounded_hours'].value_counts().sort_index()

    def custom_piecewise_scale(y_vals):
        transformed = []
        for y in y_vals:
            if y == 0: transformed.append(-0.1)
            elif y <= 10: transformed.append((y - 1) / 9.0)
            elif y <= 100: transformed.append(1 + (y - 10) / 90.0)
            elif y <= 1000: transformed.append(2 + (y - 100) / 900.0)
            else: transformed.append(3 + (y - 1000) / 9000.0)
        return transformed

    y_transformed = custom_piecewise_scale(counts.values)
    plt.figure(figsize=(12, 8))
    plt.bar(counts.index, y_transformed, color="#38bdf8", edgecolor="#111827", linewidth=1.5)
    ax = plt.gca()
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_yticklabels(["1", "10", "100", "1000", "10,000"], fontsize=12, fontweight='bold', color='white')
    ax.grid(axis='y', which='major', color='#374151', linestyle='-', linewidth=1.5)
    plt.title("The Binge Metric: Uninterrupted Sessions (Piecewise Linear Scale)", pad=15, fontsize=14)
    plt.xlabel("Continuous Listening Duration (Hours)", fontsize=12)
    plt.ylabel("Session Count", fontsize=12)
    sns.despine(left=True, bottom=True)
    plt.xticks(counts.index)
    img_path = IMAGES_DIR / "chart_10_binge_metric_piecewise.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "10. The Binge Metric (Piecewise Scale)", level=3)
    log_text(report_file, f"![Binge Metric Piecewise](images/{img_path.name})\n\n*Custom mathematical compression scaling long-tail listening marathons from 1 to 10,000 sessions.*")

    # -------------------------------------------------------------
    # 11. The Binge Metric (Log Scale)
    # -------------------------------------------------------------
    print("[11/21] Generating: The Binge Metric (Log Scale)...")
    plt.figure(figsize=(10, 6))
    sns.countplot(data=binge_discrete, x="rounded_hours", color="#38bdf8", edgecolor="#111827", linewidth=1.5)
    plt.yscale("log")
    plt.title("The Binge Metric: Uninterrupted Sessions (Clean Log Scale)", pad=15, fontsize=14)
    plt.xlabel("Continuous Listening Duration (Hours)", fontsize=12)
    plt.ylabel("Total Sessions", fontsize=12)
    sns.despine(left=True, bottom=True)
    plt.xticks(range(len(counts)))
    img_path = IMAGES_DIR / "chart_11_binge_metric_log.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "11. The Binge Metric (Log Scale)", level=3)
    log_text(report_file, f"![Binge Metric Log Scale](images/{img_path.name})\n\n*Logarithmic distribution of continuous multi-hour listening binges.*")

    # -------------------------------------------------------------
    # 12. Cloud Auto-Scaling & Traffic Heatmap
    # -------------------------------------------------------------
    print("[12/21] Generating: Cloud Auto-Scaling & Traffic Heatmap...")
    traffic_data = (
        master_df[["time_stamp"]]
        .assign(day_name=lambda df: df["time_stamp"].dt.day_name(), hour=lambda df: df["time_stamp"].dt.hour)
        .groupby(["day_name", "hour"])
        .size()
        .reset_index(name="play_volume")
    )
    traffic_pivot = traffic_data.pivot(index="day_name", columns="hour", values="play_volume").reindex(day_order)
    plt.figure(figsize=(16, 8))
    sns.heatmap(data=traffic_pivot, cmap="mako", linewidths=0.5, linecolor="#111827", annot=False, cbar_kws={'label': 'Total Play Volume'})
    plt.title("Cloud Auto-Scaling: Global Traffic Heatmap by Day and Hour", pad=20, fontsize=14)
    plt.xlabel("Hour of Day (24h Clock)", fontsize=12)
    plt.ylabel("")
    plt.yticks(rotation=0, fontsize=11)
    plt.xticks(fontsize=11)
    img_path = IMAGES_DIR / "chart_12_cloud_autoscaling_traffic_heatmap.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "12. Cloud Auto-Scaling Traffic Heatmap", level=3)
    log_text(report_file, f"![Cloud Auto-Scaling Heatmap](images/{img_path.name})\n\n*168-hour weekly load heatmap demonstrating traffic concurrency peaks for cloud infrastructure planning.*")

    # -------------------------------------------------------------
    # 13. The Micro-Buffering Threshold
    # -------------------------------------------------------------
    print("[13/21] Generating: The Micro-Buffering Threshold...")
    true_skips = master_df[["sec_played", "reason_end"]].query("reason_end == 'fwdbtn'")
    total_skips = max(len(true_skips), 1)
    pct_5s = len(true_skips.query("sec_played <= 5")) / total_skips
    pct_15s = len(true_skips.query("sec_played <= 15")) / total_skips
    pct_30s = len(true_skips.query("sec_played <= 30")) / total_skips

    plt.figure(figsize=(14, 7))
    sns.ecdfplot(data=true_skips, x="sec_played", color="#38bdf8", linewidth=3)
    plt.axvline(x=5, ymax=pct_5s, color="#FCA5A5", linestyle="--", alpha=0.8)
    plt.axhline(y=pct_5s, xmax=5/240, color="#FCA5A5", linestyle="--", alpha=0.8)
    plt.text(7, pct_5s - 0.05, f"5s: {pct_5s:.1%}", color="#FCA5A5", fontweight="bold")
    plt.axvline(x=15, ymax=pct_15s, color="#FCD34D", linestyle="--", alpha=0.8)
    plt.axhline(y=pct_15s, xmax=15/240, color="#FCD34D", linestyle="--", alpha=0.8)
    plt.text(17, pct_15s - 0.05, f"15s: {pct_15s:.1%}", color="#FCD34D", fontweight="bold")
    plt.axvline(x=30, ymax=pct_30s, color="#6EE7B7", linestyle="--", alpha=0.8)
    plt.axhline(y=pct_30s, xmax=30/240, color="#6EE7B7", linestyle="--", alpha=0.8)
    plt.text(32, pct_30s - 0.05, f"30s: {pct_30s:.1%}", color="#6EE7B7", fontweight="bold")
    plt.title("The Micro-Buffering Threshold: Cumulative Skip Percentage Over Time", pad=20, fontsize=14)
    plt.xlabel("Seconds Played Before Skipping", fontsize=12)
    plt.ylabel("Cumulative Proportion of Skips", fontsize=12)
    plt.xlim(0, 240)
    plt.ylim(0, 1.05)
    plt.grid(color="#1F2937", linestyle="--", alpha=0.5)
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_13_micro_buffering_threshold.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "13. The Micro-Buffering Threshold", level=3)
    log_text(report_file, f"![Micro-Buffering Threshold](images/{img_path.name})\n\n*Empirical CDF curve revealing where CDN edge servers should halt audio chunk pre-fetching to prevent bandwidth loss.*")

    # -------------------------------------------------------------
    # 14. Cloud Bandwidth & Cache Waste
    # -------------------------------------------------------------
    print("[14/21] Generating: Cloud Bandwidth & Cache Waste...")
    TRUE_MB_PER_TRACK = 4.3 
    true_bandwidth_data = (
        master_df[["reason_end"]]
        .assign(
            traffic_type=lambda df: np.select(
                [df["reason_end"] == "fwdbtn", df["reason_end"] == "trackdone"],
                ["Wasted Bandwidth (Skipped)", "Effective Bandwidth (Completed)"],
                default="Other (Paused/Closed)"
            )
        )
        .groupby("traffic_type")
        .size()
        .reset_index(name="track_count")
        .assign(total_gb=lambda df: (df["track_count"] * TRUE_MB_PER_TRACK) / 1024)
        .sort_values("total_gb", ascending=False)
    )
    plt.figure(figsize=(10, 5))
    ax = sns.barplot(
        data=true_bandwidth_data,
        x="total_gb",
        y="traffic_type",
        palette={"Effective Bandwidth (Completed)": "#38bdf8", "Wasted Bandwidth (Skipped)": "#FCA5A5", "Other (Paused/Closed)": "#4B5563"},
        hue="traffic_type",
        legend=False,
        edgecolor="#111827",
        linewidth=1.5
    )
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f GB', padding=5, color='white', fontweight='bold')
    plt.title("Cloud Infrastructure Cost: Total Bandwidth Wasted vs. Actually Consumed", pad=20, fontsize=14)
    plt.xlabel("Total Data Transferred (Gigabytes) @ 4.3 MB Pre-fetch Penalty", fontsize=12)
    plt.ylabel("")
    plt.grid(axis='x', color="#1F2937", linestyle="--", alpha=0.5)
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_14_cloud_bandwidth_cache_waste.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "14. Cloud Bandwidth & Cache Waste", level=3)
    log_text(report_file, f"![Cloud Bandwidth & Cache Waste](images/{img_path.name})\n\n*Calculates exact egress network volume consumed on finished tracks vs. squandered on early skips.*")

    # -------------------------------------------------------------
    # 15. Hardware Dominance
    # -------------------------------------------------------------
    print("[15/21] Generating: Hardware Dominance...")
    hardware_data = (
        master_df[["platform", "sec_played"]]
        .assign(platform_clean=lambda df: df["platform"].astype(str).apply(lambda x: x.split(' ')[0].capitalize()))
        .groupby("platform_clean", as_index=False)
        .agg(total_hours=("sec_played", lambda x: x.sum() / 3600))
        .sort_values("total_hours", ascending=False)
    )
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=hardware_data, x="total_hours", y="platform_clean", color="#38bdf8", edgecolor="#111827", linewidth=1.5)
    for container in ax.containers:
        ax.bar_label(container, fmt='%.0f hrs', padding=6, color='white', fontweight='bold')
    plt.title("Hardware Dominance: Where Does Your Music Actually Live?", pad=20, fontsize=14)
    plt.xlabel("Total Listening Time (Hours)", fontsize=12)
    plt.ylabel("Platform", fontsize=12)
    plt.grid(axis='x', color="#1F2937", linestyle="--", alpha=0.5)
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_15_hardware_dominance.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "15. Hardware Dominance", level=3)
    log_text(report_file, f"![Hardware Dominance](images/{img_path.name})\n\n*Operating system breakdown across total lifetime listening hours.*")

    # -------------------------------------------------------------
    # 16. Platform Engagement & Completion Ratios
    # -------------------------------------------------------------
    print("[16/21] Generating: Platform Engagement & Completion Ratios...")
    engagement_data = (
        master_df[["platform", "reason_end"]]
        .assign(
            traffic_type=lambda df: np.select(
                [df["reason_end"] == "fwdbtn", df["reason_end"] == "trackdone"],
                ["Skipped", "Completed"],
                default="Other"
            ),
            platform_clean=lambda df: df["platform"].astype(str).apply(lambda x: x.split(' ')[0].capitalize())
        )
        .groupby(["platform_clean", "traffic_type"])
        .size()
        .unstack(fill_value=0)
    )
    engagement_ratio = engagement_data.div(engagement_data.sum(axis=1), axis=0) * 100
    if "Completed" in engagement_ratio.columns:
        engagement_ratio = engagement_ratio.sort_values(by="Completed", ascending=False)
    color_dict = {"Completed": "#38bdf8", "Skipped": "#FCA5A5", "Other": "#4B5563"}
    plot_colors = [color_dict.get(col, "#ffffff") for col in engagement_ratio.columns]

    ax = engagement_ratio.plot(kind="barh", stacked=True, color=plot_colors, edgecolor="#111827", linewidth=1.5, figsize=(12, 6))
    for container in ax.containers:
        labels = [f"{val:.0f}%" if val > 5 else "" for val in container.datavalues]
        ax.bar_label(container, labels=labels, label_type='center', color='black', fontweight='bold')
    plt.title("Hardware Engagement: Song Completion vs. Skip Rate by Platform", pad=20, fontsize=14)
    plt.xlabel("Share of Streams (%)", fontsize=12)
    plt.ylabel("Platform", fontsize=12)
    plt.legend(title="Outcome", bbox_to_anchor=(1.01, 1), loc='upper left', frameon=False, title_fontsize=11)
    plt.xlim(0, 100)
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_16_platform_engagement_ratios.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "16. Platform Engagement Ratios", level=3)
    log_text(report_file, f"![Platform Engagement Ratios](images/{img_path.name})\n\n*100% stacked bar chart revealing focus vs. restlessness across devices.*")

    # -------------------------------------------------------------
    # 17. The Stream Lifecycle Funnel (Plotly Sankey)
    # -------------------------------------------------------------
    print("[17/21] Generating: The Stream Lifecycle Funnel (Sankey)...")
    try:
        df_sankey = master_df.assign(
            stage1=lambda df: "Device: " + df["platform"].astype(str).apply(lambda x: x.split(' ')[0].capitalize()),
            stage2=lambda df: "Start: " + df["reason_start"].astype(str),
            stage3=lambda df: "End: " + df["reason_end"].astype(str)
        )
        flow1 = df_sankey.groupby(["stage1", "stage2"]).size().reset_index(name="count")
        flow1.columns = ["source_name", "target_name", "count"]
        flow2 = df_sankey.groupby(["stage2", "stage3"]).size().reset_index(name="count")
        flow2.columns = ["source_name", "target_name", "count"]
        flow_data = pd.concat([flow1, flow2])
        flow_data = flow_data[flow_data["count"] >= (len(master_df) * 0.01)]

        all_nodes = list(pd.unique(flow_data[["source_name", "target_name"]].values.ravel('K')))
        node_dict = {name: i for i, name in enumerate(all_nodes)}
        flow_data = flow_data.assign(
            source_idx=lambda df: df["source_name"].map(node_dict),
            target_idx=lambda df: df["target_name"].map(node_dict)
        )

        fig = go.Figure(data=[go.Sankey(
            arrangement="snap",
            node=dict(
                pad=25,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color="#38bdf8"
            ),
            link=dict(
                source=flow_data["source_idx"],
                target=flow_data["target_idx"],
                value=flow_data["count"],
                color="rgba(56, 189, 248, 0.3)"
            )
        )])
        fig.update_layout(
            title_text="The Stream Lifecycle Funnel: Device -> Action -> Final Outcome",
            title_font_size=18,
            font_size=13,
            paper_bgcolor='#0D1321',
            plot_bgcolor='#0D1321',
            font_color='white',
            height=700
        )
        img_path = IMAGES_DIR / "chart_17_stream_lifecycle_sankey.png"
        fig.write_image(str(img_path), scale=2)
        fig.write_html(str(IMAGES_DIR / "chart_17_stream_lifecycle_sankey.html"))
        log_section(report_file, "17. The Stream Lifecycle Funnel (Sankey)", level=3)
        log_text(report_file, f"![Stream Lifecycle Funnel](images/{img_path.name})\n\n*End-to-end stream path routing client device -> play trigger -> final termination outcome. An interactive HTML version is also saved in `images/chart_17_stream_lifecycle_sankey.html`.*")
    except Exception as e:
        print(f"  [Notice] Sankey static image generation bypassed: {e}")

    # -------------------------------------------------------------
    # 18. The Autoplay Reliance Engine
    # -------------------------------------------------------------
    print("[18/21] Generating: The Autoplay Reliance Engine...")
    autoplay_data = (
        master_df[["time_stamp", "reason_start"]]
        .assign(
            year_month=lambda df: df["time_stamp"].dt.to_period("M"),
            is_passive=lambda df: (df["reason_start"] == "trackdone").astype(int)
        )
        .groupby("year_month")
        .agg(total_streams=("is_passive", "count"), passive_streams=("is_passive", "sum"))
        .assign(passive_ratio=lambda df: (df["passive_streams"] / df["total_streams"]) * 100)
        .reset_index()
    )
    autoplay_data["year_month"] = autoplay_data["year_month"].dt.to_timestamp()
    autoplay_data["smooth_ratio"] = autoplay_data["passive_ratio"].rolling(window=3, min_periods=1).mean()

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=autoplay_data, x="year_month", y="smooth_ratio", color="#38bdf8", linewidth=3)
    plt.fill_between(autoplay_data["year_month"], autoplay_data["smooth_ratio"], color="#38bdf8", alpha=0.15)
    plt.title("The Autoplay Reliance Engine: The Rise of Algorithmic Passive Listening", pad=20, fontsize=15)
    plt.xlabel("Timeline", fontsize=12)
    plt.ylabel("Passive Listening Ratio (%)", fontsize=12)
    plt.ylim(0, 100)
    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.grid(color="#1F2937", linestyle="--", alpha=0.5)
    sns.despine(left=True, bottom=True)
    img_path = IMAGES_DIR / "chart_18_autoplay_reliance_engine.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "18. The Autoplay Reliance Engine", level=3)
    log_text(report_file, f"![Autoplay Reliance Engine](images/{img_path.name})\n\n*3-month smoothed ratio of algorithmic autoplay (`trackdone`) vs. conscious track selections.*")

    # -------------------------------------------------------------
    # 19. UI Feature Breakdown (Donut Chart)
    # -------------------------------------------------------------
    print("[19/21] Generating: UI Feature Breakdown...")
    ui_data = master_df["reason_start"].value_counts().reset_index()
    ui_data.columns = ["reason", "count"]
    threshold = len(master_df) * 0.02
    ui_clean = (
        ui_data
        .assign(clean_reason=lambda df: np.where(df["count"] >= threshold, df["reason"], "Other"))
        .groupby("clean_reason", as_index=False)["count"]
        .sum()
        .sort_values("count", ascending=False)
    )
    plt.figure(figsize=(9, 9))
    colors = sns.color_palette("mako", len(ui_clean))
    plt.pie(
        ui_clean["count"], 
        labels=ui_clean["clean_reason"],
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        pctdistance=0.80,
        wedgeprops=dict(width=0.45, edgecolor='#111827', linewidth=2.5), 
        textprops={'color': "white", 'fontsize': 12, 'fontweight': 'bold'}
    )
    plt.title("UI Feature Breakdown: What Button Triggers Your Music?", pad=20, fontsize=15)
    img_path = IMAGES_DIR / "chart_19_ui_feature_donut.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "19. UI Feature Breakdown (Donut Chart)", level=3)
    log_text(report_file, f"![UI Feature Breakdown](images/{img_path.name})\n\n*Proportional breakdown of interactive UI triggers initiating audio playback.*")

    # -------------------------------------------------------------
    # 20. DAU vs. MAU: Volatility vs. Macro Trends
    # -------------------------------------------------------------
    print("[20/21] Generating: DAU vs. MAU...")
    dau_data = (
        master_df.assign(date=lambda df: df["time_stamp"].dt.date)
        .groupby("date")
        .agg(daily_hours=("sec_played", lambda x: x.sum() / 3600))
        .reset_index()
    )
    dau_data["date"] = pd.to_datetime(dau_data["date"])
    full_range = pd.date_range(start=dau_data["date"].min(), end=dau_data["date"].max())
    dau_data = dau_data.set_index("date").reindex(full_range, fill_value=0).reset_index().rename(columns={"index": "date"})
    dau_data["30_day_trend"] = dau_data["daily_hours"].rolling(window=30, min_periods=1).mean()

    plt.figure(figsize=(15, 6))
    plt.bar(dau_data["date"], dau_data["daily_hours"], color="#38bdf8", alpha=0.6, width=1.0, label="Daily Active Usage (Hours)")
    plt.plot(dau_data["date"], dau_data["30_day_trend"], color="#FCA5A5", linewidth=2.5, label="30-Day Macro Trend (MAU)")
    plt.title("DAU vs. MAU: Daily Listening Volatility vs. 30-Day Macro Trends", pad=20, fontsize=15)
    plt.xlabel("Timeline", fontsize=12)
    plt.ylabel("Listening Time (Hours)", fontsize=12)
    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.legend(frameon=False, labelcolor="white")
    plt.grid(axis='y', color="#1F2937", linestyle="--", alpha=0.5)
    sns.despine(left=True, bottom=True)
    plt.xlim(dau_data["date"].min(), dau_data["date"].max())
    img_path = IMAGES_DIR / "chart_20_dau_vs_mau.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "20. DAU vs. MAU Trends", level=3)
    log_text(report_file, f"![DAU vs MAU](images/{img_path.name})\n\n*Daily volume waveform contrasted against the smoothed 30-day macro moving average.*")

    # -------------------------------------------------------------
    # 21. The Sleep Churn
    # -------------------------------------------------------------
    print("[21/21] Generating: The Sleep Churn...")
    churn_data = (
        master_df[["time_stamp", "reason_start"]]
        .assign(
            hour=lambda df: df["time_stamp"].dt.hour,
            traffic_type=lambda df: np.where(df["reason_start"] == "trackdone", "Passive (Robot Auto-Play)", "Active (Human Clicks)")
        )
        .groupby(["hour", "traffic_type"])
        .size()
        .unstack(fill_value=0)
    )
    churn_ratio = churn_data.div(churn_data.sum(axis=1), axis=0) * 100
    colors = {"Active (Human Clicks)": "#38bdf8", "Passive (Robot Auto-Play)": "#FCA5A5"}
    plot_colors = [colors.get(col, "#ffffff") for col in churn_ratio.columns]

    ax = churn_ratio.plot(kind="bar", stacked=True, figsize=(12, 6), color=plot_colors, edgecolor="#111827", width=0.85)
    for container in ax.containers:
        labels = [f"{val:.0f}%" if val > 5 else "" for val in container.datavalues]
        ax.bar_label(container, labels=labels, label_type='center', color='black', fontweight='bold')
    plt.title("The DEEP FOCUS BG CHURN: Human Engagement vs. Autoplay Zombies", pad=20, fontsize=15)
    plt.xlabel("Time of Day", fontsize=12)
    plt.ylabel("Percentage of Traffic (%)", fontsize=12)
    hours_labels = [f"{h} AM" if h < 12 else f"{h-12} PM" if h > 12 else "12 PM" for h in churn_ratio.index]
    hours_labels[0] = "12 AM"
    ax.set_xticklabels(hours_labels, rotation=45, ha='right')
    plt.legend(title="Control Mode", bbox_to_anchor=(1.01, 1), loc='upper left', frameon=False, title_fontsize=12)
    sns.despine(left=True, bottom=True)
    plt.ylim(0, 100)
    img_path = IMAGES_DIR / "chart_21_sleep_churn.png"
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()
    log_section(report_file, "21. The Sleep Churn", level=3)
    log_text(report_file, f"![The Sleep Churn](images/{img_path.name})\n\n*Hourly ratio of conscious human interactions vs. automated looping while sleeping or working.*")

    print(f"\nAll 21 visualizations successfully generated and embedded in: {report_file}")


def run_feature_engineering_and_export(master_df):
    """Executes Phase 3: Generates ML features and stores dataset interactively in SQLite or PostgreSQL."""
    print("\n" + "=" * 65)
    print("   PHASE 3: FEATURE ENGINEERING & DATASET EXPORT")
    print("=" * 65)
    print("Generating advanced behavioral features...")

    # 1. Ensure Chronological Ordering
    master_df = master_df.sort_values(by="time_stamp").reset_index(drop=True)

    # 2. Ground-Truth Skip Target
    master_df["is_skip"] = (master_df["reason_end"] == "fwdbtn").astype(int)

    # 3. Temporal Signals & Circadian Encodings
    master_df["hour_of_day"] = master_df["time_stamp"].dt.hour.astype("int8")
    master_df["day_of_week"] = master_df["time_stamp"].dt.dayofweek.astype("int8")
    master_df["day_of_month"] = master_df["time_stamp"].dt.day.astype("int8")
    master_df["year"] = master_df["time_stamp"].dt.year.astype("int16")
    master_df["hour_sin"] = np.sin(2 * np.pi * master_df["hour_of_day"] / 24.0).astype("float32")
    master_df["hour_cos"] = np.cos(2 * np.pi * master_df["hour_of_day"] / 24.0).astype("float32")

    # 4. Dynamic Target Encoding with Laplace Smoothing (Strict Zero-Leakage)
    global_skip_rate = master_df["is_skip"].mean()
    smoothing_weight = 20

    # A. Artist Affinity & Cold-Start Indicator
    master_df["artist_past_plays"] = master_df.groupby("artist_name").cumcount()
    master_df["artist_past_skips"] = master_df.groupby("artist_name")["is_skip"].cumsum() - master_df["is_skip"]
    master_df["artist_smoothed_skip_rate"] = (
        (master_df["artist_past_skips"] + (smoothing_weight * global_skip_rate)) /
        (master_df["artist_past_plays"] + smoothing_weight)
    ).astype("float32")
    master_df["is_cold_start_artist"] = (master_df["artist_past_plays"] < 3).astype("int8")

    # B. Song Affinity
    master_df["song_past_plays"] = master_df.groupby("song_name").cumcount()
    master_df["song_past_skips"] = master_df.groupby("song_name")["is_skip"].cumsum() - master_df["is_skip"]
    master_df["song_smoothed_skip_rate"] = (
        (master_df["song_past_skips"] + (smoothing_weight * global_skip_rate)) /
        (master_df["song_past_plays"] + smoothing_weight)
    ).astype("float32")

    # C. Primary Genre Affinity (from Last.fm Tags)
    if "genres" in master_df.columns:
        master_df["primary_genre"] = master_df["genres"].apply(
            lambda x: x.split(",")[0].strip().lower() if isinstance(x, str) and x.strip() else "unknown"
        )
    else:
        master_df["primary_genre"] = "unknown"

    master_df["genre_past_plays"] = master_df.groupby("primary_genre").cumcount()
    master_df["genre_past_skips"] = master_df.groupby("primary_genre")["is_skip"].cumsum() - master_df["is_skip"]
    master_df["genre_smoothed_skip_rate"] = (
        (master_df["genre_past_skips"] + (smoothing_weight * global_skip_rate)) /
        (master_df["genre_past_plays"] + smoothing_weight)
    ).astype("float32")

    # D. Album Affinity
    master_df["album_name_clean"] = master_df["album_name"].fillna("unknown").astype(str)
    master_df["album_past_plays"] = master_df.groupby("album_name_clean").cumcount()
    master_df["album_past_skips"] = master_df.groupby("album_name_clean")["is_skip"].cumsum() - master_df["is_skip"]
    master_df["album_smoothed_skip_rate"] = (
        (master_df["album_past_skips"] + (smoothing_weight * global_skip_rate)) /
        (master_df["album_past_plays"] + smoothing_weight)
    ).astype("float32")

    # E. Playback Trigger Origin (reason_start)
    master_df["reason_start_clean"] = master_df["reason_start"].fillna("unknown").astype(str)
    master_df["reason_past_plays"] = master_df.groupby("reason_start_clean").cumcount()
    master_df["reason_past_skips"] = master_df.groupby("reason_start_clean")["is_skip"].cumsum() - master_df["is_skip"]
    master_df["reason_start_smoothed_skip_rate"] = (
        (master_df["reason_past_skips"] + (smoothing_weight * global_skip_rate)) /
        (master_df["reason_past_plays"] + smoothing_weight)
    ).astype("float32")

    # Cleanup intermediate calculation columns
    master_df = master_df.drop(columns=[
        "artist_past_plays", "artist_past_skips",
        "song_past_plays", "song_past_skips",
        "primary_genre", "genre_past_plays", "genre_past_skips",
        "album_name_clean", "album_past_plays", "album_past_skips",
        "reason_start_clean", "reason_past_plays", "reason_past_skips"
    ])

    # 5. Micro-Mood & Real-Time Sequential Momentum
    master_df["previous_song_skipped"] = master_df["is_skip"].shift(1).fillna(0).astype("int8")

    # A. Consecutive Listens Streak (Listening Inertia / The 'Zone' Indicator)
    streak_group = (master_df["is_skip"].shift(1).fillna(0) == 1).cumsum()
    master_df["consecutive_listens_streak"] = master_df.groupby(streak_group).cumcount().astype("int16")

    # B. Backward Merge for Distance to Last Skip (Zero Lookahead)
    skips_only = master_df[master_df["is_skip"] == 1][["time_stamp"]]
    master_df["last_skip_time"] = pd.merge_asof(
        master_df[["time_stamp"]],
        skips_only.assign(last_skip_time=skips_only["time_stamp"]),
        on="time_stamp",
        direction="backward",
        allow_exact_matches=False
    )["last_skip_time"]

    master_df["seconds_since_last_skip"] = (
        (master_df["time_stamp"] - master_df["last_skip_time"]).dt.total_seconds().fillna(10000)
    ).astype("float32")
    master_df = master_df.drop(columns=["last_skip_time"])

    # C. Multi-Scale Rolling Skip Velocities (3-Minute & 15-Minute Windows)
    master_df = master_df.set_index("time_stamp").sort_index()
    master_df["skips_last_3m"] = (master_df["is_skip"].rolling("3min").sum() - master_df["is_skip"]).astype("float32")
    master_df["skips_last_15m"] = (master_df["is_skip"].rolling("15min").sum() - master_df["is_skip"]).astype("float32")
    master_df = master_df.reset_index()

    # 6. Environmental & Hardware Context
    if "platform" in master_df.columns:
        master_df["platform_android"] = (master_df["platform"].astype(str).str.lower() == "android").astype("int8")
        master_df["platform_windows"] = (master_df["platform"].astype(str).str.lower() == "windows").astype("int8")
        master_df["platform_linux"] = (master_df["platform"].astype(str).str.lower() == "linux").astype("int8")
    else:
        master_df["platform_android"] = 0
        master_df["platform_windows"] = 0
        master_df["platform_linux"] = 0

    if "shuffle" in master_df.columns:
        master_df["shuffle_mode"] = master_df["shuffle"].fillna(0).astype(int).astype("int8")
    else:
        master_df["shuffle_mode"] = 0

    # Session boundary: Gap > 20 minutes indicates start of a fresh listening session
    time_diff_sec = (master_df["time_stamp"] - master_df["time_stamp"].shift(1)).dt.total_seconds().fillna(99999)
    master_df["is_session_start"] = (time_diff_sec > 1200).astype("int8")

    print("Feature engineering complete!")
    print(f"Engineered Dataset Shape: {master_df.shape} ({len(master_df):,} rows, {len(master_df.columns)} columns)")
    print(f"Target Distribution: Completed: {len(master_df[master_df['is_skip'] == 0]):,} ({len(master_df[master_df['is_skip'] == 0])/len(master_df)*100:.1f}%) | Skipped: {len(master_df[master_df['is_skip'] == 1]):,} ({len(master_df[master_df['is_skip'] == 1])/len(master_df)*100:.1f}%)")

    # Clean Genres for SQL export
    if "genres" in master_df.columns:
        master_df["genres"] = master_df["genres"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))

    # Drop high-dimensional one-hot genre columns (replaced by continuous genre_smoothed_skip_rate)
    dummy_genre_cols = [c for c in master_df.columns if c.startswith("genre_") and c != "genre_smoothed_skip_rate"]
    if dummy_genre_cols:
        master_df = master_df.drop(columns=dummy_genre_cols)

    # EXPORT PROMPT SETUP
    default_base_name = "Engineered_Spotify_Portable"
    print("\n--- FEATURE STORE EXPORT SETUP ---")
    print(f"Directory: {PROCESSED_DIR}")

    base_name = None
    while True:
        try:
            name_input = input(f"Enter name for file and table [press Enter for default: {default_base_name}]: ").strip()
            raw_name = name_input or default_base_name
            base_name = raw_name[:-3] if raw_name.lower().endswith(".db") else raw_name
            break
        except (KeyboardInterrupt, EOFError):
            print("\nExport cancelled by user (Escape pressed).")
            return

    db_filename = f"{base_name}.db"
    table_name = base_name
    print(f"File Name : '{db_filename}'")
    print(f"Table Name: '{table_name}'")

    print("\nWhere do you want to save the engineered features?")
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
            local_conn.execute("DROP TABLE IF EXISTS engineered_streaming_history")
            master_df.to_sql(table_name, local_conn, if_exists="replace", index=False, chunksize=10000)
            local_conn.execute("VACUUM")
            local_conn.close()
            print(f"Portable SQLite Feature Store Built Successfully at: {sqlite_path} [table: {table_name}]")
        except Exception as e:
            print(f"\n[ERROR] Failed to export to SQLite: {e}")

    # PostgreSQL Export
    def psql_insert_copy(table, conn, keys, data_iter):
        dbapi_conn = conn.connection.dbapi_connection
        with dbapi_conn.cursor() as cur:
            s_buf = io.StringIO()
            writer = csv.writer(s_buf)
            writer.writerows(data_iter)
            s_buf.seek(0)
            columns = ', '.join([f'"{k}"' for k in keys])
            t_name = f'"{table.name}"'
            sql = f'COPY {t_name} ({columns}) FROM STDIN WITH (FORMAT CSV)'
            cur.copy_expert(sql=sql, file=s_buf)

    if export_choice in ["2", "3"]:
        default_uri = os.getenv("POSTGRES_URI", "postgresql://postgres:password@localhost:5432/postgres")
        masked_uri = re.sub(r':([^@:/]+)@', ':****@', default_uri)
        print("\n--- PostgreSQL Server Export ---")
        print(f"Default URI: {masked_uri}")
        print("Press Enter to use default URI, or enter custom URI (or press Esc to cancel).")
        while True:
            try:
                uri_input = input(f"Enter PostgreSQL Connection URI [press Enter for default: {default_uri}]: ").strip()
                postgres_uri = uri_input or default_uri
                print(f"\nConnecting to: {re.sub(r':([^@:/]+)@', ':****@', postgres_uri)}")
                print(f"Writing to PostgreSQL table '{table_name}' using COPY stream...")
                engine = create_engine(postgres_uri)
                master_df.to_sql(table_name, engine, if_exists="replace", index=False, method=psql_insert_copy)
                engine.dispose()
                print(f"PostgreSQL Feature Store Table '{table_name}' Created Successfully!")
                break
            except (KeyboardInterrupt, EOFError):
                print("\nPostgreSQL export cancelled by user (Escape pressed).")
                break
            except Exception as e:
                print(f"\n[ERROR] Failed to connect or write to PostgreSQL: {e}")
                print("Tip: If you want to use the default local PostgreSQL server, simply press Enter without typing anything.")
                print("Please try again (or press Esc to cancel).\n")


def main():
    print("=" * 65)
    print("   SPOTIFY EXPLORATORY DATA ANALYSIS & REPORTING PIPELINE")
    print("=" * 65)

    master_df = ingest_cleaned_data()
    if master_df is None:
        print("\nPipeline execution cancelled.")
        return

    top_n = ask_top_n()
    if top_n is None:
        print("\nPipeline execution cancelled.")
        return

    # Phase 1 & 2: Markdown Report & Visualizations
    eda_vars = run_eda_pipeline(master_df, top_n)
    run_visualizations_pipeline(master_df, eda_vars)

    # Phase 3: Feature Engineering & Export to ML Feature Store
    run_feature_engineering_and_export(master_df)

    print("\n" + "=" * 65)
    print("   STAGE 2 COMPLETE: REPORT & FEATURE STORE READY!")
    print(f"   Markdown Report : {REPORTS_DIR / 'EDA_Report.md'}")
    print(f"   Embedded Charts : {IMAGES_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    main()

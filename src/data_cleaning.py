import argparse
import os
import glob
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
from sklearn.preprocessing import MultiLabelBinarizer

# Silence pandas warnings
pd.set_option('future.no_silent_downcasting', True)

def parse_args():
    parser = argparse.ArgumentParser(description="Spotify Data Cleaning Pipeline")
    parser.add_argument("--input-type", type=str, choices=["json", "sqlite", "postgres"], default="json",
                        help="Format of the input data (default: json)")
    parser.add_argument("--input-path", type=str, default="..",
                        help="Path to the directory containing JSON files or the SQLite DB file")
    parser.add_argument("--db-uri", type=str, default="postgresql://user:password@localhost:5432/postgres",
                        help="PostgreSQL Connection URI (if using postgres)")
    parser.add_argument("--output-type", type=str, choices=["sqlite", "postgres", "both"], default="sqlite",
                        help="Format to save the cleaned data (default: sqlite)")
    parser.add_argument("--output-path", type=str, default="Cleaned_Data/Cleaned_Spotify_Data",
                        help="Base path/name to save the output file (without extension)")
    args = parser.parse_args()
    
    import sys
    if len(sys.argv) == 1:
        print("=== Interactive Setup ===")
        args.input_type = input("How is your raw data stored? (json/sqlite/postgres) [default: json]: ").strip().lower() or "json"
        if args.input_type == "json":
            args.input_path = input("Enter the folder path containing JSON files [default: ..]: ").strip() or ".."
        elif args.input_type == "sqlite":
            args.input_path = input("Enter the path to SQLite DB: ").strip()
        elif args.input_type == "postgres":
            args.db_uri = input("Enter PostgreSQL URI: ").strip()
            
        print("\nData cleaning is meant to store data in SQL formats.")
        args.output_type = input("Where do you want to save the cleaned data? (sqlite/postgres) [default: sqlite]: ").strip().lower() or "sqlite"
        if args.output_type == "sqlite":
            args.output_path = input("Path to save the output SQLite DB (without .db) [default: Cleaned_Data/Cleaned_Spotify_Data]: ").strip() or "Cleaned_Data/Cleaned_Spotify_Data"
        elif args.output_type == "postgres":
            args.db_uri = input("Enter PostgreSQL URI for output: ").strip()
            
    return args

def load_data(args):
    """Loads raw data based on user input format."""
    print(f"Loading data from {args.input_type}...")
    
    if args.input_type == "json":
        # Load Streaming History
        filePaths = glob.glob(os.path.join(args.input_path, "**/Streaming_History_Audio_*.json"), recursive=True)
        if not filePaths:
            raise FileNotFoundError(f"No Streaming_History_Audio_*.json files found in {args.input_path}")
        
        master_df = []
        for file in filePaths:
            temp_df = pd.read_json(file)
            master_df.append(temp_df)
        master_df = pd.concat(master_df, ignore_index=True)
        
        # Load Last.fm genre data
        lastfm_files = glob.glob(os.path.join(args.input_path, "**/lastfm_track_data.json"), recursive=True)
        if not lastfm_files:
            print("WARNING: lastfm_track_data.json not found. Genre merging will be skipped.")
            temp_df = None
        else:
            temp_df = pd.read_json(lastfm_files[0])
            
        return master_df, temp_df

    elif args.input_type == "sqlite":
        conn = sqlite3.connect(args.input_path)
        master_df = pd.read_sql("SELECT * FROM raw_streaming_history", conn)
        # Note: In a real scenario, you'd load temp_df from sqlite too if it exists
        return master_df, None
        
    elif args.input_type == "postgres":
        engine = create_engine(args.db_uri)
        master_df = pd.read_sql("SELECT * FROM raw_streaming_history", engine)
        return master_df, None

def clean_data(master_df, temp_df):
    """Applies all data cleaning and transformation logic."""
    print("Cleaning data...")
    master_df = master_df.dropna(axis=1, how='all')
    
    # Target Variable creation
    if "reason_end" in master_df.columns:
        master_df["skipped"] = (master_df["reason_end"] == "fwdbtn").astype(int)
    
    if "ms_played" in master_df.columns:
        master_df['ms_played'] = (master_df['ms_played'] / 1000).astype(int)
        
    if "ts" in master_df.columns:
        master_df['ts'] = pd.to_datetime(master_df['ts'], utc=True)
        master_df["ts"] = master_df["ts"].dt.tz_convert("Asia/Kolkata")
        
    master_df = master_df.rename(
        columns={
            'ts': 'time_stamp',
            'ms_played': 'sec_played',
            'master_metadata_track_name': 'song_name',
            'master_metadata_album_artist_name': 'artist_name',
            'master_metadata_album_album_name': 'album_name',
            'episode_name': 'podcast_episode_name',
            'episode_show_name': 'podcast_name'
        }
    )

    if 'song_name' in master_df.columns:
        master_df = master_df[master_df['song_name'].notna()]
        
    cols_to_drop = ['podcast_episode_name', 'podcast_name', 'spotify_episode_uri']
    master_df.drop(columns=[c for c in cols_to_drop if c in master_df.columns], inplace=True)
    
    print(f"Shape after initial cleaning: {master_df.shape}")

    # Process Last.fm genre data if available
    if temp_df is not None:
        print("Processing Last.fm genre data...")
        unique_genre = set(temp_df["genres"].explode().value_counts().loc[lambda x: x >= 30].index)
        temp_df["genres"] = temp_df["genres"].apply(lambda genre_list: [genre for genre in genre_list if genre in unique_genre])
        temp_df.rename(columns={"track_name": "song_name"}, inplace=True)
        
        if "genres" not in master_df.columns:
            master_df = master_df.merge(temp_df, on=["song_name", "artist_name"], how="left")
            print("Merge Successful")
        else:
            print("Already Merged Once")
            
        master_df['genres'] = master_df['genres'].apply(lambda x: x if isinstance(x, list) else [])
        
        print("Applying MultiLabelBinarizer for genres...")
        mlb = MultiLabelBinarizer()
        binary_matrix = mlb.fit_transform(master_df["genres"])
        genres_df = pd.DataFrame(binary_matrix, columns=mlb.classes_).add_prefix('genre_')
        master_df = pd.concat([master_df, genres_df], axis=1)
        
        bool_cols = master_df.select_dtypes(include=['bool']).columns
        master_df[bool_cols] = master_df[bool_cols].astype(int)
        
        cols_to_fill = ['listeners', 'playcount', 'incognito_mode']
        master_df[[c for c in cols_to_fill if c in master_df.columns]] = master_df[[c for c in cols_to_fill if c in master_df.columns]].fillna(0).astype(int)
        
        print(f"Shape after genre merge: {master_df.shape}")

        print("Compressing data types to save memory...")
        genre_columns = [col for col in master_df.columns if col.startswith("genre_")]
        compressing_cols = genre_columns + ["shuffle", "skipped"]
        # Only compress columns that exist
        compressing_cols = [c for c in compressing_cols if c in master_df.columns]
        master_df[compressing_cols] = master_df[compressing_cols].astype("int8")
        
        # Clean Genres for SQL storage
        master_df['genres'] = master_df['genres'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))

    master_df.drop_duplicates(inplace=True)
    return master_df

def save_data(master_df, args):
    """Saves the cleaned dataframe to the requested destinations."""
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    
    if args.output_type in ["postgres", "both"]:
        print("Saving to PostgreSQL...")
        engine = create_engine(args.db_uri)
        master_df.to_sql("streaming_history", engine, if_exists="replace", index=False, chunksize=10000)
        print("PostgreSQL Server Rebuilt Perfectly!")

    if args.output_type in ["sqlite", "both"]:
        print("Saving to SQLite...")
        out_file = f"{args.output_path}.db"
        local_conn = sqlite3.connect(out_file)
        master_df.to_sql("streaming_history", local_conn, if_exists="replace", index=False, chunksize=10000)
        local_conn.close()
        print("Portable SQLite Backup Rebuilt Perfectly!")

def main():
    args = parse_args()
    master_df, temp_df = load_data(args)
    master_df = clean_data(master_df, temp_df)
    save_data(master_df, args)
    print("Data cleaning pipeline completed successfully!")

if __name__ == "__main__":
    main()

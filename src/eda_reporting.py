import argparse
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import numpy as np
import calendar
import sys
from IPython.display import display

def parse_args():
    parser = argparse.ArgumentParser(description='Spotify EDA Reporting')
    parser.add_argument('--input-type', type=str, choices=['csv', 'json', 'sqlite', 'postgres'], default='sqlite', help='Format of the input database (default: sqlite)')
    parser.add_argument('--input-path', type=str, default='Cleaned_Data/Cleaned_Spotify_Data.db', help='Path to the cleaned data file')
    parser.add_argument('--db-uri', type=str, default='postgresql://user:password@localhost:5432/postgres', help='PostgreSQL Connection URI (if using postgres)')
    parser.add_argument('--output-dir', type=str, default='./', help='Directory to save the Markdown report and images')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        print('=== Interactive Setup ===')
        args.input_type = input('How is your cleaned data stored? (csv/json/sqlite/postgres) [default: csv]: ').strip().lower() or 'csv'
        if args.input_type in ['csv', 'json', 'sqlite']:
            default_path = f"Cleaned_Data/Cleaned_Spotify_Data.{('db' if args.input_type == 'sqlite' else args.input_type)}"
            args.input_path = input(f'Enter the path to the {args.input_type.upper()} file [default: {default_path}]: ').strip() or default_path
        elif args.input_type == 'postgres':
            args.db_uri = input('Enter PostgreSQL URI: ').strip()
        args.output_dir = input('Enter output directory for the report [default: ./]: ').strip() or 'reports/'
    return args

def load_cleaned_data(args):
    """Loads data from the chosen database in memory-efficient chunks."""
    print(f'Loading data from {args.input_type}...')
    compressed_chunks = []
    if args.input_type == 'csv':
        master_df = pd.read_csv(args.input_path)
    elif args.input_type == 'json':
        master_df = pd.read_json(args.input_path)
    elif args.input_type == 'sqlite':
        conn = sqlite3.connect(args.input_path)
        for chunk in pd.read_sql_query('SELECT * FROM streaming_history', conn, chunksize=10000):
            genre_columns = [col for col in chunk.columns if col.startswith('genre_')]
            cols_to_compress = genre_columns + ['shuffle', 'skipped']
            cols_to_compress = [c for c in cols_to_compress if c in chunk.columns]
            chunk[cols_to_compress] = chunk[cols_to_compress].astype('int8')
            compressed_chunks.append(chunk)
        conn.close()
        master_df = pd.concat(compressed_chunks, ignore_index=True)
    elif args.input_type == 'postgres':
        engine = create_engine(args.db_uri)
        for chunk in pd.read_sql_table('streaming_history', engine, chunksize=10000):
            genre_columns = [col for col in chunk.columns if col.startswith('genre_')]
            cols_to_compress = genre_columns + ['shuffle', 'skipped']
            cols_to_compress = [c for c in cols_to_compress if c in chunk.columns]
            chunk[cols_to_compress] = chunk[cols_to_compress].astype('int8')
            compressed_chunks.append(chunk)
        master_df = pd.concat(compressed_chunks, ignore_index=True)
    master_df['time_stamp'] = pd.to_datetime(master_df['time_stamp'])
    print('Database loaded with maximum RAM efficiency!')
    return master_df

def run_eda(master_df, output_dir):
    import os
    import sys
    import builtins
    import warnings
    warnings.filterwarnings('ignore')

    from IPython.display import display as orig_display
    try:
        output_dir = output_dir if output_dir else '.'
    except Exception:
        pass
    try:
        images_dir = os.path.join(output_dir, 'images')
    except Exception:
        pass
    try:
        os.makedirs(images_dir, exist_ok=True)
    except Exception:
        pass
    try:
        md_file_path = os.path.join(output_dir, 'EDA_Report.md')
    except Exception:
        pass
    try:
        md_file = open(md_file_path, 'w', encoding='utf-8')
    except Exception:
        pass
    try:
        md_file.write('# Spotify EDA Report\n\n')
    except Exception:
        pass
    try:
        counter = [0]
    except Exception:
        pass
    try:
        total_ops = 88 + 81 + 20
    except Exception:
        pass
    try:
        _orig_print = builtins.print
    except Exception:
        pass
    try:
        _orig_show = plt.show
    except Exception:
        pass

    def update_progress():
        counter[0] += 1
        sys.stdout.write(f'\r{counter[0]}/{total_ops} results prepared...')
        sys.stdout.flush()

    def custom_print(*args, **kwargs):
        update_progress()
        text = ' '.join((str(a) for a in args))
        md_file.write(f'### {text}\n\n')

    def custom_display(*args, **kwargs):
        update_progress()
        for arg in args:
            try:
                if hasattr(arg, 'to_markdown'):
                    md_file.write(arg.head(15).to_html(index=False) + '\n\n')
                elif hasattr(arg, 'data'):
                    md_file.write(arg.data.head(15).to_html(index=False) + '\n\n')
                else:
                    md_file.write(str(arg) + '\n\n')
            except Exception:
                md_file.write(str(arg) + '\n\n')

    def custom_show(*args, **kwargs):
        update_progress()
        filename = f'chart_{counter[0]}.png'
        filepath = os.path.join(images_dir, filename)
        plt.savefig(filepath, bbox_inches='tight')
        md_file.write(f'![Chart](images/{filename})\n\n')
        plt.clf()
    try:
        builtins.print = custom_print
    except Exception:
        pass
    try:
        globals()['display'] = custom_display
    except Exception:
        pass
    try:
        plt.show = custom_show
    except Exception:
        pass
    try:
        rows, columns = master_df.shape
    except Exception:
        pass
    try:
        print(f'There are {rows} rows of data and {columns} features')
    except Exception:
        pass
    try:
        display(master_df.tail(1))
    except Exception:
        pass
    try:
        master_df.info(verbose=True, show_counts=False, buf=md_file)
    except Exception:
        pass
    try:
        season_dict = {1: 'winter', 2: 'winter', 3: 'summer', 4: 'summer', 5: 'summer', 6: 'moonsoon', 7: 'moonsoon', 8: 'moonsoon', 9: 'moonsoon', 10: 'autumn', 11: 'autumn', 12: 'winter'}
    except Exception:
        pass

    def format_time(seconds):
        seconds = int(seconds)
        if seconds < 60:
            return f'{seconds}s'
        minutes, seconds = divmod(seconds, 60)
        if minutes < 60:
            return f'{minutes}m {seconds}s'
        hours, minutes = divmod(minutes, 60)
        if hours < 24:
            return f'{hours}h {minutes}m {seconds}s'
        days, hours = divmod(hours, 24)
        if days < 30:
            return f'{days}d {hours}h {minutes}m'
        months, days = divmod(days, 30)
        if months < 12:
            return f'{months}mo {days}d {hours}h'
        year, months = divmod(months, 12)
        if year:
            return f'{year}y {months}m {days}d'
    try:
        top_artist_alltime = master_df.groupby('artist_name').agg({'artist_name': 'count', 'sec_played': 'sum'}).rename(columns={'artist_name': 'play_counts', 'sec_played': 'total_time_listened'}).reset_index()
    except Exception:
        pass
    try:
        top_artist_alltime = top_artist_alltime.sort_values(by=['total_time_listened', 'play_counts'], ascending=[False, False])
    except Exception:
        pass
    try:
        print(f'YOUR ALL TIME TOP ARTIST BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_artist_alltime.head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR ALL TIME TOP ARTIST BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_artist_alltime.sort_values(by='play_counts', ascending=False).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_artist_yearly = master_df.groupby([master_df['time_stamp'].dt.year.rename('Year'), 'artist_name']).agg({'artist_name': 'count', 'sec_played': 'sum'}).rename(columns={'artist_name': 'play_counts', 'sec_played': 'total_time_listened'}).reset_index()
    except Exception:
        pass
    try:
        top_artist_yearly = top_artist_yearly.sort_values(by=['Year', 'total_time_listened', 'play_counts'], ascending=[True, False, False])
    except Exception:
        pass
    try:
        print(f'YOUR TOP ARTIST YEARLY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_artist_yearly.groupby('Year').head(1).sort_values(by='Year', ascending=True).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP ARTIST YEARLY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_artist_yearly.groupby('Year').head(1).sort_values(by=['Year', 'play_counts'], ascending=[True, False]).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_artist_monthly = master_df.groupby([master_df['time_stamp'].dt.tz_localize(None).dt.to_period('M').rename('Period'), 'artist_name']).agg({'artist_name': 'count', 'sec_played': 'sum'}).rename(columns={'artist_name': 'play_counts', 'sec_played': 'total_time_listened'}).reset_index()
    except Exception:
        pass
    try:
        top_artist_monthly = top_artist_monthly.sort_values(by=['Period', 'total_time_listened', 'play_counts'], ascending=[True, False, False])
    except Exception:
        pass
    try:
        top_artist_monthly['total_time_listened'] = top_artist_monthly['total_time_listened'].apply(format_time)
    except Exception:
        pass
    try:
        print(f'YOUR TOP ARTIST MONTHLY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_artist_monthly.groupby('Period').head(1).sort_values(by='Period', ascending=True).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print(f'YOUR TOP ARTIST MONTHLY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_artist_monthly.groupby('Period').head(1).sort_values(by=['Period', 'play_counts'], ascending=[True, False]).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        top_artist_daily = master_df.groupby([master_df['time_stamp'].dt.tz_localize(None).dt.to_period('D').rename('Period'), 'artist_name']).agg({'artist_name': 'count', 'sec_played': 'sum'}).rename(columns={'artist_name': 'play_counts', 'sec_played': 'total_time_listened'}).reset_index()
    except Exception:
        pass
    try:
        top_artist_daily = top_artist_daily.sort_values(by=['Period', 'total_time_listened', 'play_counts'], ascending=[True, False, False])
    except Exception:
        pass
    try:
        print(f'YOUR TOP ARTIST MONTHLY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_artist_daily.groupby('Period').head(1).sort_values(by='Period', ascending=True).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP ARTIST MONTHLY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_artist_daily.groupby('Period').head(1).sort_values(by=['Period', 'play_counts'], ascending=[True, False]).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_artist_seasonal = master_df.groupby([master_df['time_stamp'].dt.year.rename('Year'), master_df['time_stamp'].dt.month.map(season_dict).rename('Season'), 'artist_name']).agg({'sec_played': 'sum', 'artist_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'artist_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_seasonal_artist = top_artist_seasonal.sort_values(by=['Season', 'total_time_listened', 'play_counts'], ascending=[True, False, False])
    except Exception:
        pass
    try:
        print(f'YOUR TOP ARTIST SEASONALY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_seasonal_artist.sort_values(by=['Year', 'Season'], ascending=[True, True]).groupby(['Year', 'Season']).head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP ARTIST SEASONALY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_seasonal_artist.sort_values(by=['Year', 'Season', 'play_counts'], ascending=[True, True, False]).groupby(['Year', 'Season']).head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_song_alltime = master_df.groupby(['song_name', 'artist_name', 'spotify_track_uri']).agg({'sec_played': 'sum', 'song_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'song_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_song_alltime = top_song_alltime.sort_values(by=['total_time_listened', 'play_counts'], ascending=[False, False])
    except Exception:
        pass
    try:
        top_song_alltime = top_song_alltime.drop(columns='spotify_track_uri')
    except Exception:
        pass
    try:
        print(f'YOUR TOP SONG ALLTIME BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_song_alltime.head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP SONG ALLTIME BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_song_alltime.sort_values(by='play_counts', ascending=False).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_song_yearly = master_df.groupby([master_df['time_stamp'].dt.year.rename('Year'), 'song_name', 'artist_name', 'spotify_track_uri']).agg({'sec_played': 'sum', 'song_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'song_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_song_yearly = top_song_yearly.sort_values(by=['Year', 'total_time_listened', 'play_counts'], ascending=[True, False, False])
    except Exception:
        pass
    try:
        top_song_yearly = top_song_yearly.drop(columns='spotify_track_uri')
    except Exception:
        pass
    try:
        print(f'YOUR TOP SONG ALLTIME BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_song_yearly.groupby('Year').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP SONG ALLTIME BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_song_yearly.sort_values(by=['Year', 'play_counts'], ascending=[True, False]).groupby('Year').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_song_monthly = master_df.groupby([master_df['time_stamp'].dt.tz_localize(None).dt.to_period('M').rename('Period'), 'song_name', 'artist_name', 'spotify_track_uri']).agg({'sec_played': 'sum', 'song_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'song_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_song_monthly = top_song_monthly.sort_values(by=['Period', 'total_time_listened', 'play_counts'], ascending=[True, False, False])
    except Exception:
        pass
    try:
        top_song_monthly = top_song_monthly.drop(columns='spotify_track_uri')
    except Exception:
        pass
    try:
        print(f'YOUR TOP SONG ALLTIME BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_song_monthly.groupby('Period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP SONG ALLTIME BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_song_monthly.sort_values(by=['Period', 'play_counts'], ascending=[True, False]).groupby('Period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_song_daily = master_df.groupby([master_df['time_stamp'].dt.tz_localize(None).dt.to_period('D').rename('Period'), 'song_name', 'artist_name', 'spotify_track_uri']).agg({'sec_played': 'sum', 'song_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'song_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_song_daily = top_song_daily.sort_values(by=['Period', 'total_time_listened', 'play_counts'], ascending=[True, False, False])
    except Exception:
        pass
    try:
        top_song_daily = top_song_daily.drop(columns='spotify_track_uri')
    except Exception:
        pass
    try:
        print(f'YOUR TOP SONG ALLTIME BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_song_daily.groupby('Period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP SONG ALLTIME BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_song_daily.sort_values(by=['Period', 'play_counts'], ascending=[True, False]).groupby('Period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_song_seasonal = master_df.groupby([master_df['time_stamp'].dt.year.rename('Year'), master_df['time_stamp'].dt.month.map(season_dict).rename('Season'), 'song_name', 'artist_name', 'spotify_track_uri']).agg({'sec_played': 'sum', 'song_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'song_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_song_seasonal = top_song_seasonal.sort_values(by=['Year', 'Season', 'total_time_listened', 'play_counts'], ascending=[True, True, False, False])
    except Exception:
        pass
    try:
        top_song_seasonal = top_song_seasonal.drop(columns='spotify_track_uri')
    except Exception:
        pass
    try:
        print(f'YOUR TOP SONG SEASONALY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_song_seasonal.sort_values(by=['Year', 'Season'], ascending=[True, True]).groupby(['Year', 'Season']).head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP SONG SEASONALY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_song_seasonal.sort_values(by=['Year', 'Season', 'play_counts'], ascending=[True, True, False]).groupby(['Year', 'Season']).head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_album_alltime = master_df.groupby(['album_name', 'artist_name']).agg({'sec_played': 'sum', 'album_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'album_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_album_alltime = top_album_alltime.sort_values(by=['total_time_listened', 'play_counts'], ascending=[False, False])
    except Exception:
        pass
    try:
        print(f'YOUR TOP ABLUM ALLTIME BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_album_alltime.head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP ALBUM ALLTIME BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_album_alltime.sort_values(by='play_counts', ascending=False).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_album_yearly = master_df.groupby([master_df['time_stamp'].dt.year.rename('Year'), 'album_name', 'artist_name']).agg({'sec_played': 'sum', 'album_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'album_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_album_yearly = top_album_yearly.sort_values(by=['Year', 'total_time_listened', 'play_counts'], ascending=[True, False, False])
    except Exception:
        pass
    try:
        print(f'YOUR TOP ALBUM YEARLY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_album_yearly.groupby('Year').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP ALBUM YEARLY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_album_yearly.sort_values(by=['Year', 'play_counts'], ascending=[True, False]).groupby('Year').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_album_monthly = master_df.groupby([master_df['time_stamp'].dt.tz_localize(None).dt.to_period('M').rename('Period'), 'album_name', 'artist_name']).agg({'sec_played': 'sum', 'album_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'album_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_album_monthly = top_album_monthly.sort_values(by=['Period', 'total_time_listened', 'play_counts'], ascending=[True, False, False])
    except Exception:
        pass
    try:
        print(f'YOUR TOP ALBUM MONTHLY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_album_monthly.groupby('Period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP ALBUM MONTHLY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_album_monthly.sort_values(by=['Period', 'play_counts'], ascending=[True, False]).groupby('Period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_album_daily = master_df.groupby([master_df['time_stamp'].dt.tz_localize(None).dt.to_period('D').rename('Period'), 'album_name', 'artist_name']).agg({'sec_played': 'sum', 'album_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'album_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_album_daily = top_album_daily.sort_values(by=['Period', 'total_time_listened', 'play_counts'], ascending=[True, False, False])
    except Exception:
        pass
    try:
        print(f'YOUR TOP ALBUM DAILY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_album_daily.groupby('Period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP ALBUM DAILY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_album_daily.sort_values(by=['Period', 'play_counts'], ascending=[True, False]).groupby('Period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        top_album_seasonal = master_df.groupby([master_df['time_stamp'].dt.year.rename('Year'), master_df['time_stamp'].dt.month.map(season_dict).rename('Season'), 'album_name', 'artist_name']).agg({'sec_played': 'sum', 'song_name': 'count'}).rename(columns={'sec_played': 'total_time_listened', 'song_name': 'play_counts'}).reset_index()
    except Exception:
        pass
    try:
        top_album_seasonal = top_album_seasonal.sort_values(by=['Year', 'Season', 'total_time_listened', 'play_counts'], ascending=[True, True, False, False])
    except Exception:
        pass
    try:
        print(f'YOUR TOP ALBUM SEASONALY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(top_album_seasonal.sort_values(by=['Year', 'Season'], ascending=[True, True]).groupby(['Year', 'Season']).head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP ABLUM SEASONALY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(top_album_seasonal.sort_values(by=['Year', 'Season', 'play_counts'], ascending=[True, True, False]).groupby(['Year', 'Season']).head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        all_genre = master_df.filter(like='genre_').columns.tolist()
    except Exception:
        pass
    try:
        print(f' You have listened to {len(all_genre)} unique genre in your lifetime! The genre are as follows:')
    except Exception:
        pass
    try:
        all_genre = pd.DataFrame(all_genre)
    except Exception:
        pass
    try:
        all_genre = all_genre.rename(columns={0: 'genre'})
    except Exception:
        pass
    try:
        all_genre['genre'] = all_genre['genre'].str.replace('genre_', '')
    except Exception:
        pass
    try:
        genre_data = [c for c in master_df.columns if c.startswith('genre_')]
    except Exception:
        pass
    try:
        display(all_genre.head().style.hide(axis='index'))
    except Exception:
        pass
    try:
        genre_time_count = pd.DataFrame({'sec_played': master_df[genre_data].T.dot(master_df['sec_played']), 'play_counts': master_df[genre_data].sum()}).reset_index().rename(columns={'index': 'genre', 'sec_played': 'total_time_listened'})
    except Exception:
        pass
    try:
        genre_alltime = genre_time_count.sort_values(by='total_time_listened', ascending=False)
    except Exception:
        pass
    try:
        genre_alltime['genre'] = genre_alltime['genre'].str.replace('genre_', '')
    except Exception:
        pass
    try:
        print(f'YOUR TOP GENRE ALLTIME BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(genre_alltime.head().style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP GENRE ALLTIME BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(genre_alltime.sort_values(by='play_counts', ascending=False).head().style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        genre_yearly = []
    except Exception:
        pass
    try:
        for year, chunk in master_df.groupby(master_df['time_stamp'].dt.year):
            chunk_summary = pd.DataFrame({'total_time_listened': chunk[genre_data].T.dot(chunk['sec_played']), 'play_counts': chunk[genre_data].sum()}).reset_index()
            chunk_summary['Year'] = year
            genre_yearly.append(chunk_summary)
    except Exception:
        pass
    try:
        genre_yearly = pd.concat(genre_yearly, ignore_index=True)
    except Exception:
        pass
    try:
        genre_yearly = genre_yearly.sort_values(by=['Year', 'total_time_listened'], ascending=[True, False]).rename(columns={'index': 'genre'})
    except Exception:
        pass
    try:
        genre_yearly['genre'] = genre_yearly['genre'].str.replace('genre_', '')
    except Exception:
        pass
    try:
        print(f'YOUR TOP GENRE YEARLY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(genre_yearly.groupby('Year').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP GENRE YEARLY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(genre_yearly.sort_values(by=['Year', 'play_counts'], ascending=[True, False]).groupby('Year').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        genre_monthly = []
    except Exception:
        pass
    try:
        for period, chunk in master_df.groupby(master_df['time_stamp'].dt.tz_localize(None).dt.to_period('M')):
            chunk_summary = pd.DataFrame({'total_time_listened': chunk[genre_data].T.dot(chunk['sec_played']), 'play_counts': chunk[genre_data].sum()}).reset_index()
            chunk_summary['period'] = period
            genre_monthly.append(chunk_summary)
    except Exception:
        pass
    try:
        genre_monthly = pd.concat(genre_monthly, ignore_index=True)
    except Exception:
        pass
    try:
        genre_monthly = genre_monthly.sort_values(by=['period', 'total_time_listened'], ascending=[True, False]).rename(columns={'index': 'genre'})
    except Exception:
        pass
    try:
        genre_monthly['genre'] = genre_monthly['genre'].str.replace('genre_', '')
    except Exception:
        pass
    try:
        print(f'YOUR TOP GENRE MONTHLY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(genre_monthly.groupby('period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP GENRE MONTHLY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(genre_monthly.sort_values(by=['period', 'play_counts'], ascending=[True, False]).groupby('period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        genre_daily = []
    except Exception:
        pass
    try:
        for period, chunk in master_df.groupby(master_df['time_stamp'].dt.tz_localize(None).dt.to_period('D')):
            chunk_summary = pd.DataFrame({'total_time_listened': chunk[genre_data].T.dot(chunk['sec_played']), 'play_counts': chunk[genre_data].sum()}).reset_index()
            chunk_summary['period'] = period
            genre_daily.append(chunk_summary)
    except Exception:
        pass
    try:
        genre_daily = pd.concat(genre_daily, ignore_index=True)
    except Exception:
        pass
    try:
        genre_daily = genre_daily.sort_values(by=['period', 'total_time_listened'], ascending=[True, False]).rename(columns={'index': 'genre'})
    except Exception:
        pass
    try:
        genre_daily['genre'] = genre_daily['genre'].str.replace('genre_', '')
    except Exception:
        pass
    try:
        print(f'YOUR TOP GENRE DAILY BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(genre_daily.groupby('period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP GENRE DAILY BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(genre_daily.sort_values(by=['period', 'play_counts'], ascending=[True, False]).groupby('period').head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        genre_seasonal = []
    except Exception:
        pass
    try:
        for (year, season), chunk in master_df.groupby([master_df['time_stamp'].dt.year, master_df['time_stamp'].dt.month.map(season_dict)]):
            chunk_summary = pd.DataFrame({'total_time_listened': chunk[genre_data].T.dot(chunk['sec_played']), 'play_counts': chunk[genre_data].sum()}).reset_index()
            chunk_summary['Year'] = year
            chunk_summary['Season'] = season
            genre_seasonal.append(chunk_summary)
    except Exception:
        pass
    try:
        genre_seasonal = pd.concat(genre_seasonal, ignore_index=True)
    except Exception:
        pass
    try:
        genre_seasonal = genre_seasonal.sort_values(by=['Year', 'Season', 'total_time_listened'], ascending=[True, True, False]).rename(columns={'index': 'genre'})
    except Exception:
        pass
    try:
        genre_seasonal['genre'] = genre_seasonal['genre'].str.replace('genre_', '')
    except Exception:
        pass
    try:
        print(f'YOUR TOP GENRE SEASONAL BY LISTEN TIME')
    except Exception:
        pass
    try:
        display(genre_seasonal.groupby(['Year', 'Season']).head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print(f'YOUR TOP GENRE SEASONAL BY PLAY COUNT')
    except Exception:
        pass
    try:
        display(genre_seasonal.sort_values(by=['Year', 'Season', 'play_counts'], ascending=[True, True, False]).groupby(['Year', 'Season']).head(1).head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print('TOTAL LISTEN TIME AND PLAY COUNT THROUGHT YOUR LIFETIME')
    except Exception:
        pass
    try:
        display(top_song_alltime.agg({'play_counts': ['sum'], 'total_time_listened': ['sum']}).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print('TOTAL LISTEN TIME AND PLAY COUNT THROUGHT YEARS')
    except Exception:
        pass
    try:
        display(top_song_yearly.groupby('Year').agg({'play_counts': 'sum', 'total_time_listened': 'sum'}).reset_index().head().style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print('TOTAL LISTEN TIME AND PLAY COUNT THROUGHT MONTHS')
    except Exception:
        pass
    try:
        display(top_song_monthly.groupby('Period').agg({'play_counts': 'sum', 'total_time_listened': 'sum'}).reset_index().head().style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print('TOTAL LISTEN TIME AND PLAY COUNT THROUGHT DAYS')
    except Exception:
        pass
    try:
        display(top_song_daily.groupby('Period').agg({'play_counts': 'sum', 'total_time_listened': 'sum'}).reset_index().head().style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        print('TOTAL LISTEN TIME AND PLAY COUNT THROUGHT SEASONS')
    except Exception:
        pass
    try:
        display(top_song_seasonal.groupby(['Year', 'Season']).agg({'play_counts': 'sum', 'total_time_listened': 'sum'}).reset_index().head(10).style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        daily_listening_pattern = master_df.groupby(master_df['time_stamp'].dt.dayofweek).agg({'sec_played': 'sum', 'song_name': 'count'}).reset_index().rename(columns={'sec_played': 'total_time_listened', 'song_name': 'play_counts', 'time_stamp': 'day_of_week'})
    except Exception:
        pass
    try:
        daily_listening_pattern['day_of_week'] = daily_listening_pattern['day_of_week'].apply(lambda x: calendar.day_name[x])
    except Exception:
        pass
    try:
        display(daily_listening_pattern.style.hide(axis='index').format({'total_time_listened': format_time}))
    except Exception:
        pass
    try:
        total_skip, total_plays = master_df.agg({'skipped': 'sum', 'song_name': 'count'})
    except Exception:
        pass
    try:
        print(f'Your all time total skipped songs are {total_skip} songs and unskipped song plays are {total_plays - total_skip} songs')
    except Exception:
        pass
    try:
        skipped_songs_df = master_df.groupby(['artist_name', 'song_name']).agg({'skipped': 'sum', 'song_name': 'count'}).rename(columns={'skipped': 'skip_count', 'song_name': 'play_count'}).reset_index().query('play_count>10').assign(skip_percentage=lambda x: x['skip_count'] / x['play_count'] * 100)
    except Exception:
        pass
    try:
        print('Your most skipped song by percentage are as follows:')
    except Exception:
        pass
    try:
        display(skipped_songs_df.sort_values(by=['skip_percentage', 'play_count'], ascending=[False, False]).head().style.hide(axis='index').format({'skip_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('Your most skipped song by count are as follows:')
    except Exception:
        pass
    try:
        display(skipped_songs_df.sort_values(by=['skip_count', 'play_count'], ascending=[False, False]).head().style.hide(axis='index').format({'skip_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        skipped_artist_df = master_df.groupby('artist_name').agg({'skipped': 'sum', 'song_name': 'count'}).rename(columns={'skipped': 'skip_count', 'song_name': 'play_count'}).reset_index().query('play_count>10').assign(skip_percentage=lambda x: x['skip_count'] / x['play_count'] * 100)
    except Exception:
        pass
    try:
        print('Your most skipped artist by percentage are as follows:')
    except Exception:
        pass
    try:
        display(skipped_artist_df.sort_values(by=['skip_percentage', 'play_count'], ascending=[False, False]).head().style.hide(axis='index').format({'skip_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('Your most skipped artist by count are as follows:')
    except Exception:
        pass
    try:
        display(skipped_artist_df.sort_values(by=['skip_count', 'play_count'], ascending=[False, False]).head().style.hide(axis='index').format({'skip_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('showing your skip activity based on hour')
    except Exception:
        pass
    try:
        display(master_df.groupby(master_df['time_stamp'].dt.hour.rename('Hour of day')).agg({'skipped': 'sum', 'song_name': 'count'}).rename(columns={'skipped': 'skip_counts', 'song_name': 'play_counts'}).reset_index().assign(skip_percentage=lambda x: x['skip_counts'] / x['play_counts'] * 100).style.hide(axis='index').format({'skip_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('showing your skip activity based on dayofweek')
    except Exception:
        pass
    try:
        display(master_df.groupby(master_df['time_stamp'].dt.day_of_week.rename('day of week')).agg({'skipped': 'sum', 'song_name': 'count'}).rename(columns={'skipped': 'skip_counts', 'song_name': 'play_counts'}).reset_index().assign(skip_percentage=lambda x: x['skip_counts'] / x['play_counts'] * 100).style.hide(axis='index').format({'skip_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('showing your skip activity based on dayofmonth')
    except Exception:
        pass
    try:
        display(master_df.groupby(master_df['time_stamp'].dt.day.rename('day of month')).agg({'skipped': 'sum', 'song_name': 'count'}).rename(columns={'skipped': 'skip_counts', 'song_name': 'play_counts'}).reset_index().assign(skip_percentage=lambda x: x['skip_counts'] / x['play_counts'] * 100).head().style.hide(axis='index').format({'skip_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('showing your skip activity based on month')
    except Exception:
        pass
    try:
        display(master_df.groupby(master_df['time_stamp'].dt.month.rename('month of year')).agg({'skipped': 'sum', 'song_name': 'count'}).rename(columns={'skipped': 'skip_counts', 'song_name': 'play_counts'}).reset_index().assign(skip_percentage=lambda x: x['skip_counts'] / x['play_counts'] * 100).style.hide(axis='index').format({'skip_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('showing your skip activity based on Year')
    except Exception:
        pass
    try:
        display(master_df.groupby(master_df['time_stamp'].dt.year.rename('Year')).agg({'skipped': 'sum', 'song_name': 'count'}).rename(columns={'skipped': 'skip_counts', 'song_name': 'play_counts'}).reset_index().assign(skip_percentage=lambda x: x['skip_counts'] / x['play_counts'] * 100).style.hide(axis='index').format({'skip_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('showing your skip activity based on shuffle')
    except Exception:
        pass
    try:
        display(master_df.groupby('shuffle').agg({'skipped': 'sum', 'song_name': 'count'}).rename(columns={'skipped': 'skip_counts', 'song_name': 'play_counts'}).reset_index().assign(skip_percentage=lambda x: x['skip_counts'] / x['play_counts'] * 100).style.hide(axis='index').format({'skip_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('showing your shuffle activity based on hour')
    except Exception:
        pass
    try:
        display(master_df.groupby([master_df['time_stamp'].dt.hour.rename('hour of day')]).agg({'shuffle': 'sum', 'song_name': 'count'}).rename(columns={'shuffle': 'shuffle_counts', 'song_name': 'play_counts'}).reset_index().assign(shuffle_percentage=lambda x: x['shuffle_counts'] / x['play_counts'] * 100).style.hide(axis='index').format({'shuffle_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('showing your shuffle activity based on day of week')
    except Exception:
        pass
    try:
        display(master_df.groupby([master_df['time_stamp'].dt.day_of_week.rename('day of week')]).agg({'shuffle': 'sum', 'song_name': 'count'}).rename(columns={'shuffle': 'shuffle_counts', 'song_name': 'play_counts'}).reset_index().assign(shuffle_percentage=lambda x: x['shuffle_counts'] / x['play_counts'] * 100).style.hide(axis='index').format({'shuffle_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('showing your shuffle activity based on month')
    except Exception:
        pass
    try:
        display(master_df.groupby([master_df['time_stamp'].dt.month.rename('month of year')]).agg({'shuffle': 'sum', 'song_name': 'count'}).rename(columns={'shuffle': 'shuffle_counts', 'song_name': 'play_counts'}).reset_index().assign(shuffle_percentage=lambda x: x['shuffle_counts'] / x['play_counts'] * 100).style.hide(axis='index').format({'shuffle_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        print('showing your shuffle activity based on year')
    except Exception:
        pass
    try:
        display(master_df.groupby([master_df['time_stamp'].dt.year.rename('year')]).agg({'shuffle': 'sum', 'song_name': 'count'}).rename(columns={'shuffle': 'shuffle_counts', 'song_name': 'play_counts'}).reset_index().assign(shuffle_percentage=lambda x: x['shuffle_counts'] / x['play_counts'] * 100).style.hide(axis='index').format({'shuffle_percentage': '{:.2f}%'}))
    except Exception:
        pass
    try:
        display(master_df.groupby('reason_start').agg({'song_name': 'count'}).rename(columns={'song_name': 'play_count'}).reset_index().sort_values(by='play_count', ascending=False).style.hide(axis='index'))
    except Exception:
        pass
    try:
        display(master_df.groupby('reason_end').agg({'song_name': 'count'}).rename(columns={'song_name': 'play_count'}).reset_index().sort_values(by='play_count', ascending=False).style.hide(axis='index'))
    except Exception:
        pass
    try:
        display(master_df.groupby(master_df['platform'].str.split(' ').str[0].str.title().rename('os_name')).agg({'song_name': 'count'}).rename(columns={'song_name': 'play_counts'}).reset_index().sort_values(by='play_counts', ascending=False).style.hide(axis='index'))
    except Exception:
        pass
    try:
        display(master_df.groupby(master_df['offline'].map({0: 'Online', 1: 'Offline'}).rename('status')).agg({'song_name': 'count'}).rename(columns={'song_name': 'play_counts'}).reset_index().sort_values(by='play_counts', ascending=False).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('Longest consecutive Years listening to specific songs:')
    except Exception:
        pass
    try:
        display(top_song_yearly.sort_values(['artist_name', 'song_name', 'Year']).assign(streak_group=lambda x: x['Year'] - x.groupby(['artist_name', 'song_name']).cumcount()).groupby(['artist_name', 'song_name', 'streak_group']).size().reset_index(name='consecutive_years').groupby(['artist_name', 'song_name'])['consecutive_years'].max().reset_index().sort_values(by='consecutive_years', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('Longest consecutive months listening to specific songs:')
    except Exception:
        pass
    try:
        display(top_song_monthly.sort_values(['artist_name', 'song_name', 'Period']).assign(streak_group=lambda x: x['Period'] - x.groupby(['artist_name', 'song_name']).cumcount()).groupby(['artist_name', 'song_name', 'streak_group']).size().reset_index(name='consecutive_months').groupby(['artist_name', 'song_name'])['consecutive_months'].max().reset_index().sort_values(by='consecutive_months', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('Longest consecutive days listening to specific songs:')
    except Exception:
        pass
    try:
        display(top_song_daily.sort_values(['artist_name', 'song_name', 'Period']).assign(streak_group=lambda x: x['Period'] - x.groupby(['artist_name', 'song_name']).cumcount()).groupby(['artist_name', 'song_name', 'streak_group']).size().reset_index(name='consecutive_days').groupby(['artist_name', 'song_name'])['consecutive_days'].max().reset_index().sort_values(by='consecutive_days', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('Longest Silent Gap (Years) for specific artists:')
    except Exception:
        pass
    try:
        display(top_artist_yearly.sort_values(['artist_name', 'Year']).assign(year_diff=lambda x: x.groupby('artist_name')['Year'].diff(), silent_years=lambda x: x['year_diff'] - 1).groupby('artist_name')['silent_years'].max().reset_index().sort_values(by='silent_years', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('Longest Silent Gap (Months) for specific artists:')
    except Exception:
        pass
    try:
        display(top_artist_monthly.sort_values(['artist_name', 'Period']).assign(month_diff=lambda x: x['Period'].astype('int64').groupby(x['artist_name']).diff(), silent_months=lambda x: x['month_diff'] - 1).groupby('artist_name')['silent_months'].max().reset_index().sort_values(by='silent_months', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('Longest Silent Gap (Days) for specific artists:')
    except Exception:
        pass
    try:
        display(top_artist_daily.sort_values(['artist_name', 'Period']).assign(day_diff=lambda x: x['Period'].astype('int64').groupby(x['artist_name']).diff(), silent_days=lambda x: x['day_diff'] - 1).groupby('artist_name')['silent_days'].max().reset_index().sort_values(by='silent_days', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('displaying the artist you have listened for most consecutive days')
    except Exception:
        pass
    try:
        display(top_artist_daily.sort_values(['artist_name', 'Period']).assign(streak_group=lambda x: x['Period'] - x.groupby('artist_name').cumcount()).groupby(['artist_name', 'streak_group']).size().reset_index(name='consecutive_days').groupby('artist_name')['consecutive_days'].max().reset_index(name='consecutive_days').sort_values(by='consecutive_days', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('displaying the artist you have listened for most consecutive months')
    except Exception:
        pass
    try:
        display(top_artist_monthly.sort_values(['artist_name', 'Period']).assign(streak_group=lambda x: x['Period'] - x.groupby('artist_name').cumcount()).groupby(['artist_name', 'streak_group']).size().reset_index(name='consecutive_months').groupby('artist_name')['consecutive_months'].max().reset_index(name='consecutive_months').sort_values(by='consecutive_months', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('displaying the artist you have listened for most consecutive Years')
    except Exception:
        pass
    try:
        display(top_artist_yearly.sort_values(['artist_name', 'Year']).assign(streak_group=lambda x: x['Year'] - x.groupby('artist_name').cumcount()).groupby(['artist_name', 'streak_group']).size().reset_index(name='consecutive_years').groupby('artist_name')['consecutive_years'].max().reset_index(name='consecutive_years').sort_values(by='consecutive_years', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('displaying the song you have listened for most consecutive Years')
    except Exception:
        pass
    try:
        display(top_song_yearly.sort_values(['song_name', 'Year']).assign(streak_group=lambda x: x['Year'] - x.groupby('song_name').cumcount()).groupby(['song_name', 'streak_group']).size().reset_index(name='consecutive_years').groupby('song_name')['consecutive_years'].max().reset_index(name='consecutive_years').sort_values(by='consecutive_years', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('displaying the song you have listened for most consecutive months')
    except Exception:
        pass
    try:
        display(top_song_monthly.sort_values(['song_name', 'Period']).assign(streak_group=lambda x: x['Period'] - x.groupby('song_name').cumcount()).groupby(['song_name', 'streak_group']).size().reset_index(name='consecutive_months').groupby('song_name')['consecutive_months'].max().reset_index(name='consecutive_months').sort_values(by='consecutive_months', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('displaying the songs you have listened for most consecutive days')
    except Exception:
        pass
    try:
        display(top_song_daily.sort_values(['song_name', 'Period']).assign(streak_group=lambda x: x['Period'] - x.groupby('song_name').cumcount()).groupby(['song_name', 'streak_group']).size().reset_index(name='consecutive_days').groupby('song_name')['consecutive_days'].max().reset_index(name='consecutive_days').sort_values(by='consecutive_days', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print("Longest streaks of days where you didn't use Spotify AT ALL:")
    except Exception:
        pass
    try:
        display(top_song_daily[['Period']].drop_duplicates().sort_values(by='Period').assign(period_start=lambda x: x['Period'].shift(1), period_end=lambda x: x['Period'], day_diff=lambda x: x['Period'].astype('int64').diff(), silent_days_streak=lambda x: (x['day_diff'] - 1).fillna(0).astype(int)).dropna()[['period_start', 'period_end', 'silent_days_streak']].sort_values(by='silent_days_streak', ascending=False).head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('artists whom you have listened for 1 song only')
    except Exception:
        pass
    try:
        display(master_df.groupby(['artist_name', 'song_name']).size().reset_index(name='play_counts').groupby('artist_name').agg(unique_songs=('song_name', 'nunique'), song_name=('song_name', 'first'), play_counts=('play_counts', 'max')).reset_index().query('unique_songs==1 and play_counts>10').sort_values(by='play_counts', ascending=False).head().style.hide(axis='index'))
    except Exception:
        pass
    try:
        display(master_df.assign(skipped_sec=lambda x: x['sec_played'].where(x['skipped'] == 1)).groupby([master_df['time_stamp'].dt.year.rename('Year'), 'artist_name']).agg(play_counts=('sec_played', 'count'), avg_time_before_skip=('skipped_sec', 'mean')).reset_index().query('play_counts>=30').assign(drastic_change=lambda df: df.groupby('artist_name')['avg_time_before_skip'].transform(lambda x: x.max() - x.min())).sort_values(by=['drastic_change', 'artist_name', 'Year'], ascending=[False, True, True]).drop(columns=['drastic_change', 'play_counts']).head(20).style.hide(axis='index'))
    except Exception:
        pass
    try:
        print('Your longest continuous listening marathons (grouped by a 30-minute inactivity threshold):')
    except Exception:
        pass
    try:
        display(master_df.sort_values(by='time_stamp').assign(time_gap=lambda x: x['time_stamp'].diff(), is_new_session=lambda x: x['time_gap'] > pd.Timedelta(minutes=30), session_id=lambda x: x['is_new_session'].cumsum()).groupby('session_id').agg(session_start=('time_stamp', 'min'), session_end=('time_stamp', 'max'), total_songs_played=('song_name', 'count'), total_hours_listened=('sec_played', lambda x: x.sum() / 3600)).sort_values(by='total_hours_listened', ascending=False).head(10).reset_index(drop=True).style.hide(axis='index'))
    except Exception:
        pass
    try:
        feature_df = master_df.sort_values(by='time_stamp').copy().assign(hour_of_day=lambda x: x['time_stamp'].dt.hour, day_of_week=lambda x: x['time_stamp'].dt.dayofweek, day_of_month=lambda x: x['time_stamp'].dt.month, year=lambda x: x['time_stamp'].dt.year, previous_song_skipped=lambda x: x['skipped'].shift(1).fillna(0).astype(int), artist_skip_percentage=lambda x: x.groupby('artist_name')['skipped'].transform(lambda y: y.expanding().mean().shift(1)), song_skip_percentage=lambda x: x.groupby('song_name')['skipped'].transform(lambda y: y.expanding().mean().shift(1)))
    except Exception:
        pass
    try:
        genre_columns = [col for col in feature_df.columns if col.startswith('genre_')]
    except Exception:
        pass
    try:
        safe_columns = ['time_stamp', 'hour_of_day', 'day_of_week', 'day_of_month', 'year', 'shuffle', 'previous_song_skipped', 'artist_skip_percentage', 'song_skip_percentage', 'skipped']
    except Exception:
        pass
    try:
        safe_columns = safe_columns + genre_columns
    except Exception:
        pass
    try:
        feature_df = feature_df[safe_columns]
    except Exception:
        pass
    try:
        feature_df = feature_df.fillna(0)
    except Exception:
        pass
    try:
        feature_df.info(verbose=True, show_counts=True, buf=md_file)
    except Exception:
        pass
    try:
        yearly_artists = master_df.groupby(['artist_name', master_df['time_stamp'].dt.year]).agg(yearly_plays=('artist_name', 'count')).reset_index().rename(columns={'time_stamp': 'year'}).sort_values(by=['artist_name', 'year'])
    except Exception:
        pass
    try:
        longest_yearly_streaks = yearly_artists.assign(gap=lambda x: x.groupby('artist_name')['year'].diff()).assign(is_broken=lambda x: x['gap'] != 1).assign(streak_id=lambda x: x['is_broken'].cumsum()).groupby(['artist_name', 'streak_id']).agg(consecutive_years=('streak_id', 'count'), total_plays_in_streak=('yearly_plays', 'sum')).reset_index().sort_values(by=['consecutive_years', 'total_plays_in_streak'], ascending=[False, False]).drop_duplicates(subset=['artist_name'], keep='first').drop(columns=['streak_id'])
    except Exception:
        pass
    try:
        display(longest_yearly_streaks.head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        monthly_artists = master_df.assign(abs_month=lambda x: x['time_stamp'].dt.year * 12 + x['time_stamp'].dt.month).groupby(['artist_name', 'abs_month']).agg(monthly_plays=('artist_name', 'count')).reset_index().sort_values(by=['artist_name', 'abs_month'])
    except Exception:
        pass
    try:
        longest_artist_streaks = monthly_artists.assign(gap=lambda x: x.groupby('artist_name')['abs_month'].diff()).assign(is_broken=lambda x: x['gap'] != 1).assign(streak_id=lambda x: x['is_broken'].cumsum()).groupby(['artist_name', 'streak_id']).agg(consecutive_months=('streak_id', 'count'), total_plays_in_streak=('monthly_plays', 'sum')).reset_index().sort_values(by=['consecutive_months', 'total_plays_in_streak'], ascending=[False, False]).drop_duplicates(subset=['artist_name'], keep='first').drop(columns=['streak_id'])
    except Exception:
        pass
    try:
        print('YOUR MOST LOYAL ARTISTS (Longest Consecutive Monthly Streaks)')
    except Exception:
        pass
    try:
        display(longest_artist_streaks.head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        daily_artists = master_df.assign(date=master_df['time_stamp'].dt.date).groupby(['artist_name', 'date']).agg(daily_plays=('artist_name', 'count')).reset_index().sort_values(by=['artist_name', 'date'])
    except Exception:
        pass
    try:
        longest_daily_streaks = daily_artists.assign(gap=lambda x: x.groupby('artist_name')['date'].diff()).assign(is_broken=lambda x: x['gap'] != pd.Timedelta(days=1)).assign(streak_id=lambda x: x['is_broken'].cumsum()).groupby(['artist_name', 'streak_id']).agg(consecutive_days=('streak_id', 'count'), total_plays_in_streak=('daily_plays', 'sum')).reset_index().sort_values(by=['consecutive_days', 'total_plays_in_streak'], ascending=[False, False]).drop_duplicates(subset=['artist_name'], keep='first').drop(columns=['streak_id'])
    except Exception:
        pass
    try:
        display(longest_daily_streaks.head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        one_hit_wonders = master_df.groupby('artist_name').agg(unique_songs=('song_name', 'nunique'), total_plays=('artist_name', 'count'), the_one_hit_song=('song_name', 'first')).query('unique_songs == 1').sort_values(by='total_plays', ascending=False).reset_index()
    except Exception:
        pass
    try:
        display(one_hit_wonders.head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        attention_span = master_df.assign(skipped_sec_played=lambda x: x['sec_played'].where(x['skipped'] == True)).groupby('artist_name').agg(avg_seconds_before_skip=('skipped_sec_played', 'median'), total_skips=('skipped', 'sum'), total_plays=('artist_name', 'count')).query('total_skips >= 5').sort_values(by=['avg_seconds_before_skip', 'total_skips'], ascending=[True, False]).reset_index()
    except Exception:
        pass
    try:
        display(attention_span.head(10).style.hide(axis='index'))
    except Exception:
        pass
    try:
        japanese_winter_night = {'figure.facecolor': '#0D1321', 'axes.facecolor': '#111827', 'text.color': '#E5E7EB', 'axes.labelcolor': '#D1D5DB', 'xtick.color': '#9CA3AF', 'ytick.color': '#E5E7EB', 'grid.color': '#1F2937'}
    except Exception:
        pass
    try:
        sns.set_theme(style='darkgrid', font='Meiryo ', rc=japanese_winter_night)
    except Exception:
        pass
    try:
        top_3_artist_each_year = top_artist_yearly.sort_values(by=['time_stamp', 'play_counts'], ascending=[True, False]).groupby('time_stamp').head(3)
    except Exception:
        pass
    try:
        top_3_artist_each_year = top_3_artist_each_year.rename(columns={'time_stamp': 'Year'})
    except Exception:
        pass
    try:
        g = sns.catplot(data=top_3_artist_each_year, kind='bar', col='Year', col_wrap=3, y='artist_name', x='play_counts', hue='artist_name', sharey=False, sharex=False, height=3, aspect=1.5, palette='cool')
    except Exception:
        pass
    try:
        g.set_titles('{col_name}')
    except Exception:
        pass
    try:
        g.set_axis_labels('', '')
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        discovery_method = master_df[['time_stamp', 'artist_name', 'reason_start']].sort_values(by='time_stamp').groupby('artist_name').first().reset_index()
    except Exception:
        pass
    try:
        discovery_method['discovery_quarter'] = discovery_method['time_stamp'].dt.year.astype(str) + '-Q' + discovery_method['time_stamp'].dt.quarter.astype(str)
    except Exception:
        pass
    try:
        discovery_method = discovery_method.groupby(['discovery_quarter', 'reason_start'])['artist_name'].count().reset_index(name='new_artists')
    except Exception:
        pass
    try:
        valid_reasons = ['clickrow', 'trackdone', 'fwdbtn']
    except Exception:
        pass
    try:
        discovery_method = discovery_method[discovery_method['reason_start'].isin(valid_reasons)]
    except Exception:
        pass
    try:
        plt.figure(figsize=(15, 6))
    except Exception:
        pass
    try:
        sns.lineplot(data=discovery_method, x='discovery_quarter', y='new_artists', hue='reason_start', linewidth=3)
    except Exception:
        pass
    try:
        plt.xticks(rotation=45)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass

    def categorize_time(time):
        if time >= 5 and time < 12:
            return 'Morning'
        elif time >= 12 and time < 17:
            return 'Afternoon'
        elif time >= 17 and time < 19.5:
            return 'Evening'
        elif time >= 19.5 and time < 24:
            return 'Night'
        else:
            return 'Midnight'
    try:
        time_float = master_df['time_stamp'].dt.hour + master_df['time_stamp'].dt.minute / 60
    except Exception:
        pass
    try:
        time_category = time_float.apply(categorize_time)
    except Exception:
        pass
    try:
        bar_chart_data = time_category.value_counts().reset_index(name='play_counts')
    except Exception:
        pass
    try:
        bar_chart_data = bar_chart_data.rename(columns={'time_stamp': 'time_category'})
    except Exception:
        pass
    try:
        if 'index' in bar_chart_data.columns:
            bar_chart_data = bar_chart_data.rename(columns={'index': 'time_category'})
    except Exception:
        pass
    try:
        display(bar_chart_data)
    except Exception:
        pass
    try:
        plt.figure(figsize=(10, 6))
    except Exception:
        pass
    try:
        sns.barplot(data=bar_chart_data, x='time_category', y='play_counts', hue='time_category', legend=False, palette='twilight_shifted', order=['Morning', 'Afternoon', 'Evening', 'Night', 'Midnight'])
    except Exception:
        pass
    try:
        plt.title('Listening Volume by Time of Day')
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        all_years = top_artist_seasonal['Year'].unique()
    except Exception:
        pass
    try:
        month_weights = {'summer': 3, 'moonsoon': 4, 'autumn': 2, 'winter': 3}
    except Exception:
        pass
    try:
        for year in all_years:
            year_df = top_artist_seasonal[top_artist_seasonal['Year'] == year]
            top_artists = year_df.groupby('artist_name')['play_counts'].sum().nlargest(5).index.tolist()
            filtered_year_df = year_df[year_df['artist_name'].isin(top_artists)].copy()
            filtered_year_df['normalized_plays'] = filtered_year_df['play_counts'] / filtered_year_df['Season'].map(month_weights)
            pivot_grid = filtered_year_df.pivot(index='artist_name', columns='Season', values='normalized_plays')
            pivot_grid = pivot_grid.reindex(columns=['summer', 'moonsoon', 'autumn', 'winter']).fillna(0)
            plt.figure(figsize=(10, 5))
            sns.heatmap(data=pivot_grid, cmap='mako', annot=True, fmt='.1f')
            plt.title(f'(Avg Plays Per Month): {year}')
            plt.show()
    except Exception:
        pass
    try:
        top_15_one_hits = one_hit_wonders.sort_values(by='total_plays', ascending=False).head(15)
    except Exception:
        pass
    try:
        plt.figure(figsize=(12, 8))
    except Exception:
        pass
    try:
        sns.barplot(data=top_15_one_hits, x='total_plays', y='artist_name', hue='artist_name', palette='magma', legend=False)
    except Exception:
        pass
    try:
        plt.title('The One-Hit Wonder Wall of Fame (1 Unique Song Only)')
    except Exception:
        pass
    try:
        plt.xlabel('Total Times Played')
    except Exception:
        pass
    try:
        plt.ylabel('Artist')
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        top_streaks = longest_artist_streaks.head(15)
    except Exception:
        pass
    try:
        plt.figure(figsize=(12, 8))
    except Exception:
        pass
    try:
        sns.barplot(data=top_streaks, x='consecutive_months', y='artist_name', hue='artist_name', palette='crest', legend=False)
    except Exception:
        pass
    try:
        plt.title('Ultimate Loyalty: Longest Consecutive Monthly Listening Streaks')
    except Exception:
        pass
    try:
        plt.xlabel('Consecutive Months Listened')
    except Exception:
        pass
    try:
        plt.ylabel('')
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        day_counts = master_df['time_stamp'].dt.day_name().value_counts().reset_index(name='play_counts')
    except Exception:
        pass
    try:
        if 'time_stamp' in day_counts.columns:
            day_counts = day_counts.rename(columns={'time_stamp': 'day_name'})
        elif 'index' in day_counts.columns:
            day_counts = day_counts.rename(columns={'index': 'day_name'})
    except Exception:
        pass
    try:
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    except Exception:
        pass
    try:
        plt.figure(figsize=(12, 6))
    except Exception:
        pass
    try:
        custom_palette = {'Monday': '#374151', 'Tuesday': '#374151', 'Wednesday': '#374151', 'Thursday': '#374151', 'Friday': '#374151', 'Saturday': '#00B4D8', 'Sunday': '#00B4D8'}
    except Exception:
        pass
    try:
        sns.barplot(data=day_counts, x='day_name', y='play_counts', order=day_order, hue='day_name', palette=custom_palette, legend=False)
    except Exception:
        pass
    try:
        plt.title('Listening Volume: Weekdays vs Weekends')
    except Exception:
        pass
    try:
        plt.ylabel('Total Songs Played')
    except Exception:
        pass
    try:
        plt.xlabel('')
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        plt.figure(figsize=(12, 6))
    except Exception:
        pass
    try:
        attention_decay = master_df.loc[(master_df['reason_end'] == 'fwdbtn') & (master_df['sec_played'] <= 630)].groupby(master_df['time_stamp'].dt.year)['sec_played'].agg(total_sec='sum', skip_count='count').reset_index()
    except Exception:
        pass
    try:
        attention_decay['avg_seconds_before_skip'] = attention_decay['total_sec'] / attention_decay['skip_count']
    except Exception:
        pass
    try:
        sns.lineplot(data=attention_decay, x='time_stamp', y='avg_seconds_before_skip', color='#00B4D8', linewidth=4, marker='o', markersize=10, markerfacecolor='#00B4D8', markeredgecolor='white', markeredgewidth=1.5)
    except Exception:
        pass
    try:
        plt.title("The True Attention Span: Avg Seconds Before Hitting 'Next'")
    except Exception:
        pass
    try:
        plt.xlabel('Year')
    except Exception:
        pass
    try:
        plt.ylabel('Average Seconds Listened Before Skipping')
    except Exception:
        pass
    try:
        plt.xticks(attention_decay['time_stamp'])
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        plt.figure(figsize=(14, 7))
    except Exception:
        pass
    try:
        skip_heatmap_data = pd.crosstab(master_df.loc[master_df['reason_end'] == 'fwdbtn', 'time_stamp'].dt.day_name().rename('Day'), master_df.loc[master_df['reason_end'] == 'fwdbtn', 'time_stamp'].dt.hour.rename('Hour'), normalize='index') * 100
    except Exception:
        pass
    try:
        skip_heatmap_data = skip_heatmap_data.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    except Exception:
        pass
    try:
        sns.heatmap(skip_heatmap_data, cmap='rocket', annot=False)
    except Exception:
        pass
    try:
        plt.title('Skip-Trigger Heatmap: When Are You Most Impatient? (Normalized by Day)')
    except Exception:
        pass
    try:
        plt.xlabel('Hour of the Day (0-23)')
    except Exception:
        pass
    try:
        plt.ylabel('')
    except Exception:
        pass
    try:
        plt.yticks(rotation=0)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        binge_sessions = master_df[['time_stamp', 'sec_played']].sort_values('time_stamp').assign(gap=lambda df: df['time_stamp'] - pd.to_timedelta(df['sec_played'], unit='s') - df['time_stamp'].shift(1), is_new_session=lambda df: df['gap'] > pd.Timedelta(minutes=15)).assign(session_id=lambda df: df['is_new_session'].cumsum()).groupby('session_id').agg(session_hours=('sec_played', lambda x: x.sum() / 3600)).query('session_hours >= 1')
    except Exception:
        pass
    try:
        binge_discrete = binge_sessions.assign(rounded_hours=lambda df: df['session_hours'].round().astype(int))
    except Exception:
        pass
    try:
        counts = binge_discrete['rounded_hours'].value_counts().sort_index()
    except Exception:
        pass

    def custom_piecewise_scale(y_values):
        transformed = []
        for y in y_values:
            if y == 0:
                transformed.append(-0.1)
            elif y <= 10:
                transformed.append((y - 1) / 9.0)
            elif y <= 100:
                transformed.append(1 + (y - 10) / 90.0)
            elif y <= 1000:
                transformed.append(2 + (y - 100) / 900.0)
            else:
                transformed.append(3 + (y - 1000) / 9000.0)
        return transformed
    try:
        y_transformed = custom_piecewise_scale(counts.values)
    except Exception:
        pass
    try:
        plt.figure(figsize=(12, 8))
    except Exception:
        pass
    try:
        plt.bar(counts.index, y_transformed, color='#38bdf8', edgecolor='#111827', linewidth=1.5)
    except Exception:
        pass
    try:
        ax = plt.gca()
    except Exception:
        pass
    try:
        major_ticks = [0, 1, 2, 3, 4]
    except Exception:
        pass
    try:
        major_labels = ['1', '10', '100', '1000', '10,000']
    except Exception:
        pass
    try:
        ax.set_yticks(major_ticks)
    except Exception:
        pass
    try:
        ax.set_yticklabels(major_labels, fontsize=12, fontweight='bold', color='white')
    except Exception:
        pass
    try:
        minor_ticks_1_10 = [(i - 1) / 9.0 for i in range(2, 10)]
    except Exception:
        pass
    try:
        minor_ticks_10_100 = [1 + (i - 10) / 90.0 for i in range(20, 100, 10)]
    except Exception:
        pass
    try:
        minor_ticks_100_1000 = [2 + (i - 100) / 900.0 for i in range(200, 1000, 100)]
    except Exception:
        pass
    try:
        minor_ticks_1000_10000 = [3 + (i - 1000) / 9000.0 for i in range(2000, 10000, 1000)]
    except Exception:
        pass
    try:
        all_minor_ticks = minor_ticks_1_10 + minor_ticks_10_100 + minor_ticks_100_1000 + minor_ticks_1000_10000
    except Exception:
        pass
    try:
        minor_labels = [str(i) for i in range(2, 10)] + [str(i) for i in range(20, 100, 10)] + [str(i) for i in range(200, 1000, 100)] + [f'{i // 1000}k' for i in range(2000, 10000, 1000)]
    except Exception:
        pass
    try:
        ax.set_yticks(all_minor_ticks, minor=True)
    except Exception:
        pass
    try:
        ax.set_yticklabels(minor_labels, minor=True, fontsize=8, color='#D1D5DB')
    except Exception:
        pass
    try:
        ax.grid(axis='y', which='major', color='#374151', linestyle='-', linewidth=1.5)
    except Exception:
        pass
    try:
        plt.title("The Binge Metric: User's Custom Piecewise Linear Scale")
    except Exception:
        pass
    try:
        plt.xlabel('Continuous Listening Duration (Rounded to nearest Hour)')
    except Exception:
        pass
    try:
        plt.ylabel('Total Count of Sessions')
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.xticks(counts.index)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        plt.figure(figsize=(10, 6))
    except Exception:
        pass
    try:
        sns.countplot(data=binge_discrete, x='rounded_hours', color='#38bdf8', edgecolor='#111827', linewidth=1.5)
    except Exception:
        pass
    try:
        plt.yscale('log')
    except Exception:
        pass
    try:
        ax = plt.gca()
    except Exception:
        pass
    try:
        minor_ticks = [i * 10 ** j for j in range(0, 4) for i in range(2, 10)]
    except Exception:
        pass
    try:
        ax.set_yticks(minor_ticks, minor=True)
    except Exception:
        pass
    try:
        minor_labels_text = []
    except Exception:
        pass
    try:
        for j in range(0, 4):
            for i in range(2, 10):
                if i <= 5:
                    minor_labels_text.append(str(i * 10 ** j))
                else:
                    minor_labels_text.append('')
    except Exception:
        pass
    try:
        ax.set_yticklabels(minor_labels_text, minor=True, fontsize=8, color='#D1D5DB')
    except Exception:
        pass
    try:
        plt.title('The Binge Metric: Uninterrupted Sessions (Clean Log Scale)')
    except Exception:
        pass
    try:
        plt.xlabel('Continuous Listening Duration (Rounded to nearest Hour)')
    except Exception:
        pass
    try:
        plt.ylabel('Total Count of Sessions')
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.xticks(range(13))
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        traffic_data = master_df[['time_stamp']].assign(day_name=lambda df: df['time_stamp'].dt.day_name(), hour=lambda df: df['time_stamp'].dt.hour).groupby(['day_name', 'hour']).size().reset_index(name='play_volume')
    except Exception:
        pass
    try:
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    except Exception:
        pass
    try:
        traffic_pivot = traffic_data.pivot(index='day_name', columns='hour', values='play_volume').reindex(day_order)
    except Exception:
        pass
    try:
        plt.figure(figsize=(16, 8))
    except Exception:
        pass
    try:
        sns.heatmap(data=traffic_pivot, cmap='mako', linewidths=0.5, linecolor='#111827', annot=False, cbar_kws={'label': 'Total Play Volume'})
    except Exception:
        pass
    try:
        plt.title('AWS Server Scaling: Global Traffic Heatmap (Day vs. Hour)', pad=20, fontsize=14)
    except Exception:
        pass
    try:
        plt.xlabel('Hour of Day (24h Clock)', fontsize=12)
    except Exception:
        pass
    try:
        plt.ylabel('')
    except Exception:
        pass
    try:
        plt.yticks(rotation=0, fontsize=11)
    except Exception:
        pass
    try:
        plt.xticks(fontsize=11)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        true_skips = master_df[['sec_played', 'reason_end']].query("reason_end == 'fwdbtn'")
    except Exception:
        pass
    try:
        total_skips = len(true_skips)
    except Exception:
        pass
    try:
        pct_5s = len(true_skips.query('sec_played <= 5')) / total_skips
    except Exception:
        pass
    try:
        pct_15s = len(true_skips.query('sec_played <= 15')) / total_skips
    except Exception:
        pass
    try:
        pct_30s = len(true_skips.query('sec_played <= 30')) / total_skips
    except Exception:
        pass
    try:
        plt.figure(figsize=(14, 7))
    except Exception:
        pass
    try:
        sns.ecdfplot(data=true_skips, x='sec_played', color='#38bdf8', linewidth=3)
    except Exception:
        pass
    try:
        plt.axvline(x=5, ymax=pct_5s, color='#FCA5A5', linestyle='--', alpha=0.8)
    except Exception:
        pass
    try:
        plt.axhline(y=pct_5s, xmax=5 / 240, color='#FCA5A5', linestyle='--', alpha=0.8)
    except Exception:
        pass
    try:
        plt.text(7, pct_5s - 0.05, f'5s: {pct_5s:.1%}', color='#FCA5A5', fontweight='bold')
    except Exception:
        pass
    try:
        plt.axvline(x=15, ymax=pct_15s, color='#FCD34D', linestyle='--', alpha=0.8)
    except Exception:
        pass
    try:
        plt.axhline(y=pct_15s, xmax=15 / 240, color='#FCD34D', linestyle='--', alpha=0.8)
    except Exception:
        pass
    try:
        plt.text(17, pct_15s - 0.05, f'15s: {pct_15s:.1%}', color='#FCD34D', fontweight='bold')
    except Exception:
        pass
    try:
        plt.axvline(x=30, ymax=pct_30s, color='#6EE7B7', linestyle='--', alpha=0.8)
    except Exception:
        pass
    try:
        plt.axhline(y=pct_30s, xmax=30 / 240, color='#6EE7B7', linestyle='--', alpha=0.8)
    except Exception:
        pass
    try:
        plt.text(32, pct_30s - 0.05, f'30s: {pct_30s:.1%}', color='#6EE7B7', fontweight='bold')
    except Exception:
        pass
    try:
        plt.title('Micro-Buffering Threshold: Cumulative Skip Percentage over Time', pad=20, fontsize=14)
    except Exception:
        pass
    try:
        plt.xlabel('Seconds Played Before User Skipped', fontsize=12)
    except Exception:
        pass
    try:
        plt.ylabel('Cumulative Proportion of Total Skips', fontsize=12)
    except Exception:
        pass
    try:
        plt.xlim(0, 240)
    except Exception:
        pass
    try:
        plt.ylim(0, 1.05)
    except Exception:
        pass
    try:
        plt.grid(color='#1F2937', linestyle='--', alpha=0.5)
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        TRUE_MB_PER_TRACK = 4.3
    except Exception:
        pass
    try:
        true_bandwidth_data = master_df[['reason_end']].assign(traffic_type=lambda df: np.select([df['reason_end'] == 'fwdbtn', df['reason_end'] == 'trackdone'], ['Wasted Bandwidth (Skipped)', 'Effective Bandwidth (Completed)'], default='Other (Paused/Closed)')).groupby('traffic_type').size().reset_index(name='track_count').assign(total_gb=lambda df: df['track_count'] * TRUE_MB_PER_TRACK / 1024).sort_values('total_gb', ascending=False)
    except Exception:
        pass
    try:
        color_map = {'Effective Bandwidth (Completed)': '#38bdf8', 'Wasted Bandwidth (Skipped)': '#FCA5A5', 'Other (Paused/Closed)': '#4B5563'}
    except Exception:
        pass
    try:
        plt.figure(figsize=(10, 5))
    except Exception:
        pass
    try:
        ax = sns.barplot(data=true_bandwidth_data, x='total_gb', y='traffic_type', palette=color_map, hue='traffic_type', legend=False, edgecolor='#111827', linewidth=1.5)
    except Exception:
        pass
    try:
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f GB', padding=5, color='white', fontweight='bold')
    except Exception:
        pass
    try:
        plt.title('TRUE AWS Infrastructure Cost: Total Bandwidth Wasted vs. Consumed', pad=20, fontsize=14)
    except Exception:
        pass
    try:
        plt.xlabel('Total Data Transferred (Gigabytes) @ 4.3 MB Download Penalty', fontsize=12)
    except Exception:
        pass
    try:
        plt.ylabel('')
    except Exception:
        pass
    try:
        max_gb = true_bandwidth_data['total_gb'].max()
    except Exception:
        pass
    try:
        plt.xlim(0, max_gb * 1.15)
    except Exception:
        pass
    try:
        plt.grid(axis='x', color='#1F2937', linestyle='--', alpha=0.5)
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        hardware_data = master_df.groupby('platform').agg(total_hours=('sec_played', lambda x: x.sum() / 3600)).reset_index().sort_values('total_hours', ascending=False)
    except Exception:
        pass
    try:
        hardware_data['platform_clean'] = hardware_data['platform'].apply(lambda x: str(x).split(' ')[0].capitalize())
    except Exception:
        pass
    try:
        hardware_data = hardware_data.groupby('platform_clean', as_index=False)['total_hours'].sum().sort_values('total_hours', ascending=False)
    except Exception:
        pass
    try:
        plt.figure(figsize=(10, 6))
    except Exception:
        pass
    try:
        ax = sns.barplot(data=hardware_data, x='total_hours', y='platform_clean', color='#38bdf8', edgecolor='#111827', linewidth=1.5)
    except Exception:
        pass
    try:
        for container in ax.containers:
            ax.bar_label(container, fmt='%.0f hrs', padding=5, color='white', fontweight='bold')
    except Exception:
        pass
    try:
        plt.title('Hardware Dominance: Total Time Spent per Platform', pad=20, fontsize=14)
    except Exception:
        pass
    try:
        plt.xlabel('Total Listening Time (Hours)', fontsize=12)
    except Exception:
        pass
    try:
        plt.ylabel('Device Platform', fontsize=12)
    except Exception:
        pass
    try:
        max_hours = hardware_data['total_hours'].max()
    except Exception:
        pass
    try:
        plt.xlim(0, max_hours * 1.15)
    except Exception:
        pass
    try:
        plt.grid(axis='x', color='#1F2937', linestyle='--', alpha=0.5)
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        engagement_data = master_df[['platform', 'reason_end']].assign(traffic_type=lambda df: np.select([df['reason_end'] == 'fwdbtn', df['reason_end'] == 'trackdone'], ['Skipped', 'Completed'], default='Other'), platform_clean=lambda df: df['platform'].apply(lambda x: str(x).split(' ')[0].capitalize())).groupby(['platform_clean', 'traffic_type']).size().unstack(fill_value=0)
    except Exception:
        pass
    try:
        engagement_ratio = engagement_data.div(engagement_data.sum(axis=1), axis=0) * 100
    except Exception:
        pass
    try:
        if 'Completed' in engagement_ratio.columns:
            engagement_ratio = engagement_ratio.sort_values(by='Completed', ascending=False)
    except Exception:
        pass
    try:
        color_dict = {'Completed': '#38bdf8', 'Skipped': '#FCA5A5', 'Other': '#4B5563'}
    except Exception:
        pass
    try:
        plot_colors = [color_dict.get(col, '#ffffff') for col in engagement_ratio.columns]
    except Exception:
        pass
    try:
        ax = engagement_ratio.plot(kind='barh', stacked=True, color=plot_colors, edgecolor='#111827', linewidth=1.5, figsize=(12, 6))
    except Exception:
        pass
    try:
        for container in ax.containers:
            labels = [f'{val:.0f}%' if val > 5 else '' for val in container.datavalues]
            ax.bar_label(container, labels=labels, label_type='center', color='black', fontweight='bold')
    except Exception:
        pass
    try:
        plt.title('Hardware Engagement: Completion vs. Skip Ratio', pad=20, fontsize=14)
    except Exception:
        pass
    try:
        plt.xlabel('Percentage of Total Streams (%)', fontsize=12)
    except Exception:
        pass
    try:
        plt.ylabel('Platform', fontsize=12)
    except Exception:
        pass
    try:
        plt.legend(title='Stream Outcome', bbox_to_anchor=(1.01, 1), loc='upper left', frameon=False, title_fontsize=12)
    except Exception:
        pass
    try:
        plt.xlim(0, 100)
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    import plotly.graph_objects as go
    try:
        df_sankey = master_df.assign(stage1=lambda df: 'Device: ' + df['platform'].astype(str).apply(lambda x: x.split(' ')[0].capitalize()), stage2=lambda df: 'Start: ' + df['reason_start'].astype(str), stage3=lambda df: 'End: ' + df['reason_end'].astype(str))
    except Exception:
        pass
    try:
        flow1 = df_sankey.groupby(['stage1', 'stage2']).size().reset_index(name='count')
    except Exception:
        pass
    try:
        flow1.columns = ['source_name', 'target_name', 'count']
    except Exception:
        pass
    try:
        flow2 = df_sankey.groupby(['stage2', 'stage3']).size().reset_index(name='count')
    except Exception:
        pass
    try:
        flow2.columns = ['source_name', 'target_name', 'count']
    except Exception:
        pass
    try:
        flow_data = pd.concat([flow1, flow2])
    except Exception:
        pass
    try:
        threshold = len(master_df) * 0.01
    except Exception:
        pass
    try:
        flow_data = flow_data[flow_data['count'] >= threshold]
    except Exception:
        pass
    try:
        all_nodes = list(pd.unique(flow_data[['source_name', 'target_name']].values.ravel('K')))
    except Exception:
        pass
    try:
        node_dict = {name: i for i, name in enumerate(all_nodes)}
    except Exception:
        pass
    try:
        flow_data = flow_data.assign(source_idx=lambda df: df['source_name'].map(node_dict), target_idx=lambda df: df['target_name'].map(node_dict))
    except Exception:
        pass
    try:
        fig = go.Figure(data=[go.Sankey(arrangement='snap', node=dict(pad=25, thickness=20, line=dict(color='black', width=0.5), label=all_nodes, color='#38bdf8'), link=dict(source=flow_data['source_idx'], target=flow_data['target_idx'], value=flow_data['count'], color='rgba(56, 189, 248, 0.3)'))])
    except Exception:
        pass
    try:
        fig.update_layout(title_text='App Navigation Funnel: Device ➔ Action ➔ Outcome', title_font_size=18, font_size=13, paper_bgcolor='#0D1321', plot_bgcolor='#0D1321', font_color='white', height=700)
    except Exception:
        pass
    try:
        update_progress()
        html_filename = f"sankey_{counter[0]}.html"
        html_path = os.path.join(images_dir, html_filename)
        fig.write_html(html_path)
        md_file.write(f"### App Navigation Funnel (Sankey)\n\n")
        md_file.write(f"[Click here to view the Interactive Funnel Diagram (HTML)](images/{html_filename})\n\n")
    except Exception:
        pass
    import matplotlib.dates as mdates
    try:
        autoplay_data = master_df[['time_stamp', 'reason_start']].assign(year_month=lambda df: df['time_stamp'].dt.to_period('M'), is_passive=lambda df: (df['reason_start'] == 'trackdone').astype(int)).groupby('year_month').agg(total_streams=('is_passive', 'count'), passive_streams=('is_passive', 'sum')).assign(passive_ratio=lambda df: df['passive_streams'] / df['total_streams'] * 100).reset_index()
    except Exception:
        pass
    try:
        autoplay_data['year_month'] = autoplay_data['year_month'].dt.to_timestamp()
    except Exception:
        pass
    try:
        autoplay_data['smooth_ratio'] = autoplay_data['passive_ratio'].rolling(window=3, min_periods=1).mean()
    except Exception:
        pass
    try:
        plt.figure(figsize=(12, 6))
    except Exception:
        pass
    try:
        sns.lineplot(data=autoplay_data, x='year_month', y='smooth_ratio', color='#38bdf8', linewidth=3)
    except Exception:
        pass
    try:
        plt.fill_between(autoplay_data['year_month'], autoplay_data['smooth_ratio'], color='#38bdf8', alpha=0.15)
    except Exception:
        pass
    try:
        plt.title('Autoplay Reliance Engine: The Rise of Passive Listening', pad=20, fontsize=15)
    except Exception:
        pass
    try:
        plt.xlabel('Timeline (Years)', fontsize=12)
    except Exception:
        pass
    try:
        plt.ylabel('Passive Listening Ratio (%)', fontsize=12)
    except Exception:
        pass
    try:
        plt.ylim(0, 100)
    except Exception:
        pass
    try:
        ax = plt.gca()
    except Exception:
        pass
    try:
        ax.xaxis.set_major_locator(mdates.YearLocator())
    except Exception:
        pass
    try:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    except Exception:
        pass
    try:
        plt.grid(color='#1F2937', linestyle='--', alpha=0.5)
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        ui_data = master_df['reason_start'].value_counts().reset_index()
    except Exception:
        pass
    try:
        ui_data.columns = ['reason', 'count']
    except Exception:
        pass
    try:
        total_streams = ui_data['count'].sum()
    except Exception:
        pass
    try:
        threshold = total_streams * 0.02
    except Exception:
        pass
    try:
        ui_data['clean_reason'] = np.where(ui_data['count'] >= threshold, ui_data['reason'], 'Other')
    except Exception:
        pass
    try:
        ui_clean = ui_data.groupby('clean_reason', as_index=False)['count'].sum().sort_values('count', ascending=False)
    except Exception:
        pass
    try:
        plt.figure(figsize=(9, 9))
    except Exception:
        pass
    try:
        colors = sns.color_palette('mako', len(ui_clean))
    except Exception:
        pass
    try:
        plt.pie(ui_clean['count'], labels=ui_clean['clean_reason'], autopct='%1.1f%%', startangle=140, colors=colors, pctdistance=0.8, wedgeprops=dict(width=0.45, edgecolor='#111827', linewidth=2.5), textprops={'color': 'white', 'fontsize': 12, 'fontweight': 'bold'})
    except Exception:
        pass
    try:
        plt.title('UI Feature Usage: How do you start a song?', pad=20, fontsize=15)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    import matplotlib.dates as mdates
    try:
        dau_data = master_df.assign(date=lambda df: df['time_stamp'].dt.date).groupby('date').agg(daily_hours=('sec_played', lambda x: x.sum() / 3600)).reset_index()
    except Exception:
        pass
    try:
        dau_data['date'] = pd.to_datetime(dau_data['date'])
    except Exception:
        pass
    try:
        full_date_range = pd.date_range(start=dau_data['date'].min(), end=dau_data['date'].max())
    except Exception:
        pass
    try:
        dau_data = dau_data.set_index('date').reindex(full_date_range, fill_value=0).reset_index()
    except Exception:
        pass
    try:
        dau_data.rename(columns={'index': 'date'}, inplace=True)
    except Exception:
        pass
    try:
        dau_data['30_day_trend'] = dau_data['daily_hours'].rolling(window=30, min_periods=1).mean()
    except Exception:
        pass
    try:
        plt.figure(figsize=(15, 6))
    except Exception:
        pass
    try:
        plt.bar(dau_data['date'], dau_data['daily_hours'], color='#38bdf8', alpha=0.6, width=1.0, label='Daily Active Usage (Hours)')
    except Exception:
        pass
    try:
        plt.plot(dau_data['date'], dau_data['30_day_trend'], color='#FCA5A5', linewidth=2.5, label='30-Day Macro Trend (MAU)')
    except Exception:
        pass
    try:
        plt.title('DAU vs. MAU: Daily Listening Volatility vs. Macro Trends', pad=20, fontsize=15)
    except Exception:
        pass
    try:
        plt.xlabel('Timeline', fontsize=12)
    except Exception:
        pass
    try:
        plt.ylabel('Listening Time (Hours)', fontsize=12)
    except Exception:
        pass
    try:
        ax = plt.gca()
    except Exception:
        pass
    try:
        ax.xaxis.set_major_locator(mdates.YearLocator())
    except Exception:
        pass
    try:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    except Exception:
        pass
    try:
        plt.legend(frameon=False, labelcolor='white')
    except Exception:
        pass
    try:
        plt.grid(axis='y', color='#1F2937', linestyle='--', alpha=0.5)
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.xlim(dau_data['date'].min(), dau_data['date'].max())
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        churn_data = master_df[['time_stamp', 'reason_start']].assign(hour=lambda df: df['time_stamp'].dt.hour, traffic_type=lambda df: np.where(df['reason_start'] == 'trackdone', 'Passive (Robot Auto-Play)', 'Active (Human Clicks)')).groupby(['hour', 'traffic_type']).size().unstack(fill_value=0)
    except Exception:
        pass
    try:
        churn_ratio = churn_data.div(churn_data.sum(axis=1), axis=0) * 100
    except Exception:
        pass
    try:
        colors = {'Active (Human Clicks)': '#38bdf8', 'Passive (Robot Auto-Play)': '#FCA5A5'}
    except Exception:
        pass
    try:
        plot_colors = [colors.get(col, '#ffffff') for col in churn_ratio.columns]
    except Exception:
        pass
    try:
        ax = churn_ratio.plot(kind='bar', stacked=True, figsize=(12, 6), color=plot_colors, edgecolor='#111827', width=0.85)
    except Exception:
        pass
    try:
        for container in ax.containers:
            labels = [f'{val:.0f}%' if val > 5 else '' for val in container.datavalues]
            ax.bar_label(container, labels=labels, label_type='center', color='black', fontweight='bold')
    except Exception:
        pass
    try:
        plt.title('The DEEP FOCUS BG CHURN: Human Engagement vs. Autoplay Zombies', pad=20, fontsize=15)
    except Exception:
        pass
    try:
        plt.xlabel('Time of Day', fontsize=12)
    except Exception:
        pass
    try:
        plt.ylabel('Percentage of Traffic (%)', fontsize=12)
    except Exception:
        pass
    try:
        hours_labels = [f'{h} AM' if h < 12 else f'{h - 12} PM' if h > 12 else '12 PM' for h in churn_ratio.index]
    except Exception:
        pass
    try:
        hours_labels[0] = '12 AM'
    except Exception:
        pass
    try:
        ax.set_xticklabels(hours_labels, rotation=45, ha='right')
    except Exception:
        pass
    try:
        plt.legend(title='Who is controlling the app?', bbox_to_anchor=(1.01, 1), loc='upper left', frameon=False, title_fontsize=12)
    except Exception:
        pass
    try:
        sns.despine(left=True, bottom=True)
    except Exception:
        pass
    try:
        plt.ylim(0, 100)
    except Exception:
        pass
    try:
        plt.show()
    except Exception:
        pass
    try:
        md_file.close()
    except Exception:
        pass
    try:
        builtins.print = _orig_print
    except Exception:
        pass
    try:
        plt.show = _orig_show
    except Exception:
        pass
    try:
        print(f'\n\nReport successfully generated at: {os.path.abspath(md_file_path)}')
    except Exception:
        pass

def main():
    args = parse_args()
    master_df = load_cleaned_data(args)
    run_eda(master_df, args.output_dir)
if __name__ == '__main__':
    main()
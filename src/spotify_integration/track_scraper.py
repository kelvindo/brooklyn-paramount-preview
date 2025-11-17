import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
from datetime import datetime
from typing import List, Dict
import time

# --- Configuration ---
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = 'http://localhost:3000/callback'

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")

# Initialize Spotify client (no special scopes needed)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=""
))

def get_latest_artist_list_filename() -> str:
    """
    Get the latest artist_list JSON filename in format: artist_list_YY-MM-DD.json
    If today's file doesn't exist, find the most recent one.
    """
    data_processed_dir = 'data/processed'
    today = datetime.now()
    date_str = today.strftime('%y-%m-%d')
    filename = f'artist_list_{date_str}.json'
    filepath = os.path.join(data_processed_dir, filename)
    
    if os.path.exists(filepath):
        return filepath
    
    # If today's file doesn't exist, try to find the most recent one
    print(f"File {filename} not found. Searching for most recent artist_list JSON file...")
    json_files = [f for f in os.listdir(data_processed_dir) if f.startswith('artist_list_') and f.endswith('.json')]
    
    if not json_files:
        raise FileNotFoundError(f"No artist_list JSON files found in {data_processed_dir}")
    
    # Sort by filename (which includes date) and get the latest
    json_files.sort(reverse=True)
    latest_file = os.path.join(data_processed_dir, json_files[0])
    print(f"Using file: {latest_file}")
    return latest_file


def extract_date_from_filename(filename: str) -> str:
    """
    Extract the date string (YY-MM-DD) from a filename like artist_list_YY-MM-DD.json
    Returns the date string or raises ValueError if format doesn't match.
    """
    # Extract just the filename without path
    basename = os.path.basename(filename)
    
    # Expected format: artist_list_YY-MM-DD.json
    if basename.startswith('artist_list_') and basename.endswith('.json'):
        date_part = basename[len('artist_list_'):-len('.json')]
        # Validate date format (YY-MM-DD)
        if len(date_part) == 8 and date_part[2] == '-' and date_part[5] == '-':
            return date_part
    
    raise ValueError(f"Could not extract date from filename: {filename}")


def load_artist_data(input_file: str) -> Dict[str, str]:
    """Load artist IDs and names from JSON file. Returns only distinct artists (deduplicated by artist ID)."""
    artist_data = {}
    total_entries = 0
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            artists = json.load(file)
            total_entries = len(artists)
            for artist in artists:
                artist_id = artist.get('id')
                artist_name = artist.get('name')
                if artist_id and artist_name:
                    # Dictionary automatically handles duplicates - same artist_id will overwrite previous entry
                    artist_data[artist_id] = artist_name
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{input_file}': {e}")
    
    if total_entries > 0:
        unique_count = len(artist_data)
        if total_entries > unique_count:
            print(f"Found {total_entries} artist entries, {unique_count} unique artists (deduplicated by ID)")
        else:
            print(f"Found {unique_count} unique artists")
    
    return artist_data


def get_artist_top_tracks(artist_id: str) -> List[Dict]:
    """Retrieves the top tracks for a given artist ID."""
    try:
        top_tracks = sp.artist_top_tracks(artist_id)
        return top_tracks['tracks']
    except spotipy.SpotifyException as e:
        print(f"Error getting top tracks for artist ID {artist_id}: {e}")
        return []


def write_tracks_to_json(tracks_data: List[Dict], output_filename: str):
    """Writes track data to a JSON file."""
    if not tracks_data:
        print("No track data to write.")
        return

    try:
        # Prepare filtered track data
        filtered_tracks = []
        for track in tracks_data:
            try:
                filtered_track = {
                    'artist_id': track.get('artist_id'),
                    'artist_name': track.get('artist_name'),
                    'track_id': track.get('id'),
                    'track_name': track.get('name'),
                    'popularity': track.get('popularity'),
                    'duration_ms': track.get('duration_ms'),
                }
                filtered_tracks.append(filtered_track)
            except Exception as e:
                print(f"Error preparing data: {e}. Data: {track}")
                continue

        # Ensure output directory exists
        output_dir = os.path.dirname(output_filename)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_filename, 'w', encoding='utf-8') as outfile:
            json.dump(filtered_tracks, outfile, indent=2, ensure_ascii=False)

        print(f"Track metadata saved to {output_filename}")

    except Exception as e:
        print(f"Error writing to JSON file: {e}")


def main():
    input_file = get_latest_artist_list_filename()
    date_str = extract_date_from_filename(input_file)
    output_file = f'data/processed/track_list_{date_str}.json'

    artist_data = load_artist_data(input_file)
    if not artist_data:
        print("No artist data found. Exiting.")
        return

    all_tracks = []
    for artist_id, artist_name in artist_data.items():
        tracks = get_artist_top_tracks(artist_id)
        # Add artist information to each track
        for track in tracks:
            track['artist_id'] = artist_id
            track['artist_name'] = artist_name
        print(artist_name)
        all_tracks.extend(tracks)  # Accumulate all tracks
        time.sleep(0.5)

    write_tracks_to_json(all_tracks, output_file)


if __name__ == "__main__":
    main()
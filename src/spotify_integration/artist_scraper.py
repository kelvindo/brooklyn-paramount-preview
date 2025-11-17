import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
from datetime import datetime
from typing import List, Dict, Tuple

# Get credentials from environment variables
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = 'http://localhost:3000/callback'

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")

# Initialize Spotify client (no special scopes needed for searching)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=""  # No specific scope required for searching
))

def get_latest_json_filename() -> str:
    """
    Get the JSON filename for today's date in format: brooklyn_paramount_shows_YY-MM-DD.json
    If today's file doesn't exist, find the most recent one.
    """
    data_raw_dir = 'data/raw'
    today = datetime.now()
    date_str = today.strftime('%y-%m-%d')
    filename = f'brooklyn_paramount_shows_{date_str}.json'
    filepath = os.path.join(data_raw_dir, filename)
    
    if os.path.exists(filepath):
        return filepath
    
    # If today's file doesn't exist, try to find the most recent one
    print(f"File {filename} not found. Searching for most recent JSON file...")
    json_files = [f for f in os.listdir(data_raw_dir) if f.startswith('brooklyn_paramount_shows_') and f.endswith('.json')]
    
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {data_raw_dir}")
    
    # Sort by filename (which includes date) and get the latest
    json_files.sort(reverse=True)
    latest_file = os.path.join(data_raw_dir, json_files[0])
    print(f"Using file: {latest_file}")
    return latest_file


def extract_date_from_filename(filename: str) -> str:
    """
    Extract the date string (YY-MM-DD) from a filename like brooklyn_paramount_shows_YY-MM-DD.json
    Returns the date string or raises ValueError if format doesn't match.
    """
    # Extract just the filename without path
    basename = os.path.basename(filename)
    
    # Expected format: brooklyn_paramount_shows_YY-MM-DD.json
    if basename.startswith('brooklyn_paramount_shows_') and basename.endswith('.json'):
        date_part = basename[len('brooklyn_paramount_shows_'):-len('.json')]
        # Validate date format (YY-MM-DD)
        if len(date_part) == 8 and date_part[2] == '-' and date_part[5] == '-':
            return date_part
    
    raise ValueError(f"Could not extract date from filename: {filename}")


def load_shows_and_artists(filename: str) -> List[Tuple[str, str]]:
    """
    Loads shows and artist names from a JSON file.
    Returns a list of tuples (show_title, artist_name) since shows can have multiple artists.
    """
    show_artist_pairs = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            shows = json.load(file)
            for show in shows:
                show_title = show.get('title', '')
                artists = show.get('artists', [])
                for artist in artists:
                    artist_name = artist.get('name', '')
                    if artist_name:
                        show_artist_pairs.append((show_title, artist_name))
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{filename}': {e}")
        return []
    
    return show_artist_pairs

def search_and_save_artists(input_filename: str, output_filename: str):
    """Searches for artists on Spotify and saves their metadata to a JSON file."""
    show_artist_pairs = load_shows_and_artists(input_filename)
    if not show_artist_pairs:
        print("No shows/artists found in input file.")
        return

    artist_data_list = []  # Store all artist data dictionaries

    for show_title, artist_name in show_artist_pairs:
        try:
            results = sp.search(q=f"artist:{artist_name}", type='artist', limit=1)  # Limit to 1 result
            if results['artists']['items']:
                artist_data = results['artists']['items'][0]  # Get the first artist found
                # Create filtered data with only the fields we want
                filtered_data = {
                    'show_title': show_title,
                    'search_term': artist_name,
                    'id': artist_data.get('id'),
                    'name': artist_data.get('name'),
                    'popularity': artist_data.get('popularity'),
                    'followers': artist_data.get('followers', {}).get('total'),  # followers is nested
                    'genres': artist_data.get('genres', [])
                }
                artist_data_list.append(filtered_data)
                print(f"Found: {artist_name} - ID: {filtered_data['id']}")

            else:
                print(f"Could not find artist: {artist_name}")

        except spotipy.SpotifyException as e:
            print(f"Error searching for {artist_name}: {e}")

    # --- Write to JSON ---
    if artist_data_list:
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_filename)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_filename, 'w', encoding='utf-8') as outfile:
                json.dump(artist_data_list, outfile, indent=2, ensure_ascii=False)
            
            print(f"Artist metadata saved to {output_filename}")
            print(f"Found {len(artist_data_list)} artists from {len(set(pair[0] for pair in show_artist_pairs))} shows")

        except Exception as e:
            print(f"Error writing to JSON file: {e}")
    else:
        print("No artist data to write.")

def main():
    input_file = get_latest_json_filename()
    date_str = extract_date_from_filename(input_file)
    output_file = f'data/processed/artist_list_{date_str}.json'
    search_and_save_artists(input_file, output_file)


if __name__ == "__main__":
    main()
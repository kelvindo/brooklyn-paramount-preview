import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import csv
from typing import List, Dict, Set
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

def load_artist_data(input_file: str) -> Dict[str, str]:
    """Load artist IDs and names from CSV file."""
    artist_data = {}
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                artist_data[row['id']] = row['name']
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    return artist_data


def get_artist_top_tracks(artist_id: str) -> List[Dict]:
    """Retrieves the top tracks for a given artist ID."""
    try:
        top_tracks = sp.artist_top_tracks(artist_id)
        return top_tracks['tracks']
    except spotipy.SpotifyException as e:
        print(f"Error getting top tracks for artist ID {artist_id}: {e}")
        return []


def write_tracks_to_csv(tracks_data: List[Dict], output_filename: str):
    """Writes track data to a CSV file."""
    if not tracks_data:
        print("No track data to write.")
        return

    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
            # Define desired fields (and order)
            fieldnames = [
                'artist_id', 'artist_name', 'track_id', 'track_name',
                'popularity', 'duration_ms',
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for track in tracks_data:
              try:
                # Extract and format relevant data
                row = {
                    'artist_id': track['artist_id'],  # Use the artist_id we passed in
                    'artist_name': track['artist_name'],  # Use the artist_name we passed in
                    'track_id': track['id'],
                    'track_name': track['name'],
                    'popularity': track['popularity'],
                    'duration_ms': track['duration_ms'],
                }
                writer.writerow(row)
              except Exception as e:
                    print(f"Error preparing data: {e}. Data: {track}")
                    continue

        print(f"Track metadata saved to {output_filename}")

    except Exception as e:
        print(f"Error writing to CSV file: {e}")


def main():
    input_file = 'data/processed/artist_list.csv'
    output_file = 'data/processed/track_list.csv'

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

    write_tracks_to_csv(all_tracks, output_file)


if __name__ == "__main__":
    main()
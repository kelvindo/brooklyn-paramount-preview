import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import csv
from typing import List, Dict, Set

# --- Configuration ---
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = 'http://localhost:3000/callback'
PLAYLIST_NAME = "Brooklyn Paramount"

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")

# Initialize Spotify client (requires playlist-modify scope)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="playlist-modify-public playlist-modify-private user-library-read"  # Correct scopes
))


def load_track_ids(filename: str) -> List[str]:
    """Loads track IDs from a CSV file."""
    track_ids = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                track_ids.append(row['track_id'])  # 'track_id' is the column
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except KeyError as e:
        print(f"Error: Required column {e} not found in CSV.")
        return []
    return track_ids


def get_or_create_playlist(playlist_name: str) -> str:
    """Gets the ID of an existing playlist or creates a new one."""
    user_id = sp.me()['id']
    playlists = sp.current_user_playlists()

    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            print(f"Playlist '{playlist_name}' found (ID: {playlist['id']}).")
            return playlist['id']

    # Playlist not found, create it
    print(f"Playlist '{playlist_name}' not found. Creating...")
    new_playlist = sp.user_playlist_create(user_id, playlist_name, public=False, description="Tracks from Brooklyn Paramount artists")
    print(f"Playlist '{playlist_name}' created (ID: {new_playlist['id']}).")
    return new_playlist['id']


def add_tracks_to_playlist(playlist_id: str, track_ids: List[str]):
    """Adds tracks to a Spotify playlist, handling batches of 100."""
    user_id = sp.me()['id']
    # Spotify API limits adding tracks to 100 at a time
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i + 100]
        # Ensure tracks are valid Spotify URIs.  Filtering here avoids errors later.
        batch_uris = [f"spotify:track:{track_id}" for track_id in batch]
        try:
            sp.user_playlist_add_tracks(user_id, playlist_id, batch_uris)
            print(f"Added {len(batch_uris)} tracks to playlist.")
        except spotipy.SpotifyException as e:
            print(f"Error adding tracks: {e}")
            # Consider adding more specific error handling (e.g., retry)

def clear_playlist(sp, playlist_id):
    """Remove all tracks from a playlist"""
    try:
        # Get current tracks in playlist
        results = sp.playlist_items(playlist_id)
        if results['items']:
            # Get list of track URIs
            track_uris = [item['track']['uri'] for item in results['items']]
            # Remove all tracks
            sp.playlist_remove_all_occurrences_of_items(playlist_id, track_uris)
            print(f"Cleared {len(track_uris)} tracks from playlist")
    except Exception as e:
        print(f"Error clearing playlist: {e}")

def main():
    input_file = 'data/processed/track_list.csv'
    track_ids = load_track_ids(input_file)

    if not track_ids:
        print("No track IDs found. Exiting.")
        return

    playlist_id = get_or_create_playlist(PLAYLIST_NAME)
    
    # Clear existing tracks from playlist
    clear_playlist(sp, playlist_id)
    
    # Add new tracks
    add_tracks_to_playlist(playlist_id, track_ids)
    print("Playlist synchronization complete.")


if __name__ == "__main__":
    main()
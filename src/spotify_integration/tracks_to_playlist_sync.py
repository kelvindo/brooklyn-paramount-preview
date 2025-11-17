import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
import argparse
from datetime import datetime
from typing import List, Set

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


def get_latest_combined_data_filename() -> str:
    """
    Get the latest combined_data JSON filename in format: combined_data_YY-MM-DD.json
    If today's file doesn't exist, find the most recent one.
    """
    data_final_dir = 'data/final'
    if not os.path.exists(data_final_dir):
        raise FileNotFoundError(f"Directory '{data_final_dir}' does not exist. Run combine_data.py first.")
    
    today = datetime.now()
    date_str = today.strftime('%y-%m-%d')
    filename = f'combined_data_{date_str}.json'
    filepath = os.path.join(data_final_dir, filename)
    
    if os.path.exists(filepath):
        return filepath
    
    # If today's file doesn't exist, try to find the most recent one
    print(f"File {filename} not found. Searching for most recent combined_data JSON file...")
    json_files = [f for f in os.listdir(data_final_dir) if f.startswith('combined_data_') and f.endswith('.json')]
    
    if not json_files:
        raise FileNotFoundError(f"No combined_data JSON files found in {data_final_dir}")
    
    # Sort by filename (which includes date) and get the latest
    json_files.sort(reverse=True)
    latest_file = os.path.join(data_final_dir, json_files[0])
    print(f"Using file: {latest_file}")
    return latest_file


def load_track_ids_from_combined_data(filename: str, first_artist_only: bool = False) -> List[str]:
    """
    Loads track IDs from combined data JSON file.
    
    Args:
        filename: Path to combined_data JSON file
        first_artist_only: If True, only include tracks from the first artist of each show.
                          If False, include tracks from all artists.
    
    Returns:
        List of unique track IDs (deduplicated)
    """
    track_ids = []
    seen_shows: Set[str] = set()
    seen_artists: Set[str] = set()
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            shows = json.load(file)
            
            for show in shows:
                show_title = show.get('title', '')
                
                # Skip duplicate shows (by title)
                if show_title in seen_shows:
                    continue
                seen_shows.add(show_title)
                
                artists = show.get('artists', [])
                
                # If first_artist_only, only process the first artist
                artists_to_process = [artists[0]] if first_artist_only and artists else artists
                
                for artist in artists_to_process:
                    spotify_id = artist.get('spotify_id')
                    
                    # Skip artists without Spotify data
                    if not spotify_id:
                        continue
                    
                    # Skip duplicate artists (by spotify_id)
                    if spotify_id in seen_artists:
                        continue
                    seen_artists.add(spotify_id)
                    
                    # Collect track IDs from this artist
                    tracks = artist.get('tracks', [])
                    for track in tracks:
                        track_id = track.get('track_id')
                        if track_id:
                            track_ids.append(track_id)
    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{filename}': {e}")
        return []
    
    # Remove duplicate track IDs while preserving order
    seen_tracks: Set[str] = set()
    unique_track_ids = []
    for track_id in track_ids:
        if track_id not in seen_tracks:
            seen_tracks.add(track_id)
            unique_track_ids.append(track_id)
    
    return unique_track_ids


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
    parser = argparse.ArgumentParser(
        description='Sync tracks from combined data to Spotify playlist',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add tracks from all artists
  python tracks_to_playlist_sync.py
  
  # Add tracks from first artist only (headliner)
  python tracks_to_playlist_sync.py --first-artist-only
        """
    )
    parser.add_argument(
        '--first-artist-only',
        action='store_true',
        help='Only include tracks from the first artist of each show (headliner only)'
    )
    
    args = parser.parse_args()
    
    input_file = get_latest_combined_data_filename()
    track_ids = load_track_ids_from_combined_data(input_file, first_artist_only=args.first_artist_only)

    if not track_ids:
        print("No track IDs found. Exiting.")
        return

    mode = "first artist only" if args.first_artist_only else "all artists"
    print(f"Loaded {len(track_ids)} unique track IDs from {input_file} ({mode} mode)")
    
    playlist_id = get_or_create_playlist(PLAYLIST_NAME)
    
    # Clear existing tracks from playlist
    clear_playlist(sp, playlist_id)
    
    # Add new tracks
    add_tracks_to_playlist(playlist_id, track_ids)
    print("Playlist synchronization complete.")


if __name__ == "__main__":
    main()
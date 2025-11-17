import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import random
import re
import sys
import os
import argparse
from typing import List, Dict

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = 'http://localhost:3000/callback'

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-modify-playback-state user-read-playback-state user-read-currently-playing"
))


def extract_playlist_id(playlist_url: str) -> str:
    """Extract playlist ID from Spotify playlist URL."""
    # Pattern to match Spotify playlist URLs
    pattern = r'https://open\.spotify\.com/playlist/([a-zA-Z0-9]+)'
    match = re.search(pattern, playlist_url)
    
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid Spotify playlist URL format")


def get_playlist_tracks(playlist_id: str) -> List[Dict]:
    """Get all tracks from a Spotify playlist."""
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    
    # Handle pagination to get all tracks
    while results:
        for item in results['items']:
            if item['track'] and item['track']['id']:  # Ensure track exists and has ID
                tracks.append({
                    'id': item['track']['id'],
                    'uri': item['track']['uri'],
                    'name': item['track']['name'],
                    'artist': ', '.join([artist['name'] for artist in item['track']['artists']]),
                    'album': item['track']['album']['name'],
                    'duration_ms': item['track']['duration_ms']
                })
        
        # Get next page if exists
        if results['next']:
            results = sp.next(results)
        else:
            break
    
    return tracks


def get_device_id():
    """Gets the ID of the first active Spotify device, with retries."""
    device_id = None
    attempts = 0
    max_attempts = 5

    while attempts < max_attempts and not device_id:
        devices = sp.devices()
        if devices and devices['devices']:
            device_id = devices['devices'][0]['id']
            break
        else:
            print("No active devices found. Please open Spotify on a device and try again...")
            time.sleep(2)
            attempts += 1
    
    return device_id


def play_next_track(tracks: List[Dict], track_index: int, device_id: str, random_start: bool = True) -> Dict:
    """Play the next track from the shuffled list and return the selected track."""
    if not tracks or track_index >= len(tracks):
        print("No more tracks available to play.")
        return None
    
    # Get the next track from the shuffled list
    selected_track = tracks[track_index]
    
    try:
        print(f"Now playing: {selected_track['name']} by {selected_track['artist']} (Album: {selected_track['album']})")
        # Start playback to load the track
        sp.start_playback(uris=[selected_track['uri']], device_id=device_id)
        
        if random_start:
            # Immediately pause to avoid giving away the beginning
            sp.pause_playback(device_id=device_id)
            
            # Wait for the track to load
            time.sleep(1)
            
            # Calculate random position based on song length
            # Skip first 10 seconds and last 10 seconds to avoid intro/outro
            song_duration = selected_track['duration_ms']
            min_position = int(song_duration * 0.10)  # 10%
            max_position = int(song_duration * 0.75) # 75%
            
            random_position = random.randint(min_position, max_position)
            sp.seek_track(random_position, device_id=device_id)
            
            # Resume playback from the random position
            sp.start_playback(device_id=device_id)
            
            song_length_sec = song_duration // 1000
            random_position_sec = random_position // 1000
            print(f"Seeking to {random_position_sec}s of {song_length_sec}s ({random_position_sec/song_length_sec*100:.1f}% through the song)")
        else:
            print("Playing from the beginning")
        
        return selected_track
    except spotipy.SpotifyException as e:
        print(f"Error playing track {selected_track['name']}: {e}")
        if e.http_status == 404:
            print("Playback error. Device likely disconnected.")
            return None
        return selected_track


def main():
    """Main function to run the song quiz."""
    parser = argparse.ArgumentParser(description='Spotify Song Quiz - Play random songs from a playlist')
    parser.add_argument('playlist_url', help='Spotify playlist URL')
    parser.add_argument('--mode', choices=['beginning', 'random'], default='random',
                        help='Start songs from beginning or random position (default: random)')
    
    args = parser.parse_args()
    
    playlist_url = args.playlist_url
    random_start = args.mode == 'random'
    
    try:
        # Extract playlist ID from URL
        playlist_id = extract_playlist_id(playlist_url)
        print(f"Extracted playlist ID: {playlist_id}")
        
        # Get all tracks from playlist
        print("Fetching playlist tracks...")
        tracks = get_playlist_tracks(playlist_id)
        
        if not tracks:
            print("No playable tracks found in the playlist.")
            sys.exit(1)
        
        print(f"Found {len(tracks)} tracks in the playlist.")
        
        # Shuffle the tracks to avoid repeats
        random.shuffle(tracks)
        track_index = 0
        
        # Get active device
        device_id = get_device_id()
        if not device_id:
            print("No active Spotify device found. Please open Spotify on a device and try again.")
            sys.exit(1)
        
        mode_text = "random position" if random_start else "beginning"
        print(f"Starting song quiz in '{args.mode}' mode! Songs will start from {mode_text}.")
        print("Press Enter to skip to the next song, 'q' to quit.")
        
        # Play first track
        current_track = play_next_track(tracks, track_index, device_id, random_start)
        track_index += 1
        
        # Main game loop
        while True:
            if track_index >= len(tracks):
                print("You've heard all songs in the playlist! Reshuffling...")
                random.shuffle(tracks)
                track_index = 0
            
            user_input = input("Press Enter for next song, or 'q' to quit: ").strip().lower()
            
            if user_input == 'q':
                print("Thanks for playing!")
                break
            elif user_input == '':  # Enter key pressed
                current_track = play_next_track(tracks, track_index, device_id, random_start)
                if current_track is None:  # Device disconnected
                    break
                track_index += 1
            else:
                print("Invalid input. Press Enter for next song or 'q' to quit.")
    
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except spotipy.SpotifyException as e:
        print(f"Spotify API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

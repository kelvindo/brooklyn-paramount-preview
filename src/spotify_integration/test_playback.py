import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import random
import csv
from typing import List
import os

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = 'http://localhost:3000/callback'

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-modify-playback-state user-read-playback-state user-read-currently-playing"  # Added currently-playing scope
))


def load_artists(filename: str) -> List[str]:
    """Loads artist names from a CSV file."""
    artists = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                artists.append(row['Artist'])
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []  # Return an empty list if the file doesn't exist
    return artists

def get_device_id():
    """Gets the ID of the first active Spotify device, with retries."""
    devices = None
    device_id = None
    attempts = 0
    max_attempts = 5

    while attempts < max_attempts and not device_id:
        devices = sp.devices()
        if devices and devices['devices']:
            device_id = devices['devices'][0]['id']
            break
        else:
            print("No active devices found. Waiting...")
            time.sleep(2)
            attempts += 1
    return device_id

def sample_artist(artist_name: str, device_id: str):
    """Samples tracks from a given artist."""
    try:
        results = sp.search(q=f"artist:{artist_name}", type='artist')
        if not results['artists']['items']:
            print(f"Could not find artist: {artist_name}")
            return

        artist_id = results['artists']['items'][0]['id']
        top_tracks = sp.artist_top_tracks(artist_id)

        if not top_tracks['tracks']:
            print(f"No top tracks found for {artist_name}")
            return

        print(f"Sampling tracks for: {artist_name}")
        for i, track in enumerate(top_tracks['tracks']):
            print(f"  Track {i+1}: {track['name']}")
            try:
                sp.start_playback(uris=[track['uri']], device_id=device_id)
                time.sleep(3) # Initial 3 second play

                for _ in range(10):  # Up to 5 skips per track
                    skip_to = random.randint(10000, 30000)  # Skip 10-30 seconds (in ms)
                    current_pos = get_playback_position()
                    if current_pos is None: # if we can't get the playback position. try again
                        continue;
                    
                    sp.seek_track(current_pos + skip_to)
                    time.sleep(5)  # Play 5 seconds after skip

            except spotipy.SpotifyException as e:
                print(f"Error during playback of {track['name']}: {e}")
                if e.http_status == 404:  # check specifically for 404
                    print("Playback error. Device likely disconnected.  Stopping.")
                    return #stop entirely
                # Other error handling as needed.

            if i + 1 < len(top_tracks['tracks']): #check if we should continue to next track
                user_input = input("Press Enter to continue to the next track, 's' to skip to the next artist, or 'q' to quit: ").strip().lower()
                if user_input == 's':
                    return  # Skip to next artist
                if user_input == 'q':
                    exit() #exit entirely

    except Exception as e:
            print(f"An error occurred while getting artist top tracks: {e}")


def get_playback_position():
    """Gets the current playback position in milliseconds.  Handles potential errors."""
    try:
        playback_state = sp.current_playback()
        if playback_state and playback_state['is_playing']:
            return playback_state['progress_ms']
        else:
            return None  # Not playing or no active device
    except spotipy.SpotifyException as e:
        print(f"Error getting playback position: {e}")
        return None


def main():
    """Main function to control the song sampler."""
    artists = load_artists('data/processed/show_title_to_artist.csv')
    if not artists:
        return

    random.shuffle(artists)
    device_id = get_device_id()

    if not device_id:
        print("No active Spotify device found. Exiting.")
        return

    for artist in artists:
        sample_artist(artist, device_id)
        user_input = input("Press Enter to continue to the next artist, or 'q' to quit: ").strip().lower()
        if user_input == 'q':
            break

if __name__ == "__main__":
    main()
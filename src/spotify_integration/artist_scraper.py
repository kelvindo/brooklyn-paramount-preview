import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import csv
import json  # For pretty-printing JSON (optional, but helpful)
from typing import List, Dict

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

def load_shows_and_artists(filename: str) -> Dict[str, str]:
    """
    Loads shows and artist names from a CSV file.
    Returns a dictionary mapping show titles to artist names.
    """
    show_to_artist = {}
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                show_title = row['Show Title']  # assuming 'title' is the column name for shows
                artist = row['Artist']     # assuming 'Artist' is the column name
                show_to_artist[show_title] = artist
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return {}
    except KeyError as e:
        print(f"Error: Required column {e} not found in CSV.")
        return {}
    
    return show_to_artist

def search_and_save_artists(input_filename: str, output_filename: str):
    """Searches for artists on Spotify and saves their metadata to a CSV."""
    shows_and_artists = load_shows_and_artists(input_filename)
    if not shows_and_artists:
        return

    artist_data_list = []  # Store all artist data dictionaries

    for show_title, artist_name in shows_and_artists.items():
        try:
            results = sp.search(q=f"artist:{artist_name}", type='artist', limit=1)  # Limit to 1 result
            if results['artists']['items']:
                artist_data = results['artists']['items'][0]  # Get the first artist found
                # Add the show title and search term to the artist data
                artist_data['show_title'] = show_title
                artist_data['search_term'] = artist_name
                artist_data_list.append(artist_data)

                # (Optional) Pretty-print the JSON data for inspection
                # print(json.dumps(artist_data, indent=4))
                print(f"Found: {artist_name} - ID: {artist_data['id']}")

            else:
                print(f"Could not find artist: {artist_name}")

        except spotipy.SpotifyException as e:
            print(f"Error searching for {artist_name}: {e}")

    # --- Write to CSV ---
    if artist_data_list: #make sure artist_data_list is not empty
      try:
          # Define the output fields and their order
          DESIRED_FIELDS = [
              'show_title',
              'search_term',
              'id',
              'name',
              'popularity',
              'followers',
              'genres'
          ]
          
          with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=DESIRED_FIELDS)
                writer.writeheader()

                for artist_data in artist_data_list:
                    # Create a new dict with only the fields we want
                    filtered_data = {
                        'show_title': artist_data.get('show_title'),
                        'search_term': artist_data.get('search_term'),
                        'id': artist_data.get('id'),
                        'name': artist_data.get('name'),
                        'popularity': artist_data.get('popularity'),
                        'followers': artist_data.get('followers', {}).get('total'),  # followers is nested
                        'genres': artist_data.get('genres', [])
                    }
                    writer.writerow(filtered_data)

          print(f"Artist metadata saved to {output_filename}")

      except Exception as e:
        print(f"Error writing to CSV file: {e}")
    else:
        print("No artist data to write.")

def main():
    input_file = 'data/processed/show_title_to_artist.csv'
    output_file = 'data/processed/artist_list.csv'
    search_and_save_artists(input_file, output_file)


if __name__ == "__main__":
    main()
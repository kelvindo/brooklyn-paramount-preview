"""
Combine show, artist, and track data into a single comprehensive JSON file.

This script reads the latest files from each step of the pipeline and combines
them into a unified structure where shows contain their artists and artists contain their tracks.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional


def get_latest_json_file(directory: str, prefix: str) -> Optional[str]:
    """
    Get the latest JSON file matching the prefix pattern.
    Returns the full path to the file or None if not found.
    """
    if not os.path.exists(directory):
        return None
    
    json_files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith('.json')]
    
    if not json_files:
        return None
    
    # Sort by filename (which includes date) and get the latest
    json_files.sort(reverse=True)
    return os.path.join(directory, json_files[0])


def extract_date_from_filename(filename: str) -> str:
    """
    Extract the date string (YY-MM-DD) from a filename.
    Works with brooklyn_paramount_shows, artist_list, or track_list prefixes.
    """
    basename = os.path.basename(filename)
    
    # Try different prefixes
    prefixes = ['brooklyn_paramount_shows_', 'artist_list_', 'track_list_']
    for prefix in prefixes:
        if basename.startswith(prefix) and basename.endswith('.json'):
            date_part = basename[len(prefix):-len('.json')]
            # Validate date format (YY-MM-DD)
            if len(date_part) == 8 and date_part[2] == '-' and date_part[5] == '-':
                return date_part
    
    raise ValueError(f"Could not extract date from filename: {filename}")


def load_shows(shows_file: str) -> List[Dict]:
    """Load shows data from JSON file."""
    try:
        with open(shows_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Shows file '{shows_file}' not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in shows file '{shows_file}': {e}")
        return []


def load_artists(artists_file: str) -> Dict[str, Dict]:
    """
    Load artists data from JSON file.
    Returns a dictionary mapping artist_id to artist data.
    Also creates a mapping by show_title for linking.
    """
    try:
        with open(artists_file, 'r', encoding='utf-8') as f:
            artists_list = json.load(f)
        
        # Create mappings: by artist_id and by show_title
        artists_by_id = {}
        artists_by_show = {}
        
        for artist in artists_list:
            artist_id = artist.get('id')
            show_title = artist.get('show_title')
            
            if artist_id:
                artists_by_id[artist_id] = artist
            
            if show_title:
                if show_title not in artists_by_show:
                    artists_by_show[show_title] = []
                artists_by_show[show_title].append(artist)
        
        return {
            'by_id': artists_by_id,
            'by_show': artists_by_show
        }
    except FileNotFoundError:
        print(f"Error: Artists file '{artists_file}' not found.")
        return {'by_id': {}, 'by_show': {}}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in artists file '{artists_file}': {e}")
        return {'by_id': {}, 'by_show': {}}


def load_tracks(tracks_file: str) -> Dict[str, List[Dict]]:
    """
    Load tracks data from JSON file.
    Returns a dictionary mapping artist_id to list of tracks.
    """
    try:
        with open(tracks_file, 'r', encoding='utf-8') as f:
            tracks_list = json.load(f)
        
        tracks_by_artist = {}
        for track in tracks_list:
            artist_id = track.get('artist_id')
            if artist_id:
                if artist_id not in tracks_by_artist:
                    tracks_by_artist[artist_id] = []
                tracks_by_artist[artist_id].append(track)
        
        return tracks_by_artist
    except FileNotFoundError:
        print(f"Error: Tracks file '{tracks_file}' not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in tracks file '{tracks_file}': {e}")
        return {}


def combine_data(shows: List[Dict], artists: Dict, tracks: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Combine shows, artists, and tracks into a unified structure.
    Each show will contain its artists, and each artist will contain its tracks.
    """
    combined_shows = []
    
    for show in shows:
        show_title = show.get('title', '')
        show_artists = show.get('artists', [])
        
        # Create enhanced show object
        enhanced_show = {
            'title': show_title,
            'date': show.get('date'),
            'ticket_url': show.get('ticket_url'),
            'artists': []
        }
        
        # Match artists from the show with Spotify artist data
        for show_artist in show_artists:
            artist_name = show_artist.get('name', '')
            
            # Find matching Spotify artist data by show_title
            spotify_artists = artists['by_show'].get(show_title, [])
            
            # Try to find exact match by name
            matched_spotify_artist = None
            for spotify_artist in spotify_artists:
                if spotify_artist.get('search_term', '').lower() == artist_name.lower():
                    matched_spotify_artist = spotify_artist
                    break
            
            # If no exact match, use first artist from this show
            if not matched_spotify_artist and spotify_artists:
                matched_spotify_artist = spotify_artists[0]
            
            # Combine original artist data with Spotify data
            enhanced_artist = {
                'name': artist_name,
                'image_url': show_artist.get('image_url'),
                'genre': show_artist.get('genre'),
            }
            
            # Add Spotify metadata if found
            if matched_spotify_artist:
                artist_id = matched_spotify_artist.get('id')
                enhanced_artist.update({
                    'spotify_id': artist_id,
                    'spotify_name': matched_spotify_artist.get('name'),
                    'popularity': matched_spotify_artist.get('popularity'),
                    'followers': matched_spotify_artist.get('followers'),
                    'spotify_genres': matched_spotify_artist.get('genres', []),
                    'tracks': tracks.get(artist_id, []) if artist_id else []
                })
            else:
                enhanced_artist['tracks'] = []
            
            enhanced_show['artists'].append(enhanced_artist)
        
        combined_shows.append(enhanced_show)
    
    return combined_shows


def main():
    """Main execution function."""
    print("=" * 60)
    print("Combining Show, Artist, and Track Data")
    print("=" * 60)
    
    # Find latest files
    shows_file = get_latest_json_file('data/raw', 'brooklyn_paramount_shows_')
    artists_file = get_latest_json_file('data/processed', 'artist_list_')
    tracks_file = get_latest_json_file('data/processed', 'track_list_')
    
    if not shows_file:
        print("Error: No shows file found in data/raw/")
        return
    
    if not artists_file:
        print("Error: No artists file found in data/processed/")
        return
    
    if not tracks_file:
        print("Error: No tracks file found in data/processed/")
        return
    
    print(f"\nUsing files:")
    print(f"  Shows: {shows_file}")
    print(f"  Artists: {artists_file}")
    print(f"  Tracks: {tracks_file}")
    
    # Extract date from shows file (use as reference date)
    try:
        date_str = extract_date_from_filename(shows_file)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Load data
    print("\nLoading data...")
    shows = load_shows(shows_file)
    artists = load_artists(artists_file)
    tracks = load_tracks(tracks_file)
    
    if not shows:
        print("Error: No shows data loaded.")
        return
    
    print(f"Loaded {len(shows)} shows")
    print(f"Loaded {len(artists['by_id'])} unique artists")
    print(f"Loaded {sum(len(t) for t in tracks.values())} tracks")
    
    # Combine data
    print("\nCombining data...")
    combined_data = combine_data(shows, artists, tracks)
    
    # Save combined data
    output_dir = 'data/final'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'combined_data_{date_str}.json')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nCombined data saved to: {output_file}")
        print(f"Total shows: {len(combined_data)}")
        
        # Count statistics
        total_artists = sum(len(show['artists']) for show in combined_data)
        artists_with_spotify = sum(
            1 for show in combined_data 
            for artist in show['artists'] 
            if artist.get('spotify_id')
        )
        total_tracks = sum(
            len(artist.get('tracks', [])) 
            for show in combined_data 
            for artist in show['artists']
        )
        
        print(f"Total artists: {total_artists}")
        print(f"Artists with Spotify data: {artists_with_spotify}")
        print(f"Total tracks: {total_tracks}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error writing combined data: {e}")


if __name__ == "__main__":
    main()


# Brooklyn Paramount Preview

An automated pipeline for discovering upcoming concerts at Brooklyn Paramount and creating Spotify playlists from the performing artists' top tracks.

## About

This repository contains a complete workflow for:
1. **Scraping** upcoming show data from Brooklyn Paramount's website via their GraphQL API (including artist names)
2. **Matching** artists to their Spotify profiles and retrieving metadata
3. **Collecting** top tracks from each artist
4. **Combining** all data into a unified JSON structure
5. **Synchronizing** tracks to a curated Spotify playlist called "Brooklyn Paramount"

The pipeline helps music discovery by automatically creating playlists of artists you'll be able to see live at Brooklyn Paramount, making it easy to familiarize yourself with their music before attending shows.

## Scripts

### Core Pipeline Scripts

**Scraping**
- `src/scraping/brooklyn_paramount_scraper.py` - Scrapes Brooklyn Paramount's GraphQL API to fetch upcoming show data including titles, dates, ticket URLs, and artist information

**Spotify Integration**
- `src/spotify_integration/artist_scraper.py` - Searches Spotify for artists and saves their metadata (ID, name, popularity, followers, genres)
- `src/spotify_integration/track_scraper.py` - Fetches top tracks for each artist found on Spotify
- `src/spotify_integration/tracks_to_playlist_sync.py` - Creates/updates a Spotify playlist with all collected tracks

**Data Processing**
- `src/processing/combine_data.py` - Combines show, artist, and track data into a single unified JSON file

### Supporting Files
- `src/spotify_integration/spotify_client.py` - Spotify API client configuration
- `src/scraping/utils.py` - Scraping utilities and helpers

## Data

### Directory Structure
```
data/
├── raw/
│   └── brooklyn_paramount_shows_YY-MM-DD.json  # Raw scraped show data with artists
├── processed/
│   ├── artist_list_YY-MM-DD.json      # Spotify artist metadata
│   └── track_list_YY-MM-DD.json      # Top tracks for all artists
├── final/
│   └── combined_data_YY-MM-DD.json    # Combined show, artist, and track data
└── cache/                              # Cached API responses
```

### Key Data Files

**`data/raw/brooklyn_paramount_shows_YY-MM-DD.json`**
- **Source**: Brooklyn Paramount GraphQL API
- **Contains**: `title`, `date`, `ticket_url`, `artists` (array with `name`, `image_url`, `genre`)
- **Purpose**: Raw show data from venue website with artist information

**`data/processed/artist_list_YY-MM-DD.json`**
- **Source**: Spotify Web API
- **Contains**: Array of artist objects with `show_title`, `search_term`, `id`, `name`, `popularity`, `followers`, `genres`
- **Purpose**: Spotify artist metadata for matched artists
- **Format**: JSON array, automatically uses date from input file

**`data/processed/track_list_YY-MM-DD.json`**
- **Source**: Spotify Web API
- **Contains**: Array of track objects with `artist_id`, `artist_name`, `track_id`, `track_name`, `popularity`, `duration_ms`
- **Purpose**: Top tracks from all artists for playlist creation
- **Format**: JSON array, automatically uses date from input file

**`data/final/combined_data_YY-MM-DD.json`**
- **Source**: Combined from shows, artists, and tracks
- **Contains**: Array of show objects, each containing:
  - Show metadata (`title`, `date`, `ticket_url`)
  - Artists array with original data (`name`, `image_url`, `genre`) and Spotify metadata (`spotify_id`, `popularity`, `followers`, `spotify_genres`)
  - Tracks array nested within each artist
- **Purpose**: Unified data structure for easy access to all show, artist, and track information
- **Format**: JSON array, uses date from input files

## Usage

### Prerequisites

1. **Python Environment**
   ```bash
   pip install -r requirements.txt
   ```

2. **Spotify Developer Account**
   - Create a Spotify app at [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Note your `Client ID` and `Client Secret`
   - Set redirect URI to `http://localhost:3000/callback`

3. **Environment Variables**
   ```bash
   export SPOTIFY_CLIENT_ID="your_client_id_here"
   export SPOTIFY_CLIENT_SECRET="your_client_secret_here"
   ```

### Step-by-Step Runbook

#### 1. Scrape Brooklyn Paramount Shows
```bash
python src/scraping/brooklyn_paramount_scraper.py
```
- **Output**: `data/raw/brooklyn_paramount_shows_YY-MM-DD.json`
- **What it does**: Fetches all upcoming shows from Brooklyn Paramount's API, including artist names, images, and genres
- **Runtime**: ~30 seconds

#### 2. Scrape Spotify Artist Data
```bash
python src/spotify_integration/artist_scraper.py
```
- **Input**: Automatically finds latest `data/raw/brooklyn_paramount_shows_YY-MM-DD.json`
- **Output**: `data/processed/artist_list_YY-MM-DD.json` (uses date from input file)
- **What it does**: 
  - Extracts artist names from scraped shows
  - Searches Spotify for each artist and saves metadata
  - Automatically deduplicates artists (same artist appearing in multiple shows)
- **Runtime**: ~1 minute for 60 artists

#### 3. Collect Artist Top Tracks
```bash
python src/spotify_integration/track_scraper.py
```
- **Input**: Automatically finds latest `data/processed/artist_list_YY-MM-DD.json`
- **Output**: `data/processed/track_list_YY-MM-DD.json` (uses date from input file)
- **What it does**: 
  - Fetches top 10 tracks for each unique artist found on Spotify
  - Only processes distinct artists (no duplicate API calls)
- **Runtime**: ~2 minutes for 60 artists

#### 4. Combine All Data
```bash
python src/processing/combine_data.py
```
- **Input**: Automatically finds latest files from `data/raw/` and `data/processed/`
- **Output**: `data/final/combined_data_YY-MM-DD.json`
- **What it does**: 
  - Combines show, artist, and track data into a unified structure
  - Links artists to their shows and tracks
  - Preserves all metadata from each source
- **Runtime**: <5 seconds

#### 5. Sync to Spotify Playlist
```bash
# Add tracks from all artists (default)
python src/spotify_integration/tracks_to_playlist_sync.py

# Add tracks from first artist only (headliner)
python src/spotify_integration/tracks_to_playlist_sync.py --first-artist-only
```
- **Input**: Automatically finds latest `data/final/combined_data_YY-MM-DD.json`
- **Output**: Spotify playlist "Brooklyn Paramount"
- **What it does**: 
  - Creates playlist if it doesn't exist
  - Clears existing tracks
  - Adds collected tracks (handles 100-track API limit)
  - Automatically deduplicates shows, artists, and tracks
  - Option to include only headliners (`--first-artist-only` flag)
- **Runtime**: ~30 seconds for 500+ tracks

### Authentication Notes

- First run of Spotify scripts will open a browser for OAuth authentication
- Subsequent runs use cached tokens
- Scripts require different scopes:
  - Artist/track lookup: No special scopes
  - Playlist modification: `playlist-modify-public playlist-modify-private user-library-read`

### Troubleshooting

**Common Issues:**
- **"No artist found"**: Artist name from API doesn't match Spotify search (may need manual adjustment)
- **Rate limiting**: Scripts include delays to respect API limits
- **Authentication errors**: Check environment variables and re-authenticate if needed
- **Empty playlist**: Verify track IDs in combined data are valid
- **File not found**: Scripts automatically find the latest dated files, but ensure previous steps have run successfully
- **Combined data not found**: Run `combine_data.py` before syncing to playlist

**Data Validation:**
- Check file counts between pipeline steps (all scripts use date-stamped filenames)
- Verify artist names from scraped data match Spotify results
- Confirm track IDs are valid Spotify URIs
- All data files are now in JSON format for better structure preservation
- Combined data file provides a single source of truth for all show, artist, and track information

**Playlist Options:**
- **Default mode**: Includes tracks from all artists across all shows
- **`--first-artist-only` mode**: Only includes tracks from the first artist (headliner) of each show
- Both modes automatically deduplicate shows, artists, and tracks to avoid duplicates in the playlist

# Brooklyn Paramount Preview

An automated pipeline for discovering upcoming concerts at Brooklyn Paramount and creating Spotify playlists from the performing artists' top tracks.

## About

This repository contains a complete workflow for:
1. **Scraping** upcoming show data from Brooklyn Paramount's website via their GraphQL API
2. **Processing** show titles to extract likely artist names (manual step using ChatGPT)
3. **Matching** artists to their Spotify profiles and retrieving metadata
4. **Collecting** top tracks from each artist
5. **Synchronizing** all tracks to a curated Spotify playlist called "Brooklyn Paramount"

The pipeline helps music discovery by automatically creating playlists of artists you'll be able to see live at Brooklyn Paramount, making it easy to familiarize yourself with their music before attending shows.

## Scripts

### Core Pipeline Scripts

**Scraping**
- `src/scraping/brooklyn_paramount_scraper.py` - Scrapes Brooklyn Paramount's GraphQL API to fetch upcoming show data including titles, dates, and ticket URLs

**Spotify Integration**
- `src/spotify_integration/artist_scraper.py` - Searches Spotify for artists and saves their metadata (ID, name, popularity, followers, genres)
- `src/spotify_integration/track_scraper.py` - Fetches top tracks for each artist found on Spotify
- `src/spotify_integration/tracks_to_playlist_sync.py` - Creates/updates a Spotify playlist with all collected tracks

**Processing Utilities**
- `src/processing/artist_extractor.py` - Utilities for extracting artist names from show titles
- `src/processing/title_processor.py` - Text processing utilities for cleaning show titles

### Supporting Files
- `src/spotify_integration/spotify_client.py` - Spotify API client configuration
- `src/scraping/utils.py` - Scraping utilities and helpers

## Data

### Directory Structure
```
data/
├── brooklyn_paramount_shows.csv         # Raw scraped show data
├── processed/
│   ├── show_title_to_artist.csv        # Manual mapping of show titles to artist names
│   ├── artist_list.csv                 # Spotify artist metadata
│   └── track_list.csv                  # Top tracks for all artists
├── raw/                                 # Raw data backups
├── cache/                              # Cached API responses
└── final/                              # Final processed datasets
```

### Key Data Files

**`data/brooklyn_paramount_shows.csv`**
- **Source**: Brooklyn Paramount GraphQL API
- **Contains**: `title`, `date`, `ticket_url`
- **Purpose**: Raw show data from venue website

**`data/processed/show_title_to_artist.csv`**
- **Source**: Manual creation (ChatGPT assisted)
- **Contains**: `Show Title`, `Artist`
- **Purpose**: Maps complex show titles to likely artist names for Spotify search

**`data/processed/artist_list.csv`**
- **Source**: Spotify Web API
- **Contains**: `show_title`, `search_term`, `id`, `name`, `popularity`, `followers`, `genres`
- **Purpose**: Spotify artist metadata for matched artists

**`data/processed/track_list.csv`**
- **Source**: Spotify Web API
- **Contains**: `artist_id`, `artist_name`, `track_id`, `track_name`, `popularity`, `duration_ms`
- **Purpose**: Top tracks from all artists for playlist creation

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
- **Output**: `data/brooklyn_paramount_shows.csv`
- **What it does**: Fetches all upcoming shows from Brooklyn Paramount's API
- **Runtime**: ~30 seconds

#### 2. Create Artist Mapping (Manual Step)
- **Input**: `data/brooklyn_paramount_shows.csv`
- **Output**: `data/processed/show_title_to_artist.csv`
- **Process**: 
  1. Review show titles in the CSV
  2. Use ChatGPT or manual research to extract likely artist names
  3. Create a CSV with columns: `Show Title`, `Artist`
  4. Handle complex cases like "Artist A + Artist B", tribute bands, etc.

**Example mapping:**
```csv
Show Title,Artist
"Vampire Weekend with Special Guest Courtney Barnett",Vampire Weekend
"The 1975: Being Funny In A Foreign Language Tour",The 1975
"An Evening with David Byrne",David Byrne
```

#### 3. Scrape Spotify Artist Data
```bash
python src/spotify_integration/artist_scraper.py
```
- **Input**: `data/processed/show_title_to_artist.csv`
- **Output**: `data/processed/artist_list.csv`
- **What it does**: Searches Spotify for each artist and saves metadata
- **Runtime**: ~1 minute for 60 artists

#### 4. Collect Artist Top Tracks
```bash
python src/spotify_integration/track_scraper.py
```
- **Input**: `data/processed/artist_list.csv`
- **Output**: `data/processed/track_list.csv`
- **What it does**: Fetches top 10 tracks for each artist found on Spotify
- **Runtime**: ~2 minutes for 60 artists

#### 5. Sync to Spotify Playlist
```bash
python src/spotify_integration/tracks_to_playlist_sync.py
```
- **Input**: `data/processed/track_list.csv`
- **Output**: Spotify playlist "Brooklyn Paramount"
- **What it does**: 
  - Creates playlist if it doesn't exist
  - Clears existing tracks
  - Adds all collected tracks (handles 100-track API limit)
- **Runtime**: ~30 seconds for 500+ tracks

### Authentication Notes

- First run of Spotify scripts will open a browser for OAuth authentication
- Subsequent runs use cached tokens
- Scripts require different scopes:
  - Artist/track lookup: No special scopes
  - Playlist modification: `playlist-modify-public playlist-modify-private user-library-read`

### Troubleshooting

**Common Issues:**
- **"No artist found"**: Artist name in mapping file doesn't match Spotify search
- **Rate limiting**: Scripts include delays to respect API limits
- **Authentication errors**: Check environment variables and re-authenticate if needed
- **Empty playlist**: Verify track IDs in `track_list.csv` are valid

**Data Validation:**
- Check row counts between pipeline steps
- Verify artist names match between mapping and Spotify results
- Confirm track IDs are valid Spotify URIs

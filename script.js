// --- Configuration ---
const CLIENT_ID = "fee1a3b5004a49ba9ae8b27253252942";  // Replace with your Client ID
const REDIRECT_URI = window.location.origin + "/"; // Dynamically get base URL, add trailing slash
const AUTH_ENDPOINT = "/.netlify/functions/auth"; // Path to your Netlify Function

// --- Global Variables ---
let accessToken = null;
let deviceId = null;
let player = null;  // Spotify Player instance
let currentArtistId = null; //track currently playing artist
let currentTopTracks = [];  // Store the list of top tracks
let currentTrackIndex = 0;  // Keep track of which song we're on

// --- Helper Functions ---
function createEl(tag, attributes = {}, text = '') {
    const el = document.createElement(tag);
    for (const key in attributes) {
        el.setAttribute(key, attributes[key]);
    }
    el.textContent = text;
    return el;
}

// --- Load Data (using fetch) ---
async function loadData() {
	try {
		const artistResponse = await fetch('data/processed/artist_list.csv'); // Fetch artist data
		if (!artistResponse.ok) {
			throw new Error(`Artist data fetch failed: ${artistResponse.status}`);
		}
		const artistCsvText = await artistResponse.text();
		const artistData = parseCSV(artistCsvText);

		const trackResponse = await fetch('data/processed/track_list.csv');    // Fetch track data
		if (!trackResponse.ok) {
			throw new Error(`Track data fetch failed: ${trackResponse.status}`);
		}
		const trackCsvText = await trackResponse.text();
		const trackData = parseCSV(trackCsvText);

		return { artists: artistData, tracks: trackData }; // Return both datasets

	} catch (error) {
		console.error("Error loading data:", error);
		document.getElementById('artist-container').textContent = "Error loading data. See console for details.";
		return null; // Or handle the error as appropriate
	}
}
// --- CSV Parsing Function ---
function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    const header = lines.shift().split(',');
    const data = [];

    for (const line of lines) {
        const values = line.split(','); // Simple split (no quoted fields handling)
        const entry = {};
        for (let i = 0; i < header.length; i++) {
             // Handle arrays within CSV (e.g., genres)
            let value = values[i] || ''; // Default to empty string if no value
            if (value.startsWith('[') && value.endsWith(']')) { //check if it looks like an array
                value = value.slice(1,-1).replace(/["']/g, '').split(',').map(item => item.trim()).filter(item => item !== '');
            }
            entry[header[i].trim()] = value; //trim the field names
        }
        data.push(entry);
    }
    return data;
}

// --- Spotify Web Playback SDK Initialization ---
window.onSpotifyWebPlaybackSDKReady = () => {
    console.log("Spotify Web Playback SDK ready!");
    // Player initialization will happen after we get the access token
};

// --- Authentication ---
async function authenticateWithSpotify() {
    const scopes = [
        "streaming",
        "user-read-email",
        "user-read-private",
        "user-modify-playback-state", // Required to control playback
        "user-read-playback-state",  // Required to get playback state
    ];
    const authUrl = `https://accounts.spotify.com/authorize?client_id=${CLIENT_ID}&response_type=code&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&scope=${encodeURIComponent(scopes.join(' '))}`;
    window.location.href = authUrl; // Redirect to Spotify for authorization
}

async function handleAuthCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
        try {
            const response = await fetch(`${AUTH_ENDPOINT}?code=${code}`);
            const data = await response.json();

            if (data.access_token) {
                accessToken = data.access_token;
                initializePlayer(); // Initialize player *after* getting token
                document.getElementById('auth-button').style.display = 'none'; //hide auth button
                displayArtistsAndTracks(); //load the artist data
            } else {
                console.error("Error getting access token:", data);
            }
        } catch (error) {
            console.error("Error during token exchange:", error);
        }
    }
}

// --- Initialize Spotify Player ---
function initializePlayer() {
    player = new Spotify.Player({
        name: 'Brooklyn Paramount Web Player',
        getOAuthToken: cb => { cb(accessToken); },
        volume: 0.5
    });

    // --- Event Handlers ---
    player.addListener('ready', ({ device_id }) => {
        console.log('Ready with Device ID', device_id);
        deviceId = device_id;
    });

    player.addListener('not_ready', ({ device_id }) => {
        console.log('Device ID has gone offline', device_id);
    });

    player.addListener('initialization_error', ({ message }) => {
        console.error("Initialization Error:", message);
    });
    player.addListener('authentication_error', ({ message }) => {
        console.error("Authentication Error:", message);
    });
    player.addListener('account_error', ({ message }) => {
        console.error("Account Error:", message);
        alert("A Spotify Premium account is required to use the Web Playback SDK.");
    });
    player.addListener('playback_error', ({ message }) => {
        console.error("Playback Error:", message);
    });

    // --- Playback Status Updates ---
    player.addListener('player_state_changed', state => {
        if (!state) {
            return;
        }
        //Update now playing display
        document.getElementById('now-playing').textContent = `Now Playing: ${state.track_window.current_track.name} - ${state.track_window.current_track.artists[0].name}`;
        //check if new artist started
        const newArtistId = state.track_window.current_track.artists[0].uri.split(":")[2]; //get artist ID

        if (currentArtistId !== newArtistId) {
            currentArtistId = newArtistId;

            // Find and expand the corresponding artist entry
            const artistEntries = document.querySelectorAll('.artist-entry');
            artistEntries.forEach(entry => {
                if (entry.dataset.artistId === currentArtistId) {
                    const trackList = entry.querySelector('.track-list');
                    if(trackList){ //make sure there is a tracklist before toggling it.
                        trackList.style.display = 'block'; // Show the track list
                    }
                    entry.scrollIntoView({behavior: "smooth", block: "start"});//smooth scroll
                } else {
                    //hide the non active tracklists.
                    const trackList = entry.querySelector('.track-list');
                    if(trackList){
                        trackList.style.display = 'none'
                    }
                }
            });
        }

        // You can add more state handling here (e.g., update UI)
    });


    // --- Connect to the Player ---
    player.connect().then(success => {
        if (success) {
            console.log('The Web Playback SDK successfully connected to Spotify!');
        }
    });
}



// --- Play a Track ---
async function playTrack(trackUri) {
    if (!accessToken || !deviceId) {
        console.error("Not authenticated or no device ID.");
        return;
    }

    try {
        const response = await fetch(`https://api.spotify.com/v1/me/player/play?device_id=${deviceId}`, {
            method: 'PUT',
            body: JSON.stringify({ uris: [trackUri] }),
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Failed to play track: ${response.status} - ${JSON.stringify(errorData)}`);
        }
        console.log("Playback started!");

    } catch (error) {
        console.error("Error starting playback:", error);
    }
}

// Add these functions after the playTrack function
async function skipForward() {
    if (!accessToken || !deviceId) {
        console.error("Not authenticated or no device ID.");
        return;
    }

    try {
        // First get current playback state
        const stateResponse = await fetch('https://api.spotify.com/v1/me/player', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (!stateResponse.ok) {
            throw new Error(`Failed to get playback state: ${stateResponse.status}`);
        }
        
        const state = await stateResponse.json();
        const newPosition = state.progress_ms + 20000; // Add 20 seconds (20000ms)
        
        // Seek to new position
        const response = await fetch(`https://api.spotify.com/v1/me/player/seek?position_ms=${newPosition}&device_id=${deviceId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to skip forward: ${response.status}`);
        }
    } catch (error) {
        console.error("Error skipping forward:", error);
    }
}

async function nextTrack() {
    if (!accessToken || !deviceId || currentTopTracks.length === 0) {
        console.error("Not authenticated, no device ID, or no tracks loaded.");
        return;
    }

    try {
        // Increment index and wrap around if we reach the end
        currentTrackIndex = (currentTrackIndex + 1) % currentTopTracks.length;
        // Play the next track
        await playTrack(currentTopTracks[currentTrackIndex].uri);
    } catch (error) {
        console.error("Error playing next track:", error);
    }
}

// --- Display Artists and Tracks (Modified) ---
async function displayArtistsAndTracks() {
    const data = await loadData();
    if (!data) return;

    const artistContainer = document.getElementById('artist-container');
    
    // Add playback controls container
    const controlsContainer = createEl('div', { class: 'playback-controls' });
    const skipForwardButton = createEl('button', { class: 'control-button' }, 'Skip 20s');
    const nextTrackButton = createEl('button', { class: 'control-button' }, 'Next Song');
    
    skipForwardButton.addEventListener('click', skipForward);
    nextTrackButton.addEventListener('click', nextTrack);
    
    controlsContainer.appendChild(skipForwardButton);
    controlsContainer.appendChild(nextTrackButton);
    artistContainer.appendChild(controlsContainer);

    const artistMap = {};
    for (const artist of data.artists) {
        artistMap[artist.id] = artist;
    }

    const shows = {};
    for (const track of data.tracks) {
        const artist = artistMap[track.artist_id];
        if (!artist) {
            console.warn(`Artist not found for track: ${track.track_id}`);
            continue;
        }
        const showTitle = artist.show_title;
        if (!shows[showTitle]) {
            shows[showTitle] = {
                artistName: artist.search_term,
                artistId: artist.id, // Store artist ID
                tracks: []
            };
        }
        shows[showTitle].tracks.push(track);
    }

    for (const showTitle in shows) {
        const show = shows[showTitle];
        const artistEntry = createEl('div', { class: 'artist-entry', 'data-artist-id': show.artistId }); // Store artist ID as data attribute
        const showTitleEl = createEl('div', { class: 'show-title' }, showTitle);
        artistEntry.appendChild(showTitleEl);
        const artistNameEl = createEl('div', { class: 'artist-name' }, show.artistName);
        artistEntry.appendChild(artistNameEl);
        const trackList = createEl('div', { class: 'track-list' });
        artistEntry.appendChild(trackList);


        //add tracks
        for (const track of show.tracks) {
            const trackEntry = createEl('div', { class: 'track-entry' }, `${track.track_name}`);
            trackList.appendChild(trackEntry);
        }

        artistEntry.addEventListener('click', async function(event) {
            // Toggle track list visibility
            const isExpanded = trackList.style.display === 'block';
            trackList.style.display = isExpanded ? 'none' : 'block';

            // --- Playback Logic ---
            if (!isExpanded) { // Only play if we're expanding, not collapsing
                try {
                    const response = await fetch(`https://api.spotify.com/v1/artists/${show.artistId}/top-tracks?market=US`, {
                        headers: {
                            'Authorization': `Bearer ${accessToken}`
                        }
                    });

                    if (!response.ok) {
                        throw new Error(`Failed to fetch top tracks: ${response.status}`);
                    }

                    const topTracksData = await response.json();
                    if (topTracksData.tracks && topTracksData.tracks.length > 0) {
                        // Store the full list of tracks and reset index
                        currentTopTracks = topTracksData.tracks;
                        currentTrackIndex = 0;
                        // Play the first track
                        await playTrack(currentTopTracks[currentTrackIndex].uri);
                    } else {
                        console.log("No top tracks found for this artist.");
                    }
                } catch (error) {
                    console.error("Error fetching top tracks:", error);
                }
            }
            event.stopPropagation();
        });

        artistContainer.appendChild(artistEntry);
    }
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('auth-button').addEventListener('click', authenticateWithSpotify);
    handleAuthCallback();  // Check for auth code on page load
});
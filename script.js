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


// --- Display Artists and Tracks ---
async function displayArtistsAndTracks() {
    const data = await loadData();
    if (!data) return; // Exit if loading failed

    const artistContainer = document.getElementById('artist-container');
    const artistMap = {}; // Store artist data by artist ID


    //create a lookup map for artists by id
    for (const artist of data.artists) {
        artistMap[artist.id] = artist;
    }

    // Group tracks by show title
    const shows = {};
    for (const track of data.tracks) {
        const artist = artistMap[track.artist_id];
        if (!artist) {
            console.warn(`Artist not found for track: ${track.track_id}`);
            continue
        }
        const showTitle = artist.show_title;
        if (!shows[showTitle]) {
            shows[showTitle] = {
                artistName: artist.search_term, //Use the search term from the artists csv
                tracks: []
            };
        }
        shows[showTitle].tracks.push(track);
    }

    //display the data.
    for(const showTitle in shows){
        const show = shows[showTitle]
        const artistEntry = createEl('div', { class: 'artist-entry' });
        const showTitleEl = createEl('div', { class: 'show-title'}, showTitle)
        artistEntry.appendChild(showTitleEl)
        const artistNameEl = createEl('div', { class: 'artist-name'}, show.artistName); //show artist name
        artistEntry.appendChild(artistNameEl);
        const trackList = createEl('div', { class: 'track-list' });
        artistEntry.appendChild(trackList);

        for (const track of show.tracks) {
            const trackEntry = createEl('div', { class: 'track-entry' }, `${track.track_name}`);
            trackList.appendChild(trackEntry);
        }
        artistEntry.addEventListener('click', function(event) {
            //toggle display of tracks
            const isExpanded = trackList.style.display === 'block';
            trackList.style.display = isExpanded ? 'none' : 'block';

            // Prevent event bubbling to parent elements
            event.stopPropagation();

        });
        artistContainer.appendChild(artistEntry);
    }
}
// --- Initialize ---
displayArtistsAndTracks();
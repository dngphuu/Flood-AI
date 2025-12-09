// Configuration
const BACKEND_URL = 'http://localhost:5000';

// State
const state = {
    startPoint: null, // {lat, lng}
    endPoint: null,   // {lat, lng}
    cameras: [],      // Array of camera objects
    cameraLayer: null, // Leaflet LayerGroup
    floodLayer: null,  // Leaflet LayerGroup
    routeLayer: null,  // Leaflet Polyline
    startMarker: null,
    endMarker: null
};

// Global coordinate storage for autocomplete
let startCoords = null; // [lat, lon]
let endCoords = null;   // [lat, lon]

// ============================================================================
// Utility Functions
// ============================================================================

// Debounce function to limit API calls
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// Map Initialization (Center on HCMC)
const map = L.map('map').setView([10.7769, 106.7009], 13); // Central HCMC

// Base Tile Layer (CartoDB Positron for clean look)
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19
}).addTo(map);

// Layers
state.cameraLayer = L.layerGroup(); // Not added by default based on prompt req? "Check to show"
state.floodLayer = L.layerGroup().addTo(map); // Added by default

// Icons
const startIcon = L.divIcon({
    className: 'location-icon-start',
    html: '<i class="fa-solid fa-location-dot"></i>',
    iconSize: [30, 30],
    iconAnchor: [15, 30]
});

const endIcon = L.divIcon({
    className: 'location-icon-end',
    html: '<i class="fa-solid fa-location-dot"></i>',
    iconSize: [30, 30],
    iconAnchor: [15, 30]
});

// ============================================================================
// Data Fetching
// ============================================================================

async function fetchFloodStatus() {
    try {
        const response = await fetch(`${BACKEND_URL}/flood-status`);
        const data = await response.json();
        
        state.cameras = data.cameras;
        updateMapMarkers();
        updateStatus(`Loaded ${data.total_cameras} cameras. ${data.flooded_count} flooded.`);
    } catch (error) {
        console.error('Error fetching flood status:', error);
        updateStatus('Error loading flood data', 'danger');
    }
}

async function findRoute() {
    if (!state.startPoint || !state.endPoint) {
        alert("Please select both start and end points.");
        return;
    }

    showLoading(true);
    
    try {
        const payload = {
            start_coords: state.startPoint,
            end_coords: state.endPoint,
            camera_ids: [] // Deprecated but required by schema if not optional? Schema says default=[]
        };

        const response = await fetch(`${BACKEND_URL}/route_request`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Route calculation failed');

        const result = await response.json();
        const routeData = result.data;

        // Draw Route
        if (state.routeLayer) map.removeLayer(state.routeLayer);
        
        // Backend returns path as array of {lat, lng} objects
        // Convert to Leaflet format: [[lat, lng], [lat, lng], ...]
        const pathCoords = routeData.path.map(coord => [coord.lat, coord.lng]);
        
        state.routeLayer = L.polyline(pathCoords, {
            color: '#00b14f',
            weight: 6,
            opacity: 0.8,
            lineCap: 'round'
        }).addTo(map);

        map.fitBounds(state.routeLayer.getBounds(), { padding: [50, 50] });
        updateStatus(`Route found! Length: ${routeData.path_length} nodes. Avoided ${routeData.flooded_count} floods.`);

    } catch (error) {
        console.error('Error finding route:', error);
        alert('Could not calculate safe route. Please try different points.');
    } finally {
        showLoading(false);
    }
}

// ============================================================================
// Map Updates
// ============================================================================

function updateMapMarkers() {
    state.cameraLayer.clearLayers();
    state.floodLayer.clearLayers();

    state.cameras.forEach(cam => {
        // Validate camera data
        if (!cam || !cam.coords || !cam.coords.lat || !cam.coords.lng) {
            console.warn('Skipping camera with invalid coordinates:', cam);
            return;
        }
        
        const isFlooded = cam.is_flooded;
        
        // Extract coordinates from the API response structure
        const lat = cam.coords.lat;
        const lng = cam.coords.lng;
        
        // 1. Camera Marker (for Camera Layer)
        // Icon based on status
        const iconHtml = isFlooded 
            ? '<i class="fa-solid fa-video"></i>' 
            : '<i class="fa-solid fa-video"></i>';
            
        const markerClass = isFlooded ? 'camera-icon-flood' : 'camera-icon-normal';

        const marker = L.marker([lat, lng], {
            icon: L.divIcon({
                className: markerClass,
                html: iconHtml,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        }).bindPopup(`<b>${cam.name || cam.camera_id}</b><br>Status: ${isFlooded ? "FLOODED" : "Dry"}`);
        
        state.cameraLayer.addLayer(marker);

        // 2. Flood Visualization (Red Blend) - Only if flooded
        if (isFlooded) {
            const circle = L.circle([lat, lng], {
                color: 'red',
                fillColor: '#f03',
                fillOpacity: 0.3,
                radius: 100, // 100 meters radius
                stroke: false
            });
            state.floodLayer.addLayer(circle);

            // Add a pulsing effect marker in center
            // const pulse = L.marker([lat, lng], {
            //     icon: L.divIcon({
            //         className: 'flood-pulse-icon',
            //         iconSize: [20, 20],
            //         iconAnchor: [10, 10]
            //     })
            // });
            // state.floodLayer.addLayer(pulse);
        }
    });
}

// ============================================================================
// Autocomplete Functionality
// ============================================================================

async function searchLocation(inputElement, suggestionsListId) {
    const query = inputElement.value.trim();
    const suggestionsList = document.getElementById(suggestionsListId);
    
    // Clear suggestions if query is empty
    if (!query || query.length < 3) {
        suggestionsList.innerHTML = '';
        suggestionsList.classList.remove('show');
        return;
    }
    
    try {
        // Call Nominatim API with Vietnam filter
        const url = `https://nominatim.openstreetmap.org/search?` +
            `format=json` +
            `&q=${encodeURIComponent(query)}` +
            `&countrycodes=vn` +
            `&limit=5` +
            `&addressdetails=1`;
        
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'FloodAI-Map-App' // Nominatim requires user agent
            }
        });
        
        const results = await response.json();
        
        // Display suggestions
        if (results && results.length > 0) {
            suggestionsList.innerHTML = results.map(result => `
                <li class="autocomplete-item" 
                    data-lat="${result.lat}" 
                    data-lon="${result.lon}"
                    data-display="${result.display_name}">
                    <span class="autocomplete-item-name">${result.display_name.split(',')[0]}</span>
                    <span class="autocomplete-item-address">${result.display_name}</span>
                </li>
            `).join('');
            suggestionsList.classList.add('show');
        } else {
            suggestionsList.innerHTML = '<li class="autocomplete-item"><span class="autocomplete-item-name">Không tìm thấy kết quả</span></li>';
            suggestionsList.classList.add('show');
        }
    } catch (error) {
        console.error('Autocomplete error:', error);
        suggestionsList.innerHTML = '<li class="autocomplete-item"><span class="autocomplete-item-name">Lỗi tìm kiếm</span></li>';
        suggestionsList.classList.add('show');
    }
}

function selectSuggestion(lat, lon, displayName, type) {
    // Convert to numbers
    const latitude = parseFloat(lat);
    const longitude = parseFloat(lon);
    
    // Store coordinates in global variables
    if (type === 'start') {
        startCoords = [latitude, longitude];
        document.getElementById('start-input').value = displayName;
        document.getElementById('start-suggestions').classList.remove('show');
        
        // Update state and map marker
        setPoint({ lat: latitude, lng: longitude }, 'start');
    } else if (type === 'end') {
        endCoords = [latitude, longitude];
        document.getElementById('end-input').value = displayName;
        document.getElementById('end-suggestions').classList.remove('show');
        
        // Update state and map marker
        setPoint({ lat: latitude, lng: longitude }, 'end');
    }
}

function hideSuggestions(suggestionsListId) {
    setTimeout(() => {
        document.getElementById(suggestionsListId).classList.remove('show');
    }, 200);
}

function initAutocomplete() {
    const startInput = document.getElementById('start-input');
    const endInput = document.getElementById('end-input');
    const startSuggestions = document.getElementById('start-suggestions');
    const endSuggestions = document.getElementById('end-suggestions');
    
    // Debounced search functions (500ms delay)
    const debouncedStartSearch = debounce(() => searchLocation(startInput, 'start-suggestions'), 500);
    const debouncedEndSearch = debounce(() => searchLocation(endInput, 'end-suggestions'), 500);
    
    // Input event listeners
    startInput.addEventListener('input', debouncedStartSearch);
    endInput.addEventListener('input', debouncedEndSearch);
    
    // Click handlers for suggestions
    startSuggestions.addEventListener('click', (e) => {
        const item = e.target.closest('.autocomplete-item');
        if (item && item.dataset.lat) {
            selectSuggestion(item.dataset.lat, item.dataset.lon, item.dataset.display, 'start');
        }
    });
    
    endSuggestions.addEventListener('click', (e) => {
        const item = e.target.closest('.autocomplete-item');
        if (item && item.dataset.lat) {
            selectSuggestion(item.dataset.lat, item.dataset.lon, item.dataset.display, 'end');
        }
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.autocomplete-container')) {
            startSuggestions.classList.remove('show');
            endSuggestions.classList.remove('show');
        }
    });
    
    // Hide suggestions on blur
    startInput.addEventListener('blur', () => hideSuggestions('start-suggestions'));
    endInput.addEventListener('blur', () => hideSuggestions('end-suggestions'));
}

// ============================================================================
// UI Interactions
// ============================================================================

// Geocoding Helper (Nominatim)
async function geocode(query) {
    if (!query) return null;
    // Check if query is "lat,lng"
    const coordMatch = query.match(/^(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)$/);
    if (coordMatch) {
        return { lat: parseFloat(coordMatch[1]), lng: parseFloat(coordMatch[3]) };
    }

    // Call Nominatim
    try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query + ', Ho Chi Minh City')}&limit=1`;
        const res = await fetch(url);
        const json = await res.json();
        if (json && json.length > 0) {
            return { lat: parseFloat(json[0].lat), lng: parseFloat(json[0].lon) };
        }
        return null;
    } catch (e) {
        console.error("Geocode error", e);
        return null;
    }
}

async function handleSearch(inputId, type) {
    const input = document.getElementById(inputId);
    const query = input.value;
    const coords = await geocode(query);

    if (coords) {
        setPoint(coords, type);
    } else {
        alert("Location not found. Try entering 'Lat,Lng' directly.");
    }
}

function setPoint(coords, type) {
    if (type === 'start') {
        state.startPoint = coords;
        document.getElementById('start-input').value = `${coords.lat.toFixed(4)}, ${coords.lng.toFixed(4)}`;
        if (state.startMarker) map.removeLayer(state.startMarker);
        state.startMarker = L.marker([coords.lat, coords.lng], { icon: startIcon, draggable: true }).addTo(map);
        state.startMarker.on('dragend', (e) => setPoint(e.target.getLatLng(), 'start'));
        map.panTo([coords.lat, coords.lng]);
    } else {
        state.endPoint = coords;
        document.getElementById('end-input').value = `${coords.lat.toFixed(4)}, ${coords.lng.toFixed(4)}`;
        if (state.endMarker) map.removeLayer(state.endMarker);
        state.endMarker = L.marker([coords.lat, coords.lng], { icon: endIcon, draggable: true }).addTo(map);
        state.endMarker.on('dragend', (e) => setPoint(e.target.getLatLng(), 'end'));
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    
    // Initialize autocomplete
    initAutocomplete();
    
    // Initial Load
    fetchFloodStatus();
    
    // Refresh flood status every 30s
    setInterval(fetchFloodStatus, 30000);

    // Toggles
    const toggleCam = document.getElementById('toggle-cameras');
    toggleCam.addEventListener('change', (e) => {
        if (e.target.checked) {
            map.addLayer(state.cameraLayer);
        } else {
            map.removeLayer(state.cameraLayer);
        }
    });

    const toggleFlood = document.getElementById('toggle-flood');
    toggleFlood.addEventListener('change', (e) => {
        if (e.target.checked) {
            map.addLayer(state.floodLayer);
        } else {
            map.removeLayer(state.floodLayer);
        }
    });

    // Test Mode
    const toggleTest = document.getElementById('toggle-test-mode');
    toggleTest.addEventListener('change', async (e) => {
        const endpoint = e.target.checked ? `${BACKEND_URL}/test-flood/enable` : `${BACKEND_URL}/test-flood/disable`;
        await fetch(endpoint, { method: 'POST' });
        await fetchFloodStatus();
    });

    // Note: Input change handlers removed - now using autocomplete

    // Buttons
    document.getElementById('btn-find-route').addEventListener('click', findRoute);
    
    document.getElementById('btn-use-current').addEventListener('click', () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(pos => {
                setPoint({ lat: pos.coords.latitude, lng: pos.coords.longitude }, 'start');
            });
        } else {
            alert("Geolocation not supported");
        }
    });

    // Map Click Context
    // map.on('click', (e) => {
    //     // Simple logic: If start is empty, set start. If start exists, set end.
    //     if (!state.startPoint) {
    //         setPoint(e.latlng, 'start');
    //     } else if (!state.endPoint) {
    //         setPoint(e.latlng, 'end');
    //     }
    // });
    
    // Better: Right click menu or just let user type. 
    // Let's implement Right Click to set points for better UX
    map.on('contextmenu', (e) => {
        const popup = L.popup()
            .setLatLng(e.latlng)
            .setContent(`
                <button class="btn btn-sm btn-success mb-1" onclick="window.setStartPoint(${e.latlng.lat}, ${e.latlng.lng});">Set Start</button><br>
                <button class="btn btn-sm btn-danger" onclick="window.setEndPoint(${e.latlng.lat}, ${e.latlng.lng});">Set End</button>
            `)
            .openOn(map);
    });

    // Expose helpers for popup
    window.setStartPoint = (lat, lng) => {
        setPoint({lat, lng}, 'start');
        map.closePopup();
    };
    window.setEndPoint = (lat, lng) => {
        setPoint({lat, lng}, 'end');
        map.closePopup();
    };
    
    // Expose map globally for debugging if needed
    window.mapInstance = map;
});

// Utilities
function showLoading(show) {
    const el = document.getElementById('loading-overlay');
    if (show) el.classList.remove('d-none');
    else el.classList.add('d-none');
}

function updateStatus(msg, type='info') {
    const panel = document.getElementById('status-panel');
    const text = document.getElementById('status-text');
    panel.className = `alert alert-${type} mb-3`;
    panel.classList.remove('d-none');
    text.textContent = msg;
    
    // Auto hide after 5s
    setTimeout(() => {
        // panel.classList.add('d-none'); 
        // Don't auto hide status, good to see state
    }, 5000);
}

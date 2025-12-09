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
        const response = await fetch('/flood-status');
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

        const response = await fetch('/route_request', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Route calculation failed');

        const result = await response.json();
        const routeData = result.data;

        // Draw Route
        if (state.routeLayer) map.removeLayer(state.routeLayer);
        
        // Path is array of [lat, lng] or objects? check backend
        // Backend returns: "path": path_coords (list of tuples/lists)
        state.routeLayer = L.polyline(routeData.path, {
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
        const endpoint = e.target.checked ? '/test-flood/enable' : '/test-flood/disable';
        await fetch(endpoint, { method: 'POST' });
        await fetchFloodStatus();
    });

    // Inputs (Blur to search)
    document.getElementById('start-input').addEventListener('change', () => handleSearch('start-input', 'start'));
    document.getElementById('end-input').addEventListener('change', () => handleSearch('end-input', 'end'));

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

# Flood-AI Frontend

Modern, interactive web interface for the Flood-AI system. Provides real-time flood detection visualization, intelligent route planning, and traffic camera integration for Ho Chi Minh City.

## 🎨 Features

### 🗺️ Interactive Map

- **Leaflet.js** integration with OpenStreetMap tiles
- **Dark theme** optimized for clarity and modern aesthetics
- **Real-time visualization** of routes, cameras, and flood zones
- **Responsive design** adapts to different screen sizes

### 🔍 Location Search

- **Autocomplete search** powered by Nominatim API
- **Smart suggestions** as you type
- **Coordinates display** for selected locations
- **Quick location selection** with click or keyboard

### 📹 Camera Management

- **696 traffic cameras** across Ho Chi Minh City
- **Camera markers** on map with popup information
- **Select multiple cameras** for flood detection
- **Real-time status** indicators

### 🛣️ Smart Routing

- **Route calculation** avoiding detected flood zones
- **Color-coded visualization**:
  - 🟢 **Green route**: Safe path avoiding floods
  - 🔴 **Pink circles**: Detected flood zones (150m radius)
- **Route statistics**: Distance, estimated time, floods avoided
- **Alternative routes** if flooding blocks primary path

### 🌊 Flood Detection

- **Real-time AI analysis** of camera images
- **Visual flood indicators** on map
- **Confidence levels** displayed for each detection
- **Status updates** during processing

## 🚀 Tech Stack

- **HTML5**: Semantic markup
- **CSS3**: Modern styling with:
  - CSS Grid & Flexbox layouts
  - CSS Custom Properties (variables)
  - Dark theme with glassmorphism effects
  - Smooth animations and transitions
- **JavaScript (ES6+)**:
  - Fetch API for backend communication
  - Async/await for asynchronous operations
  - Modular code organization
- **Leaflet.js 1.9+**: Interactive maps
- **Nominatim API**: Location search and geocoding

## 📁 Project Structure

```
frontend/
├── index.html          # Main HTML structure
├── styles.css          # All styling (25KB)
└── app.js              # Frontend logic (23KB)
```

## 🛠 Setup & Running

### Prerequisites

The frontend is automatically served by the backend service. You need:

1. **Backend service** running on port 5000
2. **AI service** running on port 8000 (optional but recommended)

See the [root README](../README.md) for complete setup instructions.

### Access the Application

1. **Start the backend service**:

   ```bash
   # From project root
   uv run backend-service
   ```

2. **Open in browser**:
   ```
   http://localhost:5000/
   ```

The frontend files are served statically from the `frontend/` directory.

## 🎯 How to Use

### 1. Search for Locations

**Starting Point**:

1. Click the "📍 Starting Point" search box
2. Type a location name (e.g., "Bến Thành Market")
3. Select from dropdown suggestions
4. Coordinates are automatically filled

**Destination**:

1. Click the "🎯 Destination" search box
2. Type destination location
3. Select from suggestions
4. Coordinates are populated

### 2. Select Cameras

**Browse Cameras**:

- Pink camera markers appear on the map
- Click any marker to see camera details
- Camera list shows all 696 cameras

**Select for Flood Detection**:

- Click "Select All Cameras" to check all
- Or manually check individual cameras from the list
- Selected cameras will be analyzed for flooding

### 3. Find Safe Route

1. **Click "Find Safe Route"** button
2. **Processing**:
   - Fetches images from selected cameras
   - AI service analyzes each image
   - Detects flooded locations
   - Calculates optimal route avoiding floods
3. **Results**:
   - Route displayed on map (green line)
   - Flood zones shown (pink circles)
   - Statistics displayed in status area

### 4. Reset and Try Again

- Click **"Reset Map"** to clear route and start over
- Search for new locations
- Select different cameras
- Calculate new route

## 🎨 UI Design

### Color Palette

- **Background**: `#0a0e27` (Deep navy)
- **Primary accent**: `#00d4ff` (Cyan)
- **Success**: `#00ff88` (Green)
- **Warning**: `#ffd700` (Gold)
- **Danger**: `#ff6b6b` (Coral red)
- **Text**: `#e0e6ed` (Light gray)

### Design Features

- **Glassmorphism**: Semi-transparent panels with backdrop blur
- **Smooth animations**: 0.3s transitions for interactions
- **Hover effects**: Visual feedback on interactive elements
- **Dark theme**: Reduced eye strain for extended use
- **Responsive typography**: Scales with viewport

## 🔌 API Integration

The frontend communicates with the backend service via REST API:

### Endpoints Used

**1. Route Request**

```javascript
POST http://localhost:5000/route_request
Content-Type: application/json

{
  "start_coords": {"lat": 10.762622, "lng": 106.660172},
  "end_coords": {"lat": 10.773163, "lng": 106.654367},
  "camera_ids": ["camera_id_1", "camera_id_2"]
}
```

**Response**:

```json
{
  "status": "success",
  "data": {
    "path": [{lat, lng}, ...],
    "flooded_coords": [{lat, lng}, ...],
    "flooded_count": 2,
    "camera_count": 10
  }
}
```

**2. Camera Data**

Cameras are loaded via static data embedded in the HTML or fetched from backend.

### Error Handling

- **Network errors**: User-friendly error messages
- **No route found**: Suggests alternative approaches
- **AI service unavailable**: Graceful degradation
- **Invalid input**: Validation with helpful messages

## 📊 Key Components

### Map Initialization

```javascript
// Leaflet map with OpenStreetMap tiles
const map = L.map("map").setView([10.8231, 106.6297], 11);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
```

### Location Search

```javascript
// Debounced Nominatim API search
async function searchLocation(query) {
  const response = await fetch(
    `https://nominatim.openstreetmap.org/search?format=json&q=${query}`
  );
  return response.json();
}
```

### Route Visualization

```javascript
// Draw route on map
const routeLine = L.polyline(pathCoords, {
  color: "#00ff88",
  weight: 4,
  opacity: 0.8,
}).addTo(map);

// Show flood zones
floodedCoords.forEach((coord) => {
  L.circle([coord.lat, coord.lng], {
    radius: 150,
    color: "#ff6b6b",
    fillOpacity: 0.3,
  }).addTo(map);
});
```

## 🐛 Troubleshooting

### Map doesn't load

- Check internet connection (OpenStreetMap tiles)
- Open browser console (F12) for errors
- Verify backend service is running

### Search doesn't work

- Check Nominatim API availability
- Verify network requests in browser DevTools
- Try different search terms

### Routes don't display

- Ensure backend service is running on port 5000
- Check backend logs for errors
- Verify coordinates are valid (within HCMC area)

### Camera markers missing

- Backend service must be running
- Check browser console for JavaScript errors
- Verify `app.js` loaded correctly

## 🚀 Future Enhancements

- [ ] **Real-time updates**: WebSocket integration for live flood status
- [ ] **Historical data**: View past flood events
- [ ] **Route comparison**: Show multiple route options
- [ ] **Mobile app**: Native mobile version
- [ ] **Offline mode**: Service worker for offline functionality
- [ ] **User accounts**: Save favorite routes and locations
- [ ] **Traffic integration**: Real-time traffic conditions
- [ ] **Weather overlay**: Weather data visualization

## 🤝 Contributing

To contribute to the frontend:

1. **Test locally**: Make changes and test in browser
2. **Follow conventions**:
   - Use existing color variables
   - Maintain code organization
   - Comment complex logic
3. **Browser compatibility**: Test in Chrome, Firefox, Safari, Edge
4. **Responsive design**: Test on mobile, tablet, desktop

## 📄 License

Part of the Flood-AI project. See [root README](../README.md) for license information.

---

**Built for safer navigation during floods in Ho Chi Minh City 🌊**

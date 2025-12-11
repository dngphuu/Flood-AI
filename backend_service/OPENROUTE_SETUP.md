# OpenRouteService Migration - Setup Guide

## ✅ What Changed

Migrated from **GraphHopper** to **OpenRouteService** because:

- ❌ GraphHopper free tier does NOT support `block_area`
- ✅ OpenRouteService free tier DOES support `avoid_polygons`

## 🔑 Get Your API Key

1. **Sign up**: https://openrouteservice.org/dev/#/signup
2. **Free tier**: 2000 requests/day (plenty for testing)
3. **Get key**: Dashboard → API Keys → Copy your key

## ⚙️ Configuration

### 1. Update `.env` File

Add your OpenRouteService API key to `backend_service/.env`:

```bash
OPENROUTE_API_KEY=your_api_key_here
```

**Example `.env`** (see `.env.example` for full template):

```bash
# OpenRouteService API Configuration
OPENROUTE_API_KEY=5b3ce3597851110001cf6248abcd1234567890ab

# Other settings...
FLOOD_BLOCK_RADIUS_METERS=150
```

### 2. Restart Backend

```bash
cd backend_service
python -m backend_service.main
```

## 🧪 Testing

### 1. Check Logs for API Key Validation

You should see:

```
INFO: Starting backend service
INFO: OpenRouteService API configured
```

If API key is missing:

```
ERROR: OpenRouteService API key is not configured
ERROR: Sign up at https://openrouteservice.org/dev/#/signup
```

### 2. Test Flood Avoidance

1. **Enable test mode** in frontend (marks random cameras as flooded)
2. **Request a route** that passes through flooded areas
3. **Check logs** for:
   ```
   INFO: Creating avoid polygons for 15 flooded areas with 150m radius
   DEBUG: Avoiding 15 flood polygons
   INFO: ✓ Route calculated successfully
   INFO: Successfully avoided 15 flood areas
   ```

### 3. Visual Verification

- Route should **NOT pass through pink circles** (flooded areas)
- Route should be **green** (safe)
- Status message: `"Avoided X floods (150m radius)"`

## 📋 Key Features

### Avoid Polygons

- Converts each flooded camera location to a circular polygon
- Default radius: **150m** (configurable via `FLOOD_BLOCK_RADIUS_METERS`)
- Sends to OpenRouteService as GeoJSON MultiPolygon

### Smart Routing

- Uses `avoid_polygons` parameter in API request
- OpenRouteService calculates route avoiding ALL flooded areas
- Falls back gracefully if no route possible

### Enhanced Logging

```
INFO: Creating avoid polygons for 8 flooded areas with 150m radius
DEBUG: Avoiding 8 flood polygons (total area: ~18.0 km²)
INFO: Requesting route from [10.7769, 106.7009] to [10.8000, 106.7200]
INFO: ✓ Route calculated successfully with 156 waypoints
INFO:   Distance: 4532.50m (4.53km), Duration: 612s (10.2min)
INFO:   Successfully avoided 8 flood areas (radius: 150m each)
```

## 🔧 Troubleshooting

### Error: "API key is not configured"

**Solution**: Add `OPENROUTE_API_KEY=...` to `.env` file

### Error: "API key unauthorized" (401)

**Solution**: Check your API key is correct, regenerate if needed

### Error: "Rate limit exceeded" (429)

**Solution**: Free tier = 2000 req/day. Wait or upgrade plan.

### Routes still pass through floods

**Possible causes**:

1. Backend not restarted after `.env` update
2. API key invalid/missing
3. Test mode not enabled (no flooded areas)
4. Check logs for actual avoid_polygons being sent

## 📊 API Comparison

| Feature             | GraphHopper Free | OpenRouteService Free     |
| ------------------- | ---------------- | ------------------------- |
| Avoid Areas         | ❌ No            | ✅ Yes (`avoid_polygons`) |
| Daily Limit         | 2500 req         | 2000 req                  |
| Vietnam Support     | ✅ Good          | ✅ Good                   |
| Free Forever        | ✅ Yes           | ✅ Yes                    |
| **Flood Avoidance** | ❌ **NO**        | ✅ **YES**                |

## 🎯 Next Steps

1. ✅ Get OpenRouteService API key
2. ✅ Add to `.env` file
3. ✅ Restart backend
4. ✅ Test with flooded routes
5. ✅ Verify avoidance works
6. 🚀 Deploy!

---

**Questions?** Check logs at `backend_service/logs/backend_service.log`

import httpx
import asyncio

AI_SERVICE_URL = "http://localhost:6000/classify" # Placeholder URL

async def check_flood_status(camera_data):
    """
    Check flood status for a list of cameras.
    
    Args:
        camera_data (list): List of dicts containing camera info.
                            Example: [{"id": "cam1", "coords": {"lat": 21.0, "lng": 105.8}, "snapshot_url": "..."}]
    
    Returns:
        list: List of coordinates that are flooded.
    """
    flooded_coords = []
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for cam in camera_data:
            # In a real scenario, we might send the snapshot URL or base64 image
            # Here we assume the AI service can fetch from a URL or we send a dummy payload for now
            payload = {
                "camera_id": cam.get("id"),
                "image_url": cam.get("snapshot_url", "") # Assuming snapshot_url is available or we handle image upload
            }
            tasks.append(client.post(AI_SERVICE_URL, json=payload))
        
        # Run requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"Error checking camera {camera_data[i].get('id')}: {response}")
                continue
                
            if response.status_code == 200:
                result = response.json()
                # Assuming AI service returns {"status": "FLOODED"} or {"status": "SAFE"}
                if result.get("status") == "FLOODED":
                    flooded_coords.append(camera_data[i]["coords"])
            else:
                print(f"AI Service returned {response.status_code} for camera {camera_data[i].get('id')}")

    return flooded_coords

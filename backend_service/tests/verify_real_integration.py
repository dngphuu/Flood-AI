import asyncio
import httpx
import respx
from backend_service.ai_service import check_flood_status

# Path to the test image
TEST_IMAGE_PATH = "tests/test.jpg"
MOCK_CAMERA_URL = "http://mock-camera/snapshot.jpg"

async def main():
    print("="*60)
    print("Verifying Real Integration with AI Service")
    print("="*60)

    # Read the test image
    try:
        with open(TEST_IMAGE_PATH, "rb") as f:
            image_bytes = f.read()
        print(f"[OK] Loaded test image: {TEST_IMAGE_PATH} ({len(image_bytes)} bytes)")
    except FileNotFoundError:
        print(f"[FAIL] Test image not found at {TEST_IMAGE_PATH}")
        return

    # Mock the camera snapshot URL to return the local image
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(MOCK_CAMERA_URL).respond(200, content=image_bytes)
        
        # Note: We are NOT mocking the AI Service URL. We want to hit the real one.
        # But we need to make sure respx doesn't block it.
        # respx by default blocks all requests unless passthrough is enabled or specific routes are mocked.
        # However, since we are using `with respx.mock`, it might block others.
        # Let's explicitly allow the AI service URL or just mock the camera URL specifically.
        # Actually, respx.mock captures all requests. We need to use `side_effect` or `pass_through`.
        
        # Better approach: Only mock the camera URL.
        # But `respx.mock` context manager captures everything.
        # We can use `mock.route(...).pass_through()` for everything else?
        # Or just use `respx.get(MOCK_CAMERA_URL).mock(...)` without the context manager if we were using the global mock,
        # but here we want a local scope.
        
        # Let's try to configure respx to pass through requests to localhost.
        mock.route(host="localhost").pass_through()
        
        camera_data = [
            {
                "id": "test_cam_1",
                "coords": {"lat": 21.0, "lng": 105.8},
                "snapshot_url": MOCK_CAMERA_URL
            }
        ]

        print(f"\n[1] Calling check_flood_status...")
        try:
            flooded_coords = await check_flood_status(camera_data)
            
            print(f"[OK] Function returned successfully")
            print(f"  Flooded coords: {flooded_coords}")
            
            if len(flooded_coords) > 0:
                print(f"  Result: FLOOD DETECTED (Expected for this image?)")
            else:
                print(f"  Result: NO FLOOD DETECTED")
                
        except Exception as e:
            print(f"[FAIL] check_flood_status failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

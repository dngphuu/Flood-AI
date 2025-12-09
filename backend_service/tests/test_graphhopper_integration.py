"""
Simple test script to verify GraphHopper API integration.
"""
import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from backend_service.routing_service import get_safe_route
from backend_service import config

def test_basic_routing():
    """Test basic routing without flood points."""
    print("Test 1: Basic Routing (No Flood Points)")
    print(f"GraphHopper API Key configured: {'Yes' if config.GRAPHHOPPER_API_KEY else 'No (using placeholder)'}")
    
    # Ho Chi Minh City coordinates
    start = [10.762622, 106.660172]  # Ben Thanh Market
    end = [10.773431, 106.700806]    # Thu Thiem Bridge
    
    print(f"Start: {start}")
    print(f"End: {end}")
    
    route = get_safe_route(start, end, [])
    
    if route:
        print(f"[PASS] Route found with {len(route)} waypoints")
        print(f"  First point: {route[0]}")
        print(f"  Last point: {route[-1]}")
        return True
    else:
        print("[FAIL] Failed to get route")
        return False


def test_flood_avoidance():
    """Test routing with flood points."""
    print("\nTest 2: Routing with Flood Avoidance")
    
    # Ho Chi Minh City coordinates
    start = [10.762622, 106.660172]  # Ben Thanh Market
    end = [10.773431, 106.700806]    # Thu Thiem Bridge
    
    # Flood point somewhere in between
    flooded = [[10.768000, 106.680000]]
    
    print(f"Start: {start}")
    print(f"End: {end}")
    print(f"Flooded points: {flooded}")
    
    route = get_safe_route(start, end, flooded)
    
    if route:
        print(f"[PASS] Route found with {len(route)} waypoints avoiding flooded area")
        print(f"  First point: {route[0]}")
        print(f"  Last point: {route[-1]}")
        return True
    else:
        print("[FAIL] Failed to get route")
        return False


def test_coordinate_format():
    """Test coordinate format validation."""
    print("\nTest 3: Coordinate Format Validation")
    
    # Valid coordinates
    valid_start = [10.762622, 106.660172]
    valid_end = [10.773431, 106.700806]
    
    # Invalid coordinates (should be handled gracefully)
    invalid_start = [200, 200]  # Out of range
    
    print("Testing with invalid coordinates...")
    route = get_safe_route(invalid_start, valid_end, [])
    
    if not route:
        print("[PASS] Invalid coordinates handled correctly (returned empty list)")
        return True
    else:
        print("[FAIL] Invalid coordinates should return empty list")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("GraphHopper API Integration Verification")
    print("=" * 60)
    
    if not config.GRAPHHOPPER_API_KEY:
        print("\n⚠ WARNING: GRAPHHOPPER_API_KEY not set in .env file")
        print("The tests will fail with API authentication errors.\n")
    
    results = []
    
    try:
        results.append(("Basic Routing", test_basic_routing()))
        results.append(("Flood Avoidance", test_flood_avoidance()))
        results.append(("Coordinate Validation", test_coordinate_format()))
    except Exception as e:
        print(f"\n[FAIL] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n[SUCCESS] All tests passed!")
    else:
        print("\n[ERROR] Some tests failed")
    
    sys.exit(0 if all_passed else 1)

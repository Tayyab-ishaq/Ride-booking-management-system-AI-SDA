"""
Test script for the GET /matching/status/{ride_id} endpoint.
Tests the polling endpoint for match progress.
"""
import asyncio
import httpx
import json
from uuid import uuid4

# Configuration
API_BASE_URL = "http://localhost:8000/api"
RIDER_EMAIL = "test_rider@example.com"
RIDER_PASSWORD = "TestPassword123!"
DRIVER_EMAIL = "test_driver@example.com"
DRIVER_PASSWORD = "TestPassword123!"


async def test_matching_status_endpoint():
    """Test the matching status polling endpoint"""
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # ============================================
        # 1. Register a rider
        # ============================================
        print("1. Registering rider...")
        rider_register_payload = {
            "email": f"rider_{uuid4().hex[:8]}@example.com",
            "password": RIDER_PASSWORD,
            "role": "rider"
        }
        resp = await client.post(
            f"{API_BASE_URL}/auth/register",
            json=rider_register_payload
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 201:
            print(f"   ✓ Rider registered successfully")
        else:
            print(f"   ✗ Error: {resp.text}")
            return
        
        # ============================================
        # 2. Login rider
        # ============================================
        print("\n2. Logging in rider...")
        rider_login_payload = {
            "email": rider_register_payload["email"],
            "password": RIDER_PASSWORD
        }
        resp = await client.post(
            f"{API_BASE_URL}/auth/login",
            json=rider_login_payload
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            rider_tokens = resp.json()
            rider_access_token = rider_tokens["access_token"]
            print(f"   ✓ Rider logged in successfully")
        else:
            print(f"   ✗ Error: {resp.text}")
            return
        
        rider_headers = {"Authorization": f"Bearer {rider_access_token}"}
        
        # ============================================
        # 3. Create a ride request
        # ============================================
        print("\n3. Creating a ride request...")
        ride_payload = {
            "origin": "123 Main Street, Downtown",
            "destination": "456 Park Avenue, Uptown"
        }
        resp = await client.post(
            f"{API_BASE_URL}/rides/create",
            json=ride_payload,
            headers=rider_headers
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 201:
            ride_data = resp.json()
            ride_id = ride_data["id"]
            print(f"   ✓ Ride created: {ride_id}")
            print(f"   Initial status: {ride_data['status']}")
        else:
            print(f"   ✗ Error: {resp.text}")
            return
        
        # ============================================
        # 4. Test GET /matching/status/{ride_id} - Before finding driver
        # ============================================
        print(f"\n4. Testing GET /matching/status/{ride_id} (before finding driver)...")
        resp = await client.get(
            f"{API_BASE_URL}/matching/status/{ride_id}",
            headers=rider_headers
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            status_data = resp.json()
            print(f"   ✓ Status retrieved successfully")
            print(f"   Response:")
            print(f"     - ID: {status_data['id']}")
            print(f"     - Status: {status_data['status']}")
            print(f"     - Driver ID: {status_data['driver_id']}")
            print(f"     - Fare: {status_data['fare']}")
            print(f"     - Created at: {status_data['created_at']}")
            print(f"     - Updated at: {status_data['updated_at']}")
        else:
            print(f"   ✗ Error: {resp.status_code}")
            print(f"   Response: {resp.text}")
            return
        
        # ============================================
        # 5. Register and login a driver
        # ============================================
        print("\n5. Registering driver...")
        driver_register_payload = {
            "email": f"driver_{uuid4().hex[:8]}@example.com",
            "password": DRIVER_PASSWORD,
            "role": "driver"
        }
        resp = await client.post(
            f"{API_BASE_URL}/auth/register",
            json=driver_register_payload
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 201:
            print(f"   ✓ Driver registered successfully")
        else:
            print(f"   ✗ Error: {resp.text}")
            return
        
        print("\n6. Logging in driver...")
        driver_login_payload = {
            "email": driver_register_payload["email"],
            "password": DRIVER_PASSWORD
        }
        resp = await client.post(
            f"{API_BASE_URL}/auth/login",
            json=driver_login_payload
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            driver_tokens = resp.json()
            driver_access_token = driver_tokens["access_token"]
            print(f"   ✓ Driver logged in successfully")
        else:
            print(f"   ✗ Error: {resp.text}")
            return
        
        # ============================================
        # 7. Find driver for the ride
        # ============================================
        print(f"\n7. Finding driver for ride {ride_id}...")
        find_payload = {"ride_id": ride_id}
        resp = await client.post(
            f"{API_BASE_URL}/matching/find",
            json=find_payload,
            headers=rider_headers
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            ride_data = resp.json()
            print(f"   ✓ Driver found!")
            print(f"   New status: {ride_data['status']}")
            print(f"   Driver ID: {ride_data['driver_id']}")
        else:
            print(f"   ✗ Error: {resp.text}")
            return
        
        # ============================================
        # 8. Test GET /matching/status/{ride_id} - After finding driver
        # ============================================
        print(f"\n8. Testing GET /matching/status/{ride_id} (after finding driver)...")
        resp = await client.get(
            f"{API_BASE_URL}/matching/status/{ride_id}",
            headers=rider_headers
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            status_data = resp.json()
            print(f"   ✓ Status retrieved successfully")
            print(f"   Response:")
            print(f"     - Status: {status_data['status']}")
            print(f"     - Driver ID: {status_data['driver_id']}")
            print(f"     - Fare: {status_data['fare']}")
        else:
            print(f"   ✗ Error: {resp.status_code}")
            print(f"   Response: {resp.text}")
            return
        
        # ============================================
        # 9. Test error case: non-existent ride
        # ============================================
        print(f"\n9. Testing GET /matching/status with non-existent ride ID...")
        fake_ride_id = str(uuid4())
        resp = await client.get(
            f"{API_BASE_URL}/matching/status/{fake_ride_id}",
            headers=rider_headers
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   ✓ Correctly returned error for non-existent ride")
            print(f"   Response: {resp.text[:100]}...")
        else:
            print(f"   ✗ Should have returned error but got: {resp.text}")
            return
        
        # ============================================
        # 10. Test error case: unauthorized access (different rider)
        # ============================================
        print(f"\n10. Testing unauthorized access with different rider...")
        
        # Register and login another rider
        another_rider_payload = {
            "email": f"rider_{uuid4().hex[:8]}@example.com",
            "password": RIDER_PASSWORD,
            "role": "rider"
        }
        resp = await client.post(
            f"{API_BASE_URL}/auth/register",
            json=another_rider_payload
        )
        
        resp = await client.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "email": another_rider_payload["email"],
                "password": RIDER_PASSWORD
            }
        )
        another_rider_token = resp.json()["access_token"]
        another_rider_headers = {"Authorization": f"Bearer {another_rider_token}"}
        
        # Try to access the original ride
        resp = await client.get(
            f"{API_BASE_URL}/matching/status/{ride_id}",
            headers=another_rider_headers
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   ✓ Correctly returned error for unauthorized access")
            print(f"   Response: {resp.text[:100]}...")
        else:
            print(f"   ✗ Should have returned error but got: {resp.text}")
        
        print("\n" + "="*60)
        print("✓ All tests completed!")
        print("="*60)


if __name__ == "__main__":
    print("Testing GET /matching/status/{ride_id} endpoint")
    print("=" * 60)
    asyncio.run(test_matching_status_endpoint())

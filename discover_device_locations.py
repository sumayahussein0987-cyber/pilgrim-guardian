"""
Run this once to see the real, fixed location Nokia's simulator returns
for each of the 9 provided test device IDs. Use the results to pick:
- one device to represent "safe, inside the group"
- one device (with a very different location) to represent "drifted"

Then update safe_zone in main.py to surround your chosen "safe" device's
real coordinates, and use the "drifted" device's ID in your /demo/run calls.

Run with: python discover_device_locations.py
"""
import config
import camara_client_live as camara

for device_id in config.SIMULATOR_DEVICE_IDS:
    try:
        result = camara.location_retrieval(device_id)
        center = result["area"]["center"]
        print(f"{device_id:20s} -> lat={center['latitude']:.5f}, lng={center['longitude']:.5f}")
    except Exception as e:
        print(f"{device_id:20s} -> ERROR: {e}")

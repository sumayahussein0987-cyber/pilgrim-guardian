"""
Tracking Agent
--------------
Owns: Location Retrieval, Location Verification, Geofencing.
Job: know where each group member is, and flag the moment they leave
the group's defined safe zone.
"""
from dataclasses import dataclass
import camara_client as camara


@dataclass
class SafeZone:
    center_lat: float
    center_lng: float
    radius_m: float


class TrackingAgent:
    def __init__(self, safe_zone: SafeZone):
        self.safe_zone = safe_zone

    def check_device(self, device_id: str) -> dict:
        """Returns the device's last location plus whether it has drifted."""
        location = camara.location_retrieval(device_id)
        verification = camara.location_verification(
            device_id,
            self.safe_zone.center_lat,
            self.safe_zone.center_lng,
            self.safe_zone.radius_m,
        )
        inside_zone = verification["verificationResult"] == "TRUE"
        return {
            "device_id": device_id,
            "location": location["area"]["center"],
            "last_location_time": location["lastLocationTime"],
            "inside_safe_zone": inside_zone,
            "drifted": not inside_zone,
        }

    def subscribe_geofence(self, device_id: str):
        """Registers a real-time exit alert (fires immediately in mock mode)."""
        return camara.geofencing_subscribe(
            device_id,
            self.safe_zone.center_lat,
            self.safe_zone.center_lng,
            self.safe_zone.radius_m,
        )

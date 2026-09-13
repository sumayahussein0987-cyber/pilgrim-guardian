"""
Fake versions of the 7 CAMARA APIs Pilgrim Guardian uses.

Response shapes are copied from Nokia's own API Playground examples, so
swapping these out for real calls later (see camara_client.py) requires no
changes to any agent code — only the CAMARA_MODE env var needs to flip.
"""
import random
import uuid
from datetime import datetime, timedelta, timezone

# In-memory store so a demo run behaves consistently across calls.
_device_state = {}


def _now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _get_or_init_device(device_id, base_lat=21.4225, base_lng=39.8262):
    """Defaults to Masjid al-Haram coordinates as the group's safe-zone center."""
    if device_id not in _device_state:
        _device_state[device_id] = {
            "lat": base_lat + random.uniform(-0.002, 0.002),
            "lng": base_lng + random.uniform(-0.002, 0.002),
            "connectivity": "CONNECTED_DATA",
            "swapped": False,
        }
    return _device_state[device_id]


def nudge_device(device_id, drift=True):
    """Test helper: move a device away from (or back toward) the safe zone."""
    state = _get_or_init_device(device_id)
    if drift:
        # Randomize DIRECTION as well as distance (not just magnitude), so
        # repeated demo runs can drift the pilgrim toward different sides
        # of the safe zone — otherwise every run drifts the same direction
        # and the "calmest nearby zone" selection always picks the same one.
        state["lat"] += random.uniform(0.01, 0.03) * random.choice([-1, 1])
        state["lng"] += random.uniform(0.01, 0.03) * random.choice([-1, 1])
        state["connectivity"] = random.choice(["CONNECTED_SMS", "NOT_CONNECTED"])
    else:
        state["lat"], state["lng"] = 21.4225, 39.8262
        state["connectivity"] = "CONNECTED_DATA"
    return state


def location_retrieval(device_id, max_age=600):
    state = _get_or_init_device(device_id)
    return {
        "lastLocationTime": _now_iso(),
        "area": {
            "areaType": "CIRCLE",
            "center": {"latitude": state["lat"], "longitude": state["lng"]},
            "radius": 1000,
        },
    }


def location_verification(device_id, center_lat, center_lng, radius_m, max_age=120):
    state = _get_or_init_device(device_id)
    dist = _haversine(state["lat"], state["lng"], center_lat, center_lng)
    return {
        "verificationResult": "TRUE" if dist <= radius_m else "FALSE",
        "lastLocationTime": _now_iso(),
    }


def geofencing_subscribe(device_id, center_lat, center_lng, radius_m):
    return {
        "protocol": "HTTP",
        "sink": "https://mock-sink.pilgrim-guardian.local",
        "types": ["org.camaraproject.geofencing-subscriptions.v0.area-entered"],
        "config": {
            "subscriptionDetail": {
                "device": {"phoneNumber": device_id},
                "area": {
                    "areaType": "CIRCLE",
                    "center": {"latitude": center_lat, "longitude": center_lng},
                    "radius": radius_m,
                },
            },
            "subscriptionMaxEvents": 10,
            "initialEvent": True,
        },
        "id": str(uuid.uuid4()),
        "startsAt": _now_iso(),
    }


def device_status(device_id):
    state = _get_or_init_device(device_id)
    return {"connectivityStatus": state["connectivity"]}


def sim_swap_check(device_id, max_age=240):
    state = _get_or_init_device(device_id)
    return {"swapped": state["swapped"]}


def sim_swap_last_change(device_id):
    return {
        "latestSimChange": (
            datetime.now(timezone.utc) - timedelta(days=30)
        ).isoformat().replace("+00:00", "Z")
    }


def qod_create_session(device_id, qos_profile="QOS_E", duration=3600):
    return {
        "qosProfile": qos_profile,
        "device": {"phoneNumber": device_id},
        "sessionId": str(uuid.uuid4()),
        "qosStatus": "REQUESTED",
        "startedAt": _now_iso(),
        "duration": duration,
    }


def number_verification(device_id, expected_number):
    return {"devicePhoneNumberVerified": device_id == expected_number}


def _haversine(lat1, lon1, lat2, lon2):
    import math

    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

"""
Real calls to Nokia's CAMARA APIs.

IMPORTANT: The exact endpoint path for each API can differ slightly by
version (e.g. Location Verification has both v0.2.0 and v1.0.0 in your
sidebar). Rather than guess, copy the exact path for each endpoint from
the "Code Snippets" tab in the API Playground (where you just got your
200 OK) and paste it into the PATHS dict below. This took you 30 seconds
per endpoint and guarantees you're hitting the version you tested.

Every function here mirrors the signature of the matching function in
mocks/camara_mock.py, so agents/*.py never need to know which mode is active.
"""
import httpx
import config

HEADERS = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": config.NOKIA_RAPIDAPI_KEY,
    "X-RapidAPI-Host": config.NOKIA_RAPIDAPI_HOST,
}

# TODO: paste real paths from the Playground's "Code Snippets" tab for each endpoint you use.
PATHS = {
    "location_retrieval": "/location-retrieval/v0/retrieve",
    "location_verification": "/location-verification/v1/verify",
    "geofencing_subscribe": "/geofencing-subscriptions/v0.3/subscriptions",
    "device_status": "/device-status/v0/connectivity",
    "sim_swap_check": "/passthrough/camara/v1/sim-swap/sim-swap/v0/check",
    "sim_swap_last_change": "/passthrough/camara/v1/sim-swap/sim-swap/v0/retrieve-date",
    "qod_create_session": "/qod/v0/sessions",
}


def _post(path_key, body):
    url = config.NOKIA_BASE_URL + PATHS[path_key]
    resp = httpx.post(url, headers=HEADERS, json=body, timeout=15)
    resp.raise_for_status()
    return resp.json()


def location_retrieval(device_id, max_age=600):
    return _post("location_retrieval", {"device": {"phoneNumber": device_id}, "maxAge": max_age})


def location_verification(device_id, center_lat, center_lng, radius_m, max_age=120):
    body = {
        "device": {"phoneNumber": device_id},
        "area": {
            "areaType": "CIRCLE",
            "center": {"latitude": center_lat, "longitude": center_lng},
            "radius": radius_m,
        },
        "maxAge": max_age,
    }
    return _post("location_verification", body)


def geofencing_subscribe(device_id, center_lat, center_lng, radius_m):
    body = {
        "protocol": "HTTP",
        "sink": "https://your-webhook-receiver.example.com",  # TODO: real or mocked webhook URL
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
            "initialEvent": True,
            "subscriptionMaxEvents": 10,
        },
    }
    return _post("geofencing_subscribe", body)


def device_status(device_id):
    return _post("device_status", {"device": {"phoneNumber": device_id}})


def sim_swap_check(device_id, max_age=240):
    return _post("sim_swap_check", {"phoneNumber": device_id, "maxAge": max_age})


def sim_swap_last_change(device_id):
    return _post("sim_swap_last_change", {"phoneNumber": device_id})


def qod_create_session(device_id, qos_profile="QOS_E", duration=3600):
    body = {
        "qosProfile": qos_profile,
        "device": {"phoneNumber": device_id, "ipv4Address": {"publicAddress": "1.1.1.1", "privateAddress": "1.1.1.1"}},
        "applicationServer": {"ipv4Address": "1.1.1.1"},
        "duration": duration,
    }
    return _post("qod_create_session", body)

"""
Pilgrim Guardian — end-to-end pipeline

Run with:  uvicorn main:app --reload
Then visit:
  http://127.0.0.1:8000/docs       interactive API docs
  http://127.0.0.1:8000/dashboard  operations console (authority-facing)
  http://127.0.0.1:8000/pilgrim    pilgrim phone view (person-facing)
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import config
from mocks.camara_mock import nudge_device
from agents.tracking_agent import TrackingAgent, SafeZone
from agents.risk_agent import RiskAgent
from agents.response_agent import ResponseAgent
from agents.guidance_agent import GuidanceAgent

app = FastAPI(title="Pilgrim Guardian")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Masjid al-Haram coordinates as the default group safe zone, 300m radius.
safe_zone = SafeZone(center_lat=21.4225, center_lng=39.8262, radius_m=300)

# Named assembly points a drifted pilgrim can be routed to, each with a
# simulated congestion level. The Guidance Agent picks the calmest nearby
# one instead of always pointing back to the same fixed spot — this is
# the "avoid the crowded road, go somewhere calmer nearby" feature.
ASSEMBLY_ZONES = [
    {"name": "King Fahd Gate", "center_lat": 21.4225, "center_lng": 39.8262, "radius_m": 300, "congestion": "HIGH"},
    {"name": "Gate 1", "center_lat": 21.4210, "center_lng": 39.8210, "radius_m": 300, "congestion": "LOW"},
    {"name": "Gate 79", "center_lat": 21.4230, "center_lng": 39.8230, "radius_m": 300, "congestion": "MEDIUM"},
    {"name": "Ajyad Gate", "center_lat": 21.4242, "center_lng": 39.8280, "radius_m": 300, "congestion": "LOW"},
]

tracking_agent = TrackingAgent(safe_zone)
risk_agent = RiskAgent()
response_agent = ResponseAgent()
guidance_agent = GuidanceAgent()

# Caches the last agentic guidance result per device, so the pilgrim phone's
# 3-second polling reuses the reasoning already done when the dashboard
# triggered the alert, instead of re-running a multi-turn Claude conversation
# on every single poll (slow and needlessly expensive).
_guidance_cache: dict[str, dict] = {}


def _get_or_compute_guidance(risk_result: dict, language: str = "English") -> dict:
    device_id = risk_result["device_id"]
    cached = _guidance_cache.get(device_id)
    if cached is not None:
        return cached

    text, trace, selected_zone = guidance_agent.generate_directions_agentic(
        risk_result, ASSEMBLY_ZONES, language=language,
    )
    target = guidance_agent._zone_to_target(selected_zone)
    result = {"guidance_message": text, "agent_trace": trace, "target_zone": target}
    _guidance_cache[device_id] = result
    return result


class DemoRequest(BaseModel):
    device_id: str = "+99999991000"
    responder_id: str = "responder-001"
    language: str = "English"
    simulate_drift: bool = True
    # Optional: override the safe zone for this run only. Leave blank to use
    # the default (Mecca). Nokia's simulator returns the SAME fixed location
    # for every test device, so to demo the "pilgrim is safe" scenario live,
    # pass the simulator's real coordinates here instead:
    # safe_zone_lat=47.48628, safe_zone_lng=19.07916, safe_zone_radius_m=1000
    safe_zone_lat: float | None = None
    safe_zone_lng: float | None = None
    safe_zone_radius_m: float | None = None


@app.get("/")
def root():
    return {
        "service": "Pilgrim Guardian",
        "camara_mode": config.CAMARA_MODE,
        "simulator_device_ids": config.SIMULATOR_DEVICE_IDS,
    }


@app.get("/dashboard")
def dashboard():
    """Authority-facing operations console."""
    return FileResponse("static/index.html")


@app.get("/pilgrim")
def pilgrim_view():
    """Person-facing phone screen. Open this on an actual phone for the demo."""
    return FileResponse("static/pilgrim.html")


@app.post("/demo/run")
def run_demo(req: DemoRequest):
    """
    Fires the full 4-agent pipeline once, end to end. This is the exact
    flow to trigger live during your hackathon demo from the dashboard.
    """
    if req.simulate_drift and config.CAMARA_MODE == "mock":
        nudge_device(req.device_id, drift=True)

    active_zone = safe_zone
    if req.safe_zone_lat is not None and req.safe_zone_lng is not None:
        active_zone = SafeZone(
            center_lat=req.safe_zone_lat,
            center_lng=req.safe_zone_lng,
            radius_m=req.safe_zone_radius_m or safe_zone.radius_m,
        )
    active_tracking_agent = TrackingAgent(active_zone)

    tracking_result = active_tracking_agent.check_device(req.device_id)
    risk_result = risk_agent.score(tracking_result)

    # Reflects the actual CAMARA_MODE rather than assuming "mock" — this
    # trace is shown on the dashboard, so it needs to stay honest whether
    # you're running against the simulator or the real Nokia sandbox.
    mode_label = f"{config.CAMARA_MODE} CAMARA API"

    if not risk_result["high_risk"]:
        service_trace = [
            {"service": "location_retrieval", "status": "resolved", "detail": mode_label},
            {"service": "location_verification", "status": "resolved", "detail": f"safe zone check: {tracking_result['inside_safe_zone']}"},
            {"service": "device_status", "status": "resolved", "detail": f"connectivity: {risk_result['connectivity']}"},
            {"service": "qod_create_session", "status": "skipped", "detail": "no alert triggered"},
            {"service": "sim_swap_check", "status": "skipped", "detail": "no alert triggered"},
        ]
        return {"status": "no_action_needed", "risk_result": risk_result, "service_trace": service_trace}

    fraud_check = guidance_agent.run_fraud_check(req.device_id)
    alert = response_agent.notify_responder(risk_result, req.responder_id)

    guidance = _get_or_compute_guidance(risk_result, language=req.language)
    service_trace = [
        {"service": "location_retrieval", "status": "resolved", "detail": mode_label},
        {"service": "location_verification", "status": "resolved", "detail": f"safe zone check: {tracking_result['inside_safe_zone']}"},
        {"service": "device_status", "status": "resolved", "detail": f"connectivity: {risk_result['connectivity']}"},
        {"service": "qod_create_session", "status": "resolved", "detail": f"responder: {alert['responder_id']}"},
        {"service": "sim_swap_check", "status": "resolved", "detail": f"swapped: {fraud_check['swapped']}"},
    ]


    return {
        "status": "alert_triggered",
        "risk_result": risk_result,
        "fraud_check": fraud_check,
        "response_alert": alert,
        "guidance_message": guidance["guidance_message"],
        "agent_trace": guidance["agent_trace"],
        "target_zone": guidance["target_zone"],
        "service_trace": service_trace,
    }


@app.post("/demo/reset")
def reset_demo(device_id: str = "+99999991000"):
    nudge_device(device_id, drift=False)
    _guidance_cache.pop(device_id, None)
    return {"status": "reset", "device_id": device_id}


@app.get("/pilgrim/status")
def pilgrim_status(device_id: str = "+99999991000"):
    """
    Read-only status check polled by the pilgrim's phone screen every few
    seconds. Deliberately only runs Tracking + Risk (never re-notifies a
    responder on every poll) — it reflects whatever state the dashboard's
    /demo/run last put the mock device into, since both endpoints share the
    same in-memory device state in mock mode. Guidance text/trace comes from
    the cache populated by /demo/run, so repeated polling doesn't re-trigger
    Claude's reasoning loop.
    """
    tracking_result = tracking_agent.check_device(device_id)
    risk_result = risk_agent.score(tracking_result)

    if not risk_result["high_risk"]:
        return {
            "status": "safe",
            "risk_result": risk_result,
            "group_center": {"lat": safe_zone.center_lat, "lng": safe_zone.center_lng},
        }

    guidance = _get_or_compute_guidance(risk_result)

    return {
        "status": "alert",
        "risk_result": risk_result,
        "guidance_message": guidance["guidance_message"],
        "target_zone": guidance["target_zone"],
        "group_center": {"lat": guidance["target_zone"]["center_lat"], "lng": guidance["target_zone"]["center_lng"]},
    }

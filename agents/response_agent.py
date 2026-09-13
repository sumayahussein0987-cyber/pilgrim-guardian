"""
Response Agent
---------------
Owns: Number Verification, Quality on Demand (QoD).
Job: when risk crosses the threshold, confirm the responder's identity and
guarantee the alert channel actually gets through, even in a congested network.

Note: Number Verification uses a 3-legged OAuth flow requiring the end-user's
device to complete a redirect (see Nokia's docs). That's overkill for a
hackathon demo — this agent mocks that confirmation step and focuses the
real integration effort on QoD, which is simpler two-legged auth.
"""
import camara_client as camara


class ResponseAgent:
    def __init__(self):
        self.alert_log = []

    def notify_responder(self, risk_result: dict, responder_id: str) -> dict:
        # In production: run the 3-legged Number Verification consent flow here.
        responder_verified = True  # mocked for demo purposes

        qod_session = camara.qod_create_session(risk_result["device_id"], duration=1800)

        alert = {
            "device_id": risk_result["device_id"],
            "responder_id": responder_id,
            "responder_verified": responder_verified,
            "risk_score": risk_result["risk_score"],
            "location": risk_result["location"],
            "qod_session_id": qod_session["sessionId"],
            "qod_status": qod_session["qosStatus"],
        }
        self.alert_log.append(alert)
        return alert

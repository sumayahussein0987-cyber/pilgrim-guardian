"""
Risk Agent
----------
Owns: Device Status/Reachability, Congestion Insights (mocked here since
Congestion Insights isn't in your current sandbox catalog — see note below).
Job: turn raw signals into one risk score per person, without waiting for
a manual SOS.
"""
import camara_client as camara
import config


def _congestion_level(device_id: str) -> str:
    """
    Congestion Insights wasn't confirmed available in your sandbox catalog.
    This stub keeps the Risk Agent's interface stable — swap in a real call
    here the moment you confirm the API is available on your plan.

    Deliberately fixed (not randomized) so repeated polls — e.g. from the
    pilgrim phone view every few seconds — don't flicker between risk
    levels on their own. For the demo, "HIGH" tells the more dramatic,
    consistent story of a congested mass gathering.
    """
    return "HIGH"


class RiskAgent:
    def __init__(self, threshold: float = None):
        self.threshold = threshold or config.RISK_THRESHOLD

    def score(self, tracking_result: dict) -> dict:
        device_id = tracking_result["device_id"]
        status = camara.device_status(device_id)
        connectivity = status["connectivityStatus"]
        congestion = _congestion_level(device_id)

        score = 0
        if tracking_result["drifted"]:
            score += 50
        if connectivity == "NOT_CONNECTED":
            score += 30
        elif connectivity == "CONNECTED_SMS":
            score += 15
        if congestion == "HIGH":
            score += 20
        elif congestion == "MEDIUM":
            score += 10

        return {
            **tracking_result,
            "connectivity": connectivity,
            "congestion": congestion,
            "risk_score": score,
            "high_risk": score >= self.threshold,
        }

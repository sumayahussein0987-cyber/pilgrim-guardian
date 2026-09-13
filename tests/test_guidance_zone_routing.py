import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.guidance_agent import GuidanceAgent


class GuidanceZoneRoutingTest(unittest.TestCase):
    def test_guidance_agent_selects_lowest_congestion_nearby_zone_and_explains_reason(self):
        agent = GuidanceAgent()
        risk_result = {
            "device_id": "+99999991000",
            "location": {"latitude": 21.4225, "longitude": 39.8262},
            "inside_safe_zone": False,
            "drifted": True,
        }

        zones = [
            {"name": "King Fahd Gate", "center_lat": 21.4225, "center_lng": 39.8262, "radius_m": 300, "congestion": "HIGH"},
            {"name": "Gate 1", "center_lat": 21.4210, "center_lng": 39.8210, "radius_m": 300, "congestion": "LOW"},
            {"name": "Gate 79", "center_lat": 21.4230, "center_lng": 39.8230, "radius_m": 300, "congestion": "MEDIUM"},
        ]

        text = agent.generate_directions(
            risk_result,
            {"center_lat": 21.4225, "center_lng": 39.8262},
            language="English",
            zones=zones,
        )

        self.assertIn("Gate 1", text)
        self.assertTrue("least crowded" in text.lower() or "calmest" in text.lower())


if __name__ == "__main__":
    unittest.main()

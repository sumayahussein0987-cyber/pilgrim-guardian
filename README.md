# Pilgrim Guardian

AI-powered crowd safety pipeline built on Nokia Network as Code (CAMARA APIs).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env: paste your NOKIA_RAPIDAPI_KEY and (optionally) ANTHROPIC_API_KEY
```

## Run

```bash
uvicorn main:app --reload
```

Then open:
- http://127.0.0.1:8000/dashboard — the authority-facing operations console (trigger scenarios here)
- http://127.0.0.1:8000/pilgrim — the person-facing phone screen (open this on an actual phone on the same wifi for the demo — see below)
- http://127.0.0.1:8000/docs — interactive Swagger docs for every endpoint

### Demoing on a real phone

1. Find your computer's local IP address (e.g. `ipconfig` on Windows, look for something like `192.168.1.42`).
2. Make sure your phone is on the **same wifi network** as your laptop.
3. On your phone's browser, go to `http://<your-computer-ip>:8000/pilgrim` (e.g. `http://192.168.1.42:8000/pilgrim`).
4. On your laptop, open `/dashboard` and click "Simulate drift" — within ~3 seconds the phone screen updates on its own with a compass pointing back to the group and the guidance message. This live two-device sync is the strongest moment in the demo.

## Try the full pipeline

```bash
curl -X POST http://127.0.0.1:8000/demo/run \
  -H "Content-Type: application/json" \
  -d '{"device_id": "+99999991000", "simulate_drift": true, "language": "English"}'
```

This runs all four agents in sequence:
1. **Tracking Agent** detects the simulated device has drifted from the safe zone.
2. **Risk Agent** scores the risk using drift + connectivity + congestion.
3. If risk crosses the threshold: **Response Agent** verifies a responder and opens a QoD session; **Guidance Agent** runs a SIM swap check and generates directions.

Reset a device back inside the safe zone with:
```bash
curl -X POST "http://127.0.0.1:8000/demo/reset?device_id=+99999991000"
```

## Mock vs. Live mode

Everything runs against a local mock of the 7 CAMARA APIs by default
(`CAMARA_MODE=mock` in `.env`). This means your demo works even with no
internet or a flaky sandbox connection.

To switch to real Nokia sandbox calls:
1. Set `CAMARA_MODE=live` in `.env`.
2. Open the API Playground in the Nokia portal, run each endpoint you need,
   and copy the exact path shown in the "Code Snippets" tab.
3. Paste those paths into the `PATHS` dict in `camara_client_live.py`.

Every agent imports from `camara_client.py`, which switches implementations
automatically — no agent code needs to change.

## Known gaps to address before the demo

- **Congestion Insights** wasn't confirmed available on the sandbox catalog
  screenshot reviewed while building this — `agents/risk_agent.py` currently
  mocks this signal with a random value. Confirm availability and wire in
  the real call if it exists on your plan.
- **Number Verification** uses a 3-legged OAuth consent flow requiring the
  end user's device to complete a redirect — too heavy for a hackathon demo,
  so `agents/response_agent.py` mocks this confirmation. Fine for judging;
  flag as "integration-ready" in your pitch if asked.
- Geofencing subscriptions are set up but this scaffold polls location on
  request rather than truly listening for a push webhook — sufficient for
  a live demo trigger, but not how it'd work in production.

## Project structure

```
config.py                # env vars + simulator device IDs
camara_client.py         # switches between mock/live automatically
camara_client_live.py    # real Nokia sandbox calls
mocks/camara_mock.py     # fake CAMARA responses, matches real response shapes
agents/tracking_agent.py # drift detection
agents/risk_agent.py     # risk scoring
agents/response_agent.py # responder alerting + QoD
agents/guidance_agent.py # SIM swap check + Claude-generated directions
main.py                  # FastAPI app wiring it all together
```

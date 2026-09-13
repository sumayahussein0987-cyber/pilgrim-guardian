import os
from dotenv import load_dotenv

load_dotenv()

CAMARA_MODE = os.getenv("CAMARA_MODE", "mock")  # "mock" or "live"

NOKIA_RAPIDAPI_KEY = os.getenv("NOKIA_RAPIDAPI_KEY", "")
NOKIA_RAPIDAPI_HOST = os.getenv("NOKIA_RAPIDAPI_HOST", "network-as-code.nokia.rapidapi.com")
NOKIA_BASE_URL = os.getenv("NOKIA_BASE_URL", "https://network-as-code.p-eu.rapidapi.com")

RISK_THRESHOLD = float(os.getenv("RISK_THRESHOLD", "70"))

# Simulator device IDs provided by Nokia's sandbox docs — safe to use freely.
SIMULATOR_DEVICE_IDS = [
    "+99999991000",
    "+99999991001",
    "+99999990400",
    "+99999990404",
    "+99999990422",
    "+99999990500",
    "+99999990502",
    "+99999990503",
    "+99999990504",
]

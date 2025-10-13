
import os

# --- API Keys ---

TOMTOM_API_KEY = os.environ.get("TOMTOM_API_KEY", "YOUR_TOMTOM_API_KEY_HERE")

# --- Default App Settings ---
DEFAULT_PLACE = "Chennai, India"
DEFAULT_DEPARTURE = "Chennai Central Railway Station"
DEFAULT_DESTINATION = "Marina Beach"
USER_AGENT = "traffic_optimizer_v4_modular_flask"

# --- Traffic Configuration ---

TRAFFIC_LEVELS = {
    'heavy': {'color': 'red', 'weight': 4, 'multiplier': 2.5},
    'medium': {'color': 'orange', 'weight': 3, 'multiplier': 1.5},
    'light': {'color': 'green', 'weight': 2, 'multiplier': 1.0}
}
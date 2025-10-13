
import math
import logging
from geopy.geocoders import Nominatim
from . import config

logger = logging.getLogger(__name__)

def haversine(lat1, lon1, lat2, lon2):
    """Calculates the distance (in meters) between two lat/lon points."""
    R = 6371000  # Radius of Earth in meters
    try:
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    except Exception as e:
        logger.error(f"Haversine calculation error: {e}")
        return float('inf')

def geocode_address(address, place_name):
    """Converts a street address and place name into (latitude, longitude)."""
    try:
        geolocator = Nominatim(user_agent=config.USER_AGENT)
        location = geolocator.geocode(f"{address}, {place_name}", timeout=5)
        return (location.latitude, location.longitude) if location else None
    except Exception as e:
        logger.error(f"Geocoding error for {address}, {place_name}: {e}")
        return None

def get_base_speed(data):
    """Determines the max allowed speed (in km/h) for a road segment based on OSM data."""
    try:
        highway_type = data.get('highway', 'residential')
        if isinstance(highway_type, list): highway_type = highway_type[0]
        speed = None

        # Check for explicit maxspeed tag
        if 'maxspeed' in data:
            ms = data['maxspeed']
            if isinstance(ms, list): ms = ms[0]
            if isinstance(ms, str):
                ms = ms.lower()
                if 'mph' in ms:
                    try: speed = float(ms.replace(' mph', '')) * 1.60934
                    except ValueError: pass
                else:
                    try: speed = float(ms)
                    except ValueError: pass

        # Use default speed limits if maxspeed is not found
        if speed is None:
            speed_dict = {
                'motorway': 120, 'trunk': 90, 'primary': 80, 'secondary': 60,
                'tertiary': 50, 'residential': 40, 'service': 30, 'unclassified': 40,
                'living_street': 20
            }
            speed = speed_dict.get(highway_type, 40)
        return speed
    except Exception as e:
        logger.error(f"Get speed error: {e}")
        return 40
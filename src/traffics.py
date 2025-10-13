
import networkx as nx
import osmnx as ox
import requests
import logging
import random
from datetime import datetime
from . import config
from . import utils

logger = logging.getLogger(__name__)

# Configure OSMNx
ox.settings.log_console = False
ox.settings.use_cache = True
ox.settings.timeout = 600

def load_road_network(dep_lat, dep_lng, dest_lat, dest_lng):
    """Loads the road network graph from OSM based on the route bounding box."""
    try:
        center_lat = (dep_lat + dest_lat) / 2
        center_lng = (dep_lng + dest_lng) / 2
        
        # Calculate a reasonable distance buffer
        dist_m = utils.haversine(dep_lat, dep_lng, dest_lat, dest_lng)
        dist_buffer = dist_m * 0.75 + 5000 # 75% of the straight distance + 5km buffer

        # Load graph
        G = ox.graph_from_point((center_lat, center_lng), dist=int(dist_buffer), network_type='drive', simplify=True)
        if 'crs' not in G.graph: G.graph['crs'] = ox.settings.default_crs
        
        # Basic edge initialization (distance, base speed, time)
        for u, v, key, data in G.edges(keys=True, data=True):
            data['base_speed'] = utils.get_base_speed(data)
            data['distance'] = data.get('length', float('inf'))
            # Base travel time in seconds
            data['travel_time'] = data['distance'] / (data['base_speed'] / 3.6) if data['base_speed'] > 0 else float('inf')

        logger.info(f"Loaded graph: {len(G.nodes)} nodes, {len(G.edges)} edges")
        return G
    except Exception as e:
        logger.error(f"Error loading road network: {e}")
        return None

def get_tomtom_traffic_data(min_lat, max_lat, min_lon, max_lon):
    """Fetches real-time traffic flow data from the TomTom API."""
    api_key = config.TOMTOM_API_KEY
    if not api_key or api_key == "YOUR_TOMTOM_API_KEY_HERE":
        logger.warning("No valid TomTom API key provided. Using simulated traffic.")
        return []
        
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    # TomTom API uses a point-based search, providing the center of the bounding box
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {
        'key': api_key,
        'point': f"{center_lat},{center_lon}",
        'unit': 'kmh'
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        flow_data = data.get('flowSegmentData')
        return [flow_data] if isinstance(flow_data, dict) else flow_data if isinstance(flow_data, list) else []
    except Exception as e:
        logger.error(f"TomTom API error: {e}")
        return []

def initialize_traffic_conditions(G, dep_lat, dep_lng, dest_lat, dest_lng):
    """Applies either real-time or simulated traffic conditions to the graph edges."""
    
    min_lat, max_lat = min(dep_lat, dest_lat), max(dep_lat, dest_lat)
    min_lon, max_lon = min(dep_lng, dest_lng), max(dep_lng, dest_lng)
    
    tomtom_data = get_tomtom_traffic_data(min_lat, max_lat, min_lon, max_lon)

    # Default all edges to light traffic
    for u, v, key, data in G.edges(keys=True, data=True):
        data['traffic_level'] = 'light'
        data['traffic_color'] = config.TRAFFIC_LEVELS['light']['color']
        data['traffic_weight_score'] = 1  # Base score for pathfinding (1=low traffic)

    if tomtom_data:
        # Apply real-time TomTom data
        for segment in tomtom_data:
            if not isinstance(segment, dict): continue
            current_speed = segment.get('currentSpeed', 0)
            free_flow_speed = segment.get('freeFlowSpeed', 1)
            if free_flow_speed <= 0: continue
            
            speed_ratio = current_speed / free_flow_speed
            
            if speed_ratio < 0.4:
                traffic_level, score = 'heavy', 3
            elif speed_ratio < 0.7:
                traffic_level, score = 'medium', 2
            else:
                traffic_level, score = 'light', 1
                
            coords = segment.get('coordinates', {}).get('coordinate', [])
            if coords and len(coords) >= 2:
                start_coord, end_coord = coords[0], coords[-1]
                if isinstance(start_coord, dict) and isinstance(end_coord, dict):
                    try:
                        node1 = ox.distance.nearest_nodes(G, start_coord.get('longitude'), start_coord.get('latitude'))
                        node2 = ox.distance.nearest_nodes(G, end_coord.get('longitude'), end_coord.get('latitude'))
                        
                        for u, v in [(node1, node2), (node2, node1)]: # Check both directions
                            if v in G[u]:
                                for edge_key in G[u][v]:
                                    edge_data = G[u][v][edge_key]
                                    edge_data['traffic_level'] = traffic_level
                                    edge_data['traffic_color'] = config.TRAFFIC_LEVELS[traffic_level]['color']
                                    edge_data['traffic_weight_score'] = score
                                    # Update travel time based on real-time speed
                                    edge_data['travel_time'] = edge_data['distance'] / (current_speed / 3.6) if current_speed > 0 else edge_data['travel_time']
                    except Exception as e:
                        logger.debug(f"Error mapping TomTom segment: {e}")
    else: 
        # Simulation (if no API key or API fails)
        current_hour = datetime.now().hour
        is_rush = current_hour in [7, 8, 9, 17, 18, 19]
        
        for u, v, key, data in G.edges(keys=True, data=True):
            highway_type = data.get('highway', 'residential')
            if isinstance(highway_type, list): highway_type = highway_type[0]
            
            heavy_prob = 0.7 if is_rush and highway_type in ['motorway', 'trunk', 'primary'] else 0.3
            medium_prob = 0.2 if is_rush and highway_type in ['motorway', 'trunk', 'primary'] else 0.5
            traffic_roll = random.random()
            
            if traffic_roll < heavy_prob:
                traffic_level, score, multiplier = 'heavy', 3, config.TRAFFIC_LEVELS['heavy']['multiplier']
            elif traffic_roll < heavy_prob + medium_prob:
                traffic_level, score, multiplier = 'medium', 2, config.TRAFFIC_LEVELS['medium']['multiplier']
            else:
                traffic_level, score, multiplier = 'light', 1, config.TRAFFIC_LEVELS['light']['multiplier']
                
            data['traffic_level'] = traffic_level
            data['traffic_color'] = config.TRAFFIC_LEVELS[traffic_level]['color']
            data['traffic_weight_score'] = score
            
            # Simulate increased travel time
            data['travel_time'] = data['travel_time'] * multiplier
            
    return G
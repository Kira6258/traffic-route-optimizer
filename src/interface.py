import logging
from flask import Flask, render_template, request
import osmnx as ox
import networkx as nx
from . import config, utils, traffics, routes, visualization

logger = logging.getLogger(__name__)

def create_app():
    """Application factory function."""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='static')  
    
    app.config.from_object(config)
    
    @app.route("/", methods=["GET", "POST"])
    def index():
        """Handles the main route, processing form submission and displaying results."""
        
        # 1. Initialize variables
        place_name = request.form.get("place_name", config.DEFAULT_PLACE)
        departure_address = request.form.get("departure_address", config.DEFAULT_DEPARTURE)
        destination_address = request.form.get("destination_address", config.DEFAULT_DESTINATION)
        result_html = ""
        routes_summary = []
        
        # 2. Process form submission
        if request.method == "POST":
            try:
                if not place_name or not departure_address or not destination_address:
                    result_html = "<p class='error'>Please fill in all fields: location, departure address, and destination address.</p>"
                else:
                    # 3. Geocoding
                    dep_coords = utils.geocode_address(departure_address, place_name)
                    dest_coords = utils.geocode_address(destination_address, place_name)
                    
                    if not dep_coords or not dest_coords:
                        result_html = f"<p class='error'>Geocoding failed for one or both addresses. Try more specific addresses within {place_name}.</p>"
                    else:
                        dep_lat, dep_lng = dep_coords
                        dest_lat, dest_lng = dest_coords

                        # 4. Load Road Network and Initialize Traffic
                        G = traffics.load_road_network(dep_lat, dep_lng, dest_lat, dest_lng, place_name)
                        
                        if G is None:
                            result_html = "<p class='error'>Error loading road network. The area might be too large or too remote.</p>"
                        else:
                            G = traffics.initialize_traffic_conditions(G, dep_lat, dep_lng, dest_lat, dest_lng)

                            # 5. Find Nodes
                            departure_node = ox.distance.nearest_nodes(G, dep_lng, dep_lat)
                            destination_node = ox.distance.nearest_nodes(G, dest_lng, dest_lat)
                            
                            if departure_node is None or destination_node is None:
                                result_html = "<p class='error'>Could not locate exact road nodes for your addresses. Try slightly different addresses.</p>"
                            else:
                                # 6. Find Routes
                                routes_data = routes.find_all_route_options(G, departure_node, destination_node)
                                
                                if not routes_data:
                                    result_html = "<p class='error'>No routes found between the specified locations. The locations might be disconnected.</p>"
                                else:
                                    # 7. Format Route Information (for display)

                                    routes_summary = [] 
                                   
                                    for route_data in routes_data:
                                        
                                        if len(route_data) != 6:
                                            logger.error(f"Malformed route data encountered: Expected 6 items, got {len(route_data)}")
                                            continue

                                        label, path, time_s, distance_m, traffic_score, _ = route_data

                                        if not path: continue 
                                        
                                        time_min = time_s / 60
                                        distance_km = distance_m / 1000
                                        avg_traffic = traffic_score / (len(path) - 1) if len(path) > 1 else 0

                                        routes_summary.append({
                                            'label': label,
                                            'time_min': f"{time_min:.1f}",
                                            'distance_km': f"{distance_km:.1f}",
                                            'avg_traffic': f"{avg_traffic:.1f}"
                                        })

                                    
                                    # 8. Generate Map
                                    map_html = visualization.visualize_traffic_clean(G, routes_data)
                                    result_html = f"{map_html}" 

            except Exception as e:
                logger.error(f"Main processing error: {e}")
                result_html = f"<p class='error'>An unexpected error occurred: {str(e)}. Please check your inputs and try again.</p>"

       
        return render_template(
            'index.html', 
            result_html=result_html, 
            routes_summary=routes_summary,
            
            place_name=place_name, 
            departure_address=departure_address, 
            destination_address=destination_address
        )
        
    return app
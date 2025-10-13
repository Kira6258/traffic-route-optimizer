
import folium
import logging
from . import config

logger = logging.getLogger(__name__)

def visualize_traffic_clean(G, routes_data):
    """
    Generates an HTML representation of a Folium map showing traffic conditions 
    and the calculated route options.
    
    routes_data format: [(label, path, time_s, distance_m, traffic_score, edges_set), ...]
    """
    try:
        route_lats, route_lons = [], []
        
        # 1. Determine map boundaries and center
        for _, route, _, _, _, _ in routes_data:
            if route:
                for node in route:
                    node_data = G.nodes[node]
                    route_lats.append(node_data['y'])
                    route_lons.append(node_data['x'])
        
        if not route_lats: return ""
        min_lat, max_lat = min(route_lats), max(route_lats)
        min_lon, max_lon = min(route_lons), max(route_lons)
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # Adjust zoom based on the span of the routes
        span_lat = max_lat - min_lat
        span_lon = max_lon - min_lon
        zoom_start = 14
        if span_lat < 0.005 and span_lon < 0.005: zoom_start = 16
        elif span_lat < 0.01 and span_lon < 0.01: zoom_start = 15
        elif span_lat > 0.1 or span_lon > 0.1: zoom_start = 12

        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start, tiles='OpenStreetMap', control_scale=True, width='100%', height='600px')

        # 2. Draw background traffic
        added_edges = set()
        for u, v, key, data in G.edges(keys=True, data=True):
            # Only visualize major roads for a cleaner look
            highway_type = data.get('highway', '')
            if isinstance(highway_type, list): highway_type = highway_type[0]
            if highway_type not in ['motorway', 'trunk', 'primary', 'secondary', 'tertiary']: continue
            
            # Avoid drawing parallel edges in the same line twice (if bidir)
            edge_tuple = tuple(sorted((u, v)))
            if edge_tuple in added_edges: continue
            added_edges.add(edge_tuple)

            loc1 = (G.nodes[u]['y'], G.nodes[u]['x'])
            loc2 = (G.nodes[v]['y'], G.nodes[v]['x'])
            color = data.get('traffic_color', 'gray')
            
            folium.PolyLine(
                locations=[loc1, loc2],
                color=color,
                weight=config.TRAFFIC_LEVELS.get(data.get('traffic_level'), {'weight': 2})['weight'],
                opacity=0.4,
                tooltip=f"Traffic: {data.get('traffic_level', 'unknown')}"
            ).add_to(m)

        # 3. Draw routes
        route_colors = ['blue', 'brown', 'purple', 'pink']
        dash_styles = [None, '5, 5', '1, 5', '10, 5']
        
        for i, (label, route, time_s, distance_m, traffic_score, _) in enumerate(routes_data):
            if not route: continue
            
            route_coords = [[G.nodes[node]['y'], G.nodes[node]['x']] for node in route]
            time_min = time_s / 60
            distance_km = distance_m / 1000
            
            # Calculate average traffic score per edge
            avg_traffic = traffic_score / (len(route) - 1) if len(route) > 1 else 0

            folium.PolyLine(
                locations=route_coords,
                color=route_colors[i % len(route_colors)], # Cycle colors
                weight=8,
                opacity=0.95,
                dash_array=dash_styles[i % len(dash_styles)],
                popup=f"<b>{label}</b><br>Time: {time_min:.1f} min<br>Distance: {distance_km:.1f} km<br>Avg Traffic Score: {avg_traffic:.1f}",
                tooltip=label
            ).add_to(m)

        # 4. Add Start/End markers
        start_node = routes_data[0][1][0] if routes_data[0][1] else None
        end_node = routes_data[0][1][-1] if routes_data[0][1] else None
        
        if start_node:
            folium.Marker([G.nodes[start_node]['y'], G.nodes[start_node]['x']], popup="Start", icon=folium.Icon(color='green', icon='play', prefix='fa')).add_to(m)
        if end_node:
            folium.Marker([G.nodes[end_node]['y'], G.nodes[end_node]['x']], popup="End", icon=folium.Icon(color='red', icon='stop', prefix='fa')).add_to(m)

        # 5. Add Legend
        legend_html = f'''
        <div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: 300px; background-color: white; z-index:9999; font-size:14px; border:2px solid grey; padding: 10px;">
        <b>Traffic Conditions (Background)</b><br>
        <i style="background:{config.TRAFFIC_LEVELS['heavy']['color']}; width:20px; height:20px; float:left; margin-right:10px;"></i>Heavy<br>
        <i style="background:{config.TRAFFIC_LEVELS['medium']['color']}; width:20px; height:20px; float:left; margin-right:10px;"></i>Medium<br>
        <i style="background:{config.TRAFFIC_LEVELS['light']['color']}; width:20px; height:20px; float:left; margin-right:10px;"></i>Light<br><hr style="clear:both;">
        <b>Routes</b><br>
        <i style="background:{route_colors[0]}; width:20px; height:20px; float:left; margin-right:10px; border-radius: 50%;"></i>{routes_data[0][0]} (Solid)<br>
        <i style="background:{route_colors[1]}; width:20px; height:20px; float:left; margin-right:10px; border-radius: 50%;"></i>{routes_data[1][0]} (Dashed)<br>
        <i style="background:{route_colors[2]}; width:20px; height:20px; float:left; margin-right:10px; border-radius: 50%;"></i>{routes_data[2][0]} (Dotted)<br>
        <i style="background:{route_colors[3]}; width:20px; height:20px; float:left; margin-right:10px; border-radius: 50%;"></i>{routes_data[3][0]} (Long Dash)<br>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        return m._repr_html_()
    except Exception as e:
        logger.error(f"Error in visualize_traffic_clean: {e}")
        return "<p class='error'>Error generating map. Please check your inputs and try again.</p>"
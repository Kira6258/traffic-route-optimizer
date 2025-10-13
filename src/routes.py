import networkx as nx
import heapq
from collections import defaultdict
import logging 
from . import utils

# Initialize the logger for this module
logger = logging.getLogger(__name__) 

# --- A* Pathfinding Logic ---

def find_balanced_route(G, origin_node, destination_node, time_weight=0.5, traffic_weight=0.3, distance_weight=0.2, used_edges=None):
    """
    Finds a balanced route using a custom A* search, minimizing a weighted cost function:
    Cost = (W_time * travel_time) + (W_traffic * traffic_score) + (W_dist * distance)
    """
    try:
        used_edges = used_edges or set()
        if origin_node not in G.nodes or destination_node not in G.nodes: return [], 0, 0, 0, set()
        
        dest_lat, dest_lon = G.nodes[destination_node]['y'], G.nodes[destination_node]['x']
        max_speed_kmh = 120 

        def heuristic(node):
            node_lat, node_lon = G.nodes[node]['y'], G.nodes[node]['x']
            dist_m = utils.haversine(node_lat, node_lon, dest_lat, dest_lon)
            
            min_time = dist_m / (max_speed_kmh / 3.6)
            min_distance_cost = dist_m / 1000 
            min_traffic_cost = dist_m / 1000 * 1 
            
            return (time_weight * min_time + distance_weight * min_distance_cost + traffic_weight * min_traffic_cost)

        g_cost, predecessors = defaultdict(lambda: float('inf')), {}
        g_cost[origin_node] = 0
        open_set = [(heuristic(origin_node), origin_node)]
        visited = set()

        while open_set:
            current_f, current_node = heapq.heappop(open_set)
            
            if current_node == destination_node: break
            if current_node in visited: continue
            visited.add(current_node)

            for neighbor, edges in G[current_node].items():
                for key, edge_data in edges.items():
                    edge = (current_node, neighbor, key)
                    penalty = 1000000 if edge in used_edges else 0 
                    
                    time_cost = edge_data.get('travel_time', float('inf'))
                    traffic_score = edge_data.get('traffic_weight_score', 1)
                    distance_m = edge_data.get('distance', float('inf'))
                    
                    traffic_cost = traffic_score * distance_m / 1000 
                    distance_cost = distance_m / 1000 

                    combined_cost = (time_weight * time_cost + 
                                     traffic_weight * traffic_cost + 
                                     distance_weight * distance_cost + 
                                     penalty)
                                     
                    tentative_g_cost = g_cost[current_node] + combined_cost

                    if tentative_g_cost < g_cost[neighbor]:
                        predecessors[neighbor] = (current_node, key)
                        g_cost[neighbor] = tentative_g_cost
                        heapq.heappush(open_set, (tentative_g_cost + heuristic(neighbor), neighbor))

        path, path_edges = [], set()
        current = destination_node
        while current != origin_node and current in predecessors:
            next_node, edge_key = predecessors[current]
            path.append(current)
            path_edges.add((next_node, current, edge_key))
            current = next_node
        if current == origin_node: path.append(origin_node)
        path.reverse()
        
        if not path or path[0] != origin_node: return [], 0, 0, 0, set()

        total_time, total_distance, total_traffic_score = 0, 0, 0
        for u, v, key in path_edges:
            edge_data = G[u][v][key]
            total_time += edge_data.get('travel_time', 0)
            total_distance += edge_data.get('distance', 0)
            total_traffic_score += edge_data.get('traffic_weight_score', 1)

        # Returns 5 items: (path, time_s, distance_m, traffic_score, edges_set)
        return path, total_time, total_distance, total_traffic_score, path_edges
    except Exception as e:
        logger.error(f"Error in find_balanced_route: {e}")
        return [], 0, 0, 0, set()

# --- Dijkstra Pathfinding Logic ---

def find_shortest_path_by_metric(G, origin_node, destination_node, weight_metric='travel_time'):
    """Finds the shortest path using a simple Dijkstra (fastest or shortest distance)."""
    try:
        if origin_node not in G.nodes or destination_node not in G.nodes: return [], 0, 0, 0, set()
        
        path = nx.shortest_path(G, origin_node, destination_node, weight=weight_metric)
        
        path_edges, total_time, total_distance, total_traffic_score = set(), 0, 0, 0
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            min_weight, best_key, best_data = float('inf'), None, None
            
            for key, data in G[u][v].items():
                if data.get(weight_metric, float('inf')) < min_weight:
                    min_weight = data[weight_metric]
                    best_key = key
                    best_data = data
            
            if best_data:
                path_edges.add((u, v, best_key))
                total_time += best_data.get('travel_time', 0)
                total_distance += best_data.get('distance', 0)
                total_traffic_score += best_data.get('traffic_weight_score', 1)

        # Returns 5 items: (path, time_s, distance_m, traffic_score, edges_set)
        return path, total_time, total_distance, total_traffic_score, path_edges
    except nx.NetworkXNoPath:
        logger.error(f"No path found for {weight_metric} route.")
        return [], 0, 0, 0, set()
    except Exception as e:
        logger.error(f"Error in find_shortest_path_by_metric: {e}")
        return [], 0, 0, 0, set()

# --- Main Routing Function (Corrected) ---

def find_all_route_options(G, origin_node, destination_node):
    if not nx.has_path(G, origin_node, destination_node): return []
    
    routes = []
    used_edges = set() 

    # 1. Balanced Route
    route_balanced = find_balanced_route(G, origin_node, destination_node, time_weight=0.5, traffic_weight=0.3, distance_weight=0.2, used_edges=used_edges)
    if route_balanced[0]: 
        routes.append(("Balanced",) + route_balanced) # Creates 6-item tuple
        used_edges.update(route_balanced[4])
    
    # 2. Time-Optimized Route (A* with high time priority)
    route_time_opt = find_balanced_route(G, origin_node, destination_node, time_weight=0.8, traffic_weight=0.1, distance_weight=0.1, used_edges=used_edges)
    if route_time_opt[0]: 
        routes.append(("Time-Optimized",) + route_time_opt) # Creates 6-item tuple
        used_edges.update(route_time_opt[4])

    # 3. Traffic-Avoiding Route (A* with high traffic priority)
    route_traffic_avoid = find_balanced_route(G, origin_node, destination_node, time_weight=0.2, traffic_weight=0.7, distance_weight=0.1, used_edges=used_edges)
    if route_traffic_avoid[0]: 
        routes.append(("Traffic-Avoiding",) + route_traffic_avoid) # Creates 6-item tuple
        used_edges.update(route_traffic_avoid[4])
        
    # 4. Distance-Optimized Route (Dijkstra by distance)
    route_distance_opt = find_shortest_path_by_metric(G, origin_node, destination_node, weight_metric='distance')
    if route_distance_opt[0]: 
        routes.append(("Distance-Optimized",) + route_distance_opt) # Creates 6-item tuple
        
    return routes
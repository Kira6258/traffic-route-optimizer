
import pickle
import os
import logging
import hashlib
from . import config

logger = logging.getLogger(__name__)

class SmartMapCache:
    def __init__(self):
        self.cache_dir = "map_cache"
        self.max_cities = 5  
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_city_hash(self, place_name):
        """Generate unique hash for each city"""
        return hashlib.md5(place_name.lower().encode()).hexdigest()[:10]
    
    def get_city_map(self, place_name):
        """Get cached map or download if new city"""
        city_hash = self.get_city_hash(place_name)
        cache_file = os.path.join(self.cache_dir, f"{city_hash}.pkl")
        
        # Try to load from cache
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    G = pickle.load(f)
                logger.info(f"Loaded cached map for {place_name}")
                return G
            except Exception as e:
                logger.error(f"Error loading cached map: {e}")
        
        # Download new city map
        G = self.download_city_map(place_name)
        if G:
            self.save_city_map(cache_file, G)
            self.cleanup_old_caches()
        return G
    
    def download_city_map(self, place_name):
        """Download map for a new city"""
        import osmnx as ox
        
        try:
            logger.info(f"Downloading map for {place_name}")
            
            # Use smaller area for new cities to save memory
            G = ox.graph_from_place(
                place_name, 
                network_type='drive', 
                simplify=True,
                which_result=1  
            )
            
            # Initialize edge data
            for u, v, key, data in G.edges(keys=True, data=True):
                data['base_speed'] = self.get_base_speed(data)
                data['distance'] = data.get('length', float('inf'))
                data['travel_time'] = data['distance'] / (data['base_speed'] / 3.6) if data['base_speed'] > 0 else float('inf')
            
            logger.info(f"Downloaded {place_name}: {len(G.nodes)} nodes")
            return G
            
        except Exception as e:
            logger.error(f"Error downloading map for {place_name}: {e}")
            return None
    
    def save_city_map(self, cache_file, G):
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(G, f)
            logger.info(f"Map saved to cache: {cache_file}")
        except Exception as e:
            logger.error(f"Error saving map cache: {e}")
    
    def cleanup_old_caches(self):
        
        try:
            cache_files = []
            for f in os.listdir(self.cache_dir):
                if f.endswith('.pkl'):
                    filepath = os.path.join(self.cache_dir, f)
                    cache_files.append((filepath, os.path.getmtime(filepath)))
            
            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda x: x[1])
            
            # Remove oldest files if we have too many
            while len(cache_files) > self.max_cities:
                oldest_file = cache_files.pop(0)[0]
                os.remove(oldest_file)
                logger.info(f"Removed old cache: {oldest_file}")
                
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")
    
    def get_base_speed(self, data):
        
        try:
            highway_type = data.get('highway', 'residential')
            if isinstance(highway_type, list): 
                highway_type = highway_type[0]
            
            speed_dict = {
                'motorway': 120, 'trunk': 90, 'primary': 80, 'secondary': 60,
                'tertiary': 50, 'residential': 40, 'service': 30, 'unclassified': 40,
                'living_street': 20
            }
            return speed_dict.get(highway_type, 40)
        except:
            return 40

# Global instance
map_cache = SmartMapCache()
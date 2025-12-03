"""
Optimized routing service with map caching and efficient flood avoidance.
"""
import osmnx as ox
import networkx as nx
from pathlib import Path
from typing import List, Dict, Optional
from .logger import logger
from . import config

# Global graph cache
_graph = None

def get_cached_graph_path() -> Path:
    """Get the path to the cached graph file."""
    return config.MAP_CACHE_DIR / f"{config.CITY_NAME.replace(' ', '_').replace(',', '')}.graphml"

def load_or_download_graph():
    """
    Load graph from cache or download if not exists.
    
    Returns:
        NetworkX MultiDiGraph
    """
    global _graph
    
    if _graph is not None:
        return _graph
    
    cache_file = get_cached_graph_path()
    
    if cache_file.exists():
        logger.info(f"Loading cached graph from {cache_file}")
        try:
            _graph = ox.load_graphml(cache_file)
            logger.info(f"Successfully loaded cached graph with {len(_graph.nodes)} nodes")
            return _graph
        except Exception as e:
            logger.warning(f"Failed to load cached graph: {e}. Downloading fresh copy.")
    
    # Download graph
    logger.info(f"Downloading graph for {config.CITY_NAME}...")
    try:
        _graph = ox.graph_from_place(config.CITY_NAME, network_type='drive')
        logger.info(f"Downloaded graph with {len(_graph.nodes)} nodes, {len(_graph.edges)} edges")
        
        # Save to cache
        logger.info(f"Saving graph to {cache_file}")
        ox.save_graphml(_graph, cache_file)
        logger.info("Graph cached successfully")
        
    except Exception as e:
        logger.error(f"Failed to download graph: {e}")
        raise
    
    return _graph

def get_safe_route(start_coords: Dict, end_coords: Dict, flooded_coords: List[Dict], 
                   buffer_radius: float = 50) -> List[Dict]:
    """
    Calculate a safe route avoiding flooded areas using edge weight modification.
    
    Args:
        start_coords: {"lat": float, "lng": float}
        end_coords: {"lat": float, "lng": float}
        flooded_coords: List of {"lat": float, "lng": float}
        buffer_radius: Radius in meters around flood points (not used in current implementation)
        
    Returns:
        List of {"lat": float, "lng": float} representing the path
    """
    try:
        graph = load_or_download_graph()
        
        # Find nearest nodes
        logger.debug(f"Finding route from {start_coords} to {end_coords}")
        orig_node = ox.distance.nearest_nodes(graph, start_coords['lng'], start_coords['lat'])
        dest_node = ox.distance.nearest_nodes(graph, end_coords['lng'], end_coords['lat'])
        
        if not flooded_coords:
            # No flooding, use normal shortest path
            logger.info("No flooded areas, calculating normal shortest path")
            path_nodes = nx.shortest_path(graph, orig_node, dest_node, weight='length')
        else:
            # Mark flooded edges with infinite weight
            logger.info(f"Avoiding {len(flooded_coords)} flooded areas")
            flooded_nodes = set()
            for flood in flooded_coords:
                flood_node = ox.distance.nearest_nodes(graph, flood['lng'], flood['lat'])
                flooded_nodes.add(flood_node)
            
            # Create a custom weight function
            def edge_weight(u, v, edge_data):
                # If either endpoint is flooded, make edge very expensive
                if u in flooded_nodes or v in flooded_nodes:
                    return float('inf')
                return edge_data.get('length', 1)
            
            # Calculate path with custom weights
            try:
                path_nodes = nx.shortest_path(graph, orig_node, dest_node, weight=edge_weight)
            except nx.NetworkXNoPath:
                logger.warning("No path found avoiding flooded areas, trying without flood avoidance")
                # Fallback to normal path if no safe route exists
                path_nodes = nx.shortest_path(graph, orig_node, dest_node, weight='length')
        
        # Convert path nodes to coordinates
        path_coords = []
        for node_id in path_nodes:
            node = graph.nodes[node_id]
            path_coords.append({"lat": node['y'], "lng": node['x']})
        
        logger.info(f"Route calculated with {len(path_coords)} waypoints")
        return path_coords
        
    except nx.NetworkXNoPath:
        logger.error("No path found between start and end points")
        return []
    except Exception as e:
        logger.error(f"Routing error: {e}", exc_info=True)
        return []

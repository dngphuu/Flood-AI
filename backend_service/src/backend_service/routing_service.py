import osmnx as ox
import networkx as nx
from shapely.geometry import Point

# Global graph cache
G = None

def get_graph(place_name="Hanoi, Vietnam"):
    """
    Load or download the street network graph.
    """
    global G
    if G is None:
        # Download drive network
        # In production, this should be cached to disk or loaded from a file
        print(f"Downloading graph for {place_name}...")
        G = ox.graph_from_place(place_name, network_type='drive')
        # Project graph to UTM for accurate distance calculations if needed
        # G = ox.project_graph(G) 
    return G

def get_safe_route(start_coords, end_coords, flooded_coords, buffer_radius=50):
    """
    Calculate a safe route avoiding flooded areas.
    
    Args:
        start_coords (dict): {"lat": float, "lng": float}
        end_coords (dict): {"lat": float, "lng": float}
        flooded_coords (list): List of {"lat": float, "lng": float}
        buffer_radius (float): Radius in meters to consider around a flooded point (approx).
                               Note: Without projecting, we use rough degree approximation or nearest node logic.
    
    Returns:
        list: List of {"lat": float, "lng": float} representing the path.
    """
    graph = get_graph()
    
    # Find nearest nodes
    orig_node = ox.distance.nearest_nodes(graph, start_coords['lng'], start_coords['lat'])
    dest_node = ox.distance.nearest_nodes(graph, end_coords['lng'], end_coords['lat'])
    
    # Create a copy of the graph to modify weights/remove nodes
    # For efficiency, we might just increase weight of flooded edges instead of removing
    # But removing is safer to guarantee avoidance
    H = graph.copy()
    
    nodes_to_remove = set()
    
    # Identify nodes to remove based on flooded_coords
    # This is a naive implementation. For better performance, use spatial index.
    for flood in flooded_coords:
        # Find nearest node to the flood point
        flood_node = ox.distance.nearest_nodes(graph, flood['lng'], flood['lat'])
        nodes_to_remove.add(flood_node)
        
        # Optionally find all nodes within a radius
        # For now, we just remove the nearest node to the flood point
    
    # Remove flooded nodes
    H.remove_nodes_from(nodes_to_remove)
    
    try:
        # Calculate shortest path
        path_nodes = nx.shortest_path(H, orig_node, dest_node, weight='length')
        
        # Convert path nodes to coordinates
        path_coords = []
        for node_id in path_nodes:
            node = graph.nodes[node_id]
            path_coords.append({"lat": node['y'], "lng": node['x']})
            
        return path_coords
        
    except nx.NetworkXNoPath:
        print("No path found!")
        return []
    except Exception as e:
        print(f"Routing error: {e}")
        return []

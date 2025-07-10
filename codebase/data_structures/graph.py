from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict, deque
import heapq
from dataclasses import dataclass, field
from enum import Enum


class GraphType(Enum):
    DIRECTED = "directed"
    UNDIRECTED = "undirected"


@dataclass
class Edge:
    """Represents an edge in the graph"""
    source: Any
    destination: Any
    weight: float = 1.0
    
    def __repr__(self) -> str:
        return f"Edge({self.source} -> {self.destination}, weight={self.weight})"


@dataclass
class Vertex:
    """Represents a vertex in the graph"""
    value: Any
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Vertex({self.value})"
    
    def __hash__(self) -> int:
        return hash(self.value)
    
    def __eq__(self, other) -> bool:
        return isinstance(other, Vertex) and self.value == other.value


class Graph:
    """Graph implementation supporting both directed and undirected graphs"""
    
    def __init__(self, graph_type: GraphType = GraphType.UNDIRECTED):
        self.graph_type = graph_type
        self.vertices: Dict[Any, Vertex] = {}
        self.adjacency_list: Dict[Any, List[Edge]] = defaultdict(list)
        self._edge_count = 0
    
    def add_vertex(self, value: Any, data: Dict[str, Any] = None) -> Vertex:
        """Add a vertex to the graph"""
        if value not in self.vertices:
            vertex = Vertex(value, data or {})
            self.vertices[value] = vertex
            self.adjacency_list[value] = []
            return vertex
        return self.vertices[value]
    
    def add_edge(self, source: Any, destination: Any, weight: float = 1.0) -> Edge:
        """Add an edge between two vertices"""
        # Ensure vertices exist
        self.add_vertex(source)
        self.add_vertex(destination)
        
        edge = Edge(source, destination, weight)
        self.adjacency_list[source].append(edge)
        
        # For undirected graphs, add the reverse edge
        if self.graph_type == GraphType.UNDIRECTED:
            reverse_edge = Edge(destination, source, weight)
            self.adjacency_list[destination].append(reverse_edge)
        
        self._edge_count += 1
        return edge
    
    def remove_vertex(self, value: Any) -> bool:
        """Remove a vertex and all its edges"""
        if value not in self.vertices:
            return False
        
        # Remove all edges pointing to this vertex
        for vertex_value in list(self.adjacency_list.keys()):
            self.adjacency_list[vertex_value] = [
                edge for edge in self.adjacency_list[vertex_value] 
                if edge.destination != value
            ]
        
        # Remove vertex and its adjacency list
        del self.vertices[value]
        del self.adjacency_list[value]
        
        return True
    
    def remove_edge(self, source: Any, destination: Any) -> bool:
        """Remove an edge between two vertices"""
        if source not in self.adjacency_list:
            return False
        
        initial_length = len(self.adjacency_list[source])
        self.adjacency_list[source] = [
            edge for edge in self.adjacency_list[source] 
            if edge.destination != destination
        ]
        
        # For undirected graphs, remove the reverse edge
        if self.graph_type == GraphType.UNDIRECTED and destination in self.adjacency_list:
            self.adjacency_list[destination] = [
                edge for edge in self.adjacency_list[destination] 
                if edge.destination != source
            ]
        
        return len(self.adjacency_list[source]) < initial_length
    
    def get_neighbors(self, vertex: Any) -> List[Any]:
        """Get all neighbors of a vertex"""
        if vertex not in self.adjacency_list:
            return []
        return [edge.destination for edge in self.adjacency_list[vertex]]
    
    def get_edges(self, vertex: Any) -> List[Edge]:
        """Get all edges from a vertex"""
        return self.adjacency_list.get(vertex, [])
    
    def has_edge(self, source: Any, destination: Any) -> bool:
        """Check if an edge exists between two vertices"""
        if source not in self.adjacency_list:
            return False
        return any(edge.destination == destination for edge in self.adjacency_list[source])
    
    def get_edge_weight(self, source: Any, destination: Any) -> Optional[float]:
        """Get the weight of an edge"""
        if source not in self.adjacency_list:
            return None
        
        for edge in self.adjacency_list[source]:
            if edge.destination == destination:
                return edge.weight
        return None
    
    def vertex_count(self) -> int:
        """Get number of vertices"""
        return len(self.vertices)
    
    def edge_count(self) -> int:
        """Get number of edges"""
        return self._edge_count
    
    def is_empty(self) -> bool:
        """Check if graph is empty"""
        return len(self.vertices) == 0
    
    # Graph traversal algorithms
    def breadth_first_search(self, start: Any) -> List[Any]:
        """BFS traversal starting from given vertex"""
        if start not in self.vertices:
            return []
        
        visited = set()
        queue = deque([start])
        result = []
        
        while queue:
            vertex = queue.popleft()
            
            if vertex not in visited:
                visited.add(vertex)
                result.append(vertex)
                
                # Add unvisited neighbors to queue
                for neighbor in self.get_neighbors(vertex):
                    if neighbor not in visited:
                        queue.append(neighbor)
        
        return result
    
    def depth_first_search(self, start: Any) -> List[Any]:
        """DFS traversal starting from given vertex"""
        if start not in self.vertices:
            return []
        
        visited = set()
        result = []
        
        def dfs_recursive(vertex):
            visited.add(vertex)
            result.append(vertex)
            
            for neighbor in self.get_neighbors(vertex):
                if neighbor not in visited:
                    dfs_recursive(neighbor)
        
        dfs_recursive(start)
        return result
    
    def find_path(self, start: Any, end: Any) -> Optional[List[Any]]:
        """Find a path between two vertices using BFS"""
        if start not in self.vertices or end not in self.vertices:
            return None
        
        if start == end:
            return [start]
        
        visited = set()
        queue = deque([(start, [start])])
        
        while queue:
            vertex, path = queue.popleft()
            
            if vertex in visited:
                continue
            
            visited.add(vertex)
            
            for neighbor in self.get_neighbors(vertex):
                if neighbor not in visited:
                    new_path = path + [neighbor]
                    
                    if neighbor == end:
                        return new_path
                    
                    queue.append((neighbor, new_path))
        
        return None
    
    def is_connected(self) -> bool:
        """Check if graph is connected (for undirected) or strongly connected (for directed)"""
        if self.is_empty():
            return True
        
        if self.graph_type == GraphType.UNDIRECTED:
            # For undirected graph, check if all vertices are reachable from any vertex
            start_vertex = next(iter(self.vertices))
            reachable = set(self.breadth_first_search(start_vertex))
            return len(reachable) == len(self.vertices)
        else:
            # For directed graph, check strong connectivity (simplified)
            # This is a basic implementation; more sophisticated algorithms exist
            for vertex in self.vertices:
                reachable = set(self.breadth_first_search(vertex))
                if len(reachable) != len(self.vertices):
                    return False
            return True
    
    def has_cycle(self) -> bool:
        """Detect if graph has a cycle"""
        if self.graph_type == GraphType.UNDIRECTED:
            return self._has_cycle_undirected()
        else:
            return self._has_cycle_directed()
    
    def _has_cycle_undirected(self) -> bool:
        """Detect cycle in undirected graph using DFS"""
        visited = set()
        
        def dfs(vertex, parent):
            visited.add(vertex)
            
            for neighbor in self.get_neighbors(vertex):
                if neighbor not in visited:
                    if dfs(neighbor, vertex):
                        return True
                elif neighbor != parent:
                    return True
            
            return False
        
        for vertex in self.vertices:
            if vertex not in visited:
                if dfs(vertex, None):
                    return True
        
        return False
    
    def _has_cycle_directed(self) -> bool:
        """Detect cycle in directed graph using DFS"""
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {vertex: WHITE for vertex in self.vertices}
        
        def dfs(vertex):
            colors[vertex] = GRAY
            
            for neighbor in self.get_neighbors(vertex):
                if colors[neighbor] == GRAY:  # Back edge found
                    return True
                elif colors[neighbor] == WHITE and dfs(neighbor):
                    return True
            
            colors[vertex] = BLACK
            return False
        
        for vertex in self.vertices:
            if colors[vertex] == WHITE:
                if dfs(vertex):
                    return True
        
        return False
    
    def topological_sort(self) -> Optional[List[Any]]:
        """Topological sort for directed acyclic graph"""
        if self.graph_type == GraphType.UNDIRECTED:
            return None
        
        if self.has_cycle():
            return None  # Cannot sort cyclic graph
        
        in_degree = {vertex: 0 for vertex in self.vertices}
        
        # Calculate in-degrees
        for vertex in self.vertices:
            for neighbor in self.get_neighbors(vertex):
                in_degree[neighbor] += 1
        
        # Start with vertices having no incoming edges
        queue = deque([vertex for vertex in self.vertices if in_degree[vertex] == 0])
        result = []
        
        while queue:
            vertex = queue.popleft()
            result.append(vertex)
            
            # Reduce in-degree of neighbors
            for neighbor in self.get_neighbors(vertex):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result if len(result) == len(self.vertices) else None
    
    def dijkstra(self, start: Any) -> Dict[Any, Tuple[float, Optional[Any]]]:
        """Dijkstra's algorithm for shortest paths"""
        if start not in self.vertices:
            return {}
        
        distances = {vertex: float('inf') for vertex in self.vertices}
        distances[start] = 0
        previous = {vertex: None for vertex in self.vertices}
        
        # Priority queue: (distance, vertex)
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_distance, current_vertex = heapq.heappop(pq)
            
            if current_vertex in visited:
                continue
            
            visited.add(current_vertex)
            
            for edge in self.get_edges(current_vertex):
                neighbor = edge.destination
                distance = current_distance + edge.weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_vertex
                    heapq.heappush(pq, (distance, neighbor))
        
        # Return distances and previous vertices for path reconstruction
        return {vertex: (distances[vertex], previous[vertex]) for vertex in self.vertices}
    
    def get_shortest_path(self, start: Any, end: Any) -> Tuple[Optional[List[Any]], float]:
        """Get shortest path and distance between two vertices"""
        dijkstra_result = self.dijkstra(start)
        
        if end not in dijkstra_result:
            return None, float('inf')
        
        distance, _ = dijkstra_result[end]
        
        if distance == float('inf'):
            return None, float('inf')
        
        # Reconstruct path
        path = []
        current = end
        
        while current is not None:
            path.append(current)
            _, current = dijkstra_result[current]
        
        path.reverse()
        return path, distance
    
    def __repr__(self) -> str:
        return f"Graph({self.graph_type.value}, vertices={len(self.vertices)}, edges={self.edge_count()})"
    
    def __str__(self) -> str:
        result = []
        for vertex in self.vertices:
            neighbors = self.get_neighbors(vertex)
            result.append(f"{vertex}: {neighbors}")
        return "\n".join(result) 
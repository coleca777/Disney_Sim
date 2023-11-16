import networkx as nx


# Creates the graph that will be used for guests to "navigate"
# Organization of the points don't matter, just that the edges are connected to the right location
class Map:
    def __init__(self, edges):

        self.graph = nx.Graph(directed=False)        

        for edge in edges:
            points = edge.split("/")
            self.graph.add_edge(points[0], points[1], weight = edges[edge]["distance"])
        
        self.shortest_paths = self.dijkstra_shortest_paths()

    def dijkstra_shortest_paths(self):
        all_shortest_paths = {}
        for node in self.graph.nodes:
            shortest_paths = (nx.single_source_dijkstra_path_length(self.graph, node), nx.single_source_dijkstra_path(self.graph, node))
            all_shortest_paths[node] = shortest_paths
        return all_shortest_paths
                
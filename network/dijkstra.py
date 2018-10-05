from collections import deque
import numpy as np


def dijkstra(source, dest, train):
    # 1. Mark all nodes unvisited and store them.
    # 2. Set the distance to zero for our initial node
    # and to infinity for other nodes.
    distances = {vertex.label: np.inf for vertex in train.network.nodes.values()}
    previous_vertices = {vertex.label: None for vertex in train.network.nodes.values()}
    distances[source] = 0
    vertices = train.network.nodes.copy()

    while vertices:
        # 3. Select the unvisited node with the smallest distance,
        # it's current node now.
        current_vertex = min(vertices, key=lambda vertex: distances[vertex])
        # 6. Stop, if the smallest distance
        # among the unvisited nodes is infinity.
        if distances[current_vertex] == np.inf:
            break

        # 4. Find unvisited neighbors for the current node
        # and calculate their distances through the current node.
        for edge in vertices[current_vertex].out_links:
            neighbour = edge.end_node
            cost = edge.get_minimum_running_time()
            r = edge.get_requirement()

            if r is not None:
                if r.get_min_stopping_time() is not None:
                    cost += r.get_min_stopping_time()

            alternative_route = distances[current_vertex] + cost

            # Compare the newly calculated distance to the assigned
            # and save the smaller one.
            if alternative_route < distances[neighbour.label]:
                distances[neighbour.label] = alternative_route
                previous_vertices[neighbour.label] = current_vertex

        # 5. Mark the current node as visited
        # and remove it from the unvisited set.
        del vertices[current_vertex]

    path, current_vertex = deque(), dest
    while previous_vertices[current_vertex] is not None:
        path.appendleft(current_vertex)
        current_vertex = previous_vertices[current_vertex]
    if path:
        path.appendleft(current_vertex)
    return distances

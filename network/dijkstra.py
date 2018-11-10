from collections import deque
import numpy as np


def dijkstra(source, train):
    # 1. Mark all nodes unvisited and store them.
    # 2. Set the distance to zero for our initial node
    # and to infinity for other nodes.
    distances = {vertex.label: -np.inf for vertex in train.network.nodes.values()}
    # previous_vertices = {vertex.label: None for vertex in train.network.nodes.values()}
    vertices = train.network.nodes.copy()
    r = vertices[source].in_links[0].get_requirement()
    distances[source] = r.get_exit_latest() - r.get_min_stopping_time()

    while vertices:
        # 3. Select the unvisited node with the smallest distance,
        # it's current node now.
        current_vertex = max(vertices, key=lambda vertex: distances[vertex])
        # 6. Stop, if the smallest distance
        # among the unvisited nodes is infinity.
        if distances[current_vertex] == -np.inf:
            break

        # 4. Find unvisited neighbors for the current node
        # and calculate their distances through the current node.
        for edge in vertices[current_vertex].in_links:
            neighbour = edge.start_node
            r = edge.get_requirement()

            entry_latest = distances[current_vertex] - edge.get_minimum_running_time()
            if r is not None:
                if r.get_min_stopping_time() is not None:
                    entry_latest = entry_latest - r.get_min_stopping_time()

                    latest = r.get_entry_latest()
                    if latest < 24 * 60 * 60 * 3:
                        entry_latest = max(r.get_entry_latest(), entry_latest)

            # Compare the newly calculated distance to the assigned
            # and save the smaller one.
            if entry_latest > distances[neighbour.label]:
                distances[neighbour.label] = entry_latest
                # previous_vertices[neighbour.label] = current_vertex

        # 5. Mark the current node as visited
        # and remove it from the unvisited set.
        del vertices[current_vertex]

    # path, current_vertex = deque(), dest
    # while previous_vertices[current_vertex] is not None:
    #    path.appendleft(current_vertex)
    #    current_vertex = previous_vertices[current_vertex]
    # if path:
    #    path.appendleft(current_vertex)
    return distances

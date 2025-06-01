import numpy as np
import random
import networkx as nx

class Tile:
    def __init__(self, resource, frequency):
        self.resource = resource
        self.frequency = frequency
    def get_resource(self):
        if self.resource != 'desert':
            return self.resource
        else:
            return None
class Node:
    def __init__(self, id, occupied_by, is_city, adjacent_tiles, neighbors):
        self.id = id
        self.occupied_by = occupied_by
        self.is_city = is_city
        self.adjacent_tiles = adjacent_tiles
        self.neighbors = neighbors

class Edge:
    def __init__(self, id, node_a, node_b, built_by):
        self.id = id
        self.node_a = node_a
        self.node_b = node_b 
        self.built_by = built_by

resource_distribution = {
    'wheat': 4,
    'sheep': 4,
    'ore': 3,
    'brick': 3,
    'wood': 4,
    'desert': 1
}


frequencies = [5, 2, 6, 3, 8, 10, 9, 12, 11, 4, 8, 10, 9, 4, 5, 6, 3, 11]
resources = []
for resource, count in resource_distribution.items():
    for _ in range(count):
        resources.append(resource)

random.shuffle(resources)
random.shuffle(frequencies)

tiles = []
for resource in resources:
    if resource == 'desert':
        frequency = None
    else:
        frequency = frequencies.pop()
    tiles.append(Tile(resource,frequency))

G = nx.Graph()
row_structure = [3,4,4,5,5,6,6,5,5,4,4,3]
node_id = 0
y_offset = 0

for row in row_structure:
    x_start = (max(row_structure)-row)*0.5
    for i in range(row):
        x = x_start+i
        y = -y_offset
        G.add_node(
            node_id,
            occupied_by = None,
            is_city = False,
            adjacent_tiles = [],
            coordinates = (x,y)
        )
        node_id += 1
    y_offset += 1

node_offset_top = 0
node_offset_bottom = 53
edge_id_top = 0
edge_id_bottom = 113

for index, row in enumerate(row_structure):
    for i in range (int(row/2)):
        if index % 2 == 1:
            node_a_top = i + node_offset_top
            node_a_bottom = node_offset_bottom - i
            edge_top = Edge(id=edge_id_top, node_a = node_a_top, node_b = node_a_top+row, built_by=None)
            edge_bottom = Edge(id=edge_id_bottom, node_a = node_a_bottom, node_b = node_a_bottom-row, built_by=None)

            G.add_edge(
                node_a_top,
                node_a_top + row,
                edge = edge_top
            )
            G.add_edge(
                node_a_bottom,
                node_a_bottom - row,
                edge = edge_bottom
            )

        else:
            node_a_top = i + node_offset_top
            node_a_bottom = node_offset_bottom - i
            edge_top = Edge(id=edge_id_top, node_a = node_a_top, node_b = node_a_top+row, built_by=None)

            G.add_edge(
                node_a_top,
                node_a_top + row, 
                edge = edge_top
            )
            edge_id_top += 1
            edge_top = Edge(id=edge_id_top, node_a = node_a_top, node_b = node_a_top+row, built_by=None)
            G.add_edge(
                node_a_top, 
                node_a_top + row + 1,
                edge = edge_top
            )
            edge_bottom = Edge(id=edge_id_bottom, node_a = node_a_bottom, node_b = node_a_bottom-row, built_by=None)
            G.add_edge(
                node_a_bottom,
                node_a_bottom - row, 
                edge = edge_bottom
            )
            edge_id_bottom -= 1
            edge_bottom = Edge(id=edge_id_bottom, node_a = node_a_bottom, node_b = node_a_bottom-row, built_by=None)
            G.add_edge(
                node_a_bottom,
                node_a_bottom - row-1, 
                edge = edge_bottom
            )

        edge_id_top += 1
        edge_id_bottom -= 1
    node_offset_top += row
    node_offset_bottom -= row

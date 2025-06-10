import numpy as np
import random
import networkx as nx
import matplotlib.pyplot as plt
import math
from player import Player

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
    tiles.append(Tile(resource, frequency))

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
            occupied_by=None,
            is_city=False,
            adjacent_tiles=[],
            coordinates=(x, y)
        )
        node_id += 1
    y_offset += 1

rows = []
node_counter = 0
for count in row_structure:
    row = list(range(node_counter, node_counter + count))
    rows.append(row)
    node_counter += count

edge_pairs = [
    (0,3),(0,4),(1,4),(1,5),(2,5),(2,6),(3,7),(4,8),(5,9),(6,10),
    (7,11),(7,12),(8,12),(8,13),(9,13),(9,14),(10,14),(10,15),
    (11,16),(12,17),(13,18),(14,19),(15,20),(16,21),(16,22),
    (17,22),(17,23),(18,23),(18,24),(19,24),(19,25),(20,25),
    (20,26),(21,27),(22,28),(23,29),(24,30),(25,31),(26,32),
    (27,33),(28,33),(28,34),(29,34),(29,35),(30,35),(30,36),
    (31,36),(31,37),(32,37),(33,38),(34,39),(35,40),(36,41),
    (37,42),(38,43),(39,43),(39,44),(40,44),(40,45),(41,45),
    (41,46),(42,46),(43,47),(44,48),(45,49),(46,50),(47,51),
    (48,51),(48,52),(49,52),(49,53),(50,53)
]

G.add_edges_from(edge_pairs)

import numpy as np

tile_axial_coords = [
    (0, -2), (1, -2), (2, -2),
    (-1, -1), (0, -1), (1, -1), (2, -1),
    (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
    (-2, 1), (-1, 1), (0, 1), (1, 1),
    (-2, 2), (-1, 2), (0, 2)
]

def ax_to_cart(q, r, size=1):
    x = size * np.sqrt(3) * (q + r / 2)
    y = size * 1.5 * r
    return (x, -y)

tile_positions = [ax_to_cart(q, r) for q, r in tile_axial_coords]
for i, tile in enumerate(tiles):
    tile.center = tile_positions[i]

for node_id in G.nodes:
    if 'adjacent_tiles' not in G.nodes[node_id]:
        G.nodes[node_id]['adjacent_tiles'] = []

for tile in tiles:
    distances = []
    for node_id, data in G.nodes(data=True):
        node_pos = np.array(data['coordinates'])
        dist = np.linalg.norm(np.array(tile.center) - node_pos)
        distances.append((dist, node_id))
    distances.sort()
    tile.corner_nodes = [node_id for _, node_id in distances[:6]]

    for node_id in tile.corner_nodes:
        G.nodes[node_id]['adjacent_tiles'].append(tile)

pos = nx.get_node_attributes(G, 'coordinates')
plt.figure(figsize=(8, 8))
nx.draw_networkx_nodes(G, pos, node_size=300, node_color='lightblue', edgecolors='black')
nx.draw_networkx_edges(G, pos)
nx.draw_networkx_labels(G, pos, font_size=10)
plt.title("Catan Board Visualization")
plt.axis('off')
plt.tight_layout()
plt.show()

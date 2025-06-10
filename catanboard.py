import numpy as np
import random
import networkx as nx
import math
from player import Player

class Tile:
    def __init__(self, resource, frequency, center, corner_nodes):
        self.resource = resource
        self.frequency = frequency
        self.center = center
        self.corner_nodes = corner_nodes
    def get_resource(self):
        return self.resource if self.resource != 'desert' else None
resource_colors = {
    'wheat': '#F9DC5C',
    'sheep': '#A1C349',
    'wood':  '#8FBC8F',
    'brick': '#D2691E',
    'ore':   '#A9A9A9',
    'desert': '#F0E68C'
}

def ax_to_cart(q, r, size=1):
    x = size * np.sqrt(3) * (q + r / 2)
    y = size * 1.5 * r
    return (x, -y)

tile_axial_coords = [
    (0, -2), (1, -2), (2, -2),
    (-1, -1), (0, -1), (1, -1), (2, -1),
    (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
    (-2, 1), (-1, 1), (0, 1), (1, 1),
    (-2, 2), (-1, 2), (0, 2)
]
tile_centers = [ax_to_cart(q, r) for q, r in tile_axial_coords]

G = nx.Graph()
node_coords = {}
coord_to_node = {}
edges = set()
tile_corner_nodes = []
node_id = 0

for center in tile_centers:
    cx, cy = center
    corners = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = cx + math.cos(angle)
        y = cy + math.sin(angle)
        coord = (round(x, 5), round(y, 5))

        if coord not in coord_to_node:
            coord_to_node[coord] = node_id
            node_coords[node_id] = coord
            G.add_node(node_id, coordinates=coord, occupied_by=None, is_city=False, adjacent_tiles=[])
            node_id += 1

        corners.append(coord_to_node[coord])

    for i in range(6):
        a = corners[i]
        b = corners[(i + 1) % 6]
        edge = tuple(sorted((a, b)))
        edges.add(edge)

    tile_corner_nodes.append(corners)

G.add_edges_from(edges)

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
    resources.extend([resource] * count)

random.shuffle(resources)
random.shuffle(frequencies)

tiles = []
for i, center in enumerate(tile_centers):
    resource = resources[i]
    frequency = None if resource == 'desert' else frequencies.pop()
    tile = Tile(resource, frequency, center, tile_corner_nodes[i])
    tiles.append(tile)

for tile in tiles:
    for node_id in tile.corner_nodes:
        G.nodes[node_id]['adjacent_tiles'].append(tile)

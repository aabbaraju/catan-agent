import numpy as np
import random

class Tile:
    def __init__(self, resource, frequency):
        self.resource = resource
        self.frequency = frequency
    def get_resource(self):
        if self.resource != 'desert':
            return self.resource
        else:
            return None
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
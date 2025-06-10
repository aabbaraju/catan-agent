import os
import math
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

class CatanBoardVisualizer:
    def __init__(self, graph, tiles, resource_dir="resources"):
        self.G = graph
        self.tiles = tiles
        self.resource_dir = resource_dir

        self.resource_colors = {
            'wheat': '#F9DC5C',
            'sheep': '#A1C349',
            'wood': '#8FBC8F',
            'brick': '#D2691E',
            'ore': '#A9A9A9',
            'desert': '#F0E68C'
        }

        self.resource_images = {}
        for resource in self.resource_colors:
            img_path = os.path.join(self.resource_dir, f"{resource}.png")
            if os.path.exists(img_path):
                self.resource_images[resource] = mpimg.imread(img_path)

    def draw_hex(self, center, size=1, color='white', edgecolor='black', ax=None):
        if ax is None:
            ax = plt.gca()
        hexagon = plt.Polygon([
            (center[0] + size * math.cos(math.radians(60 * i)),
             center[1] + size * math.sin(math.radians(60 * i)))
            for i in range(6)
        ], closed=True, facecolor=color, edgecolor=edgecolor, linewidth=2, zorder=0)
        ax.add_patch(hexagon)

    def draw_tile_image(self, ax, tile, zoom=0.2):
        resource = tile.resource
        if resource in self.resource_images:
            image = self.resource_images[resource]
            x, y = tile.center
            extent = [x - zoom, x + zoom, y - zoom, y + zoom]
            ax.imshow(image, extent=extent, zorder=1)

    def draw(self):
        fig, ax = plt.subplots(figsize=(10, 10))

        for tile in self.tiles:
            color = self.resource_colors.get(tile.resource, 'white')
            self.draw_hex(tile.center, size=1, color=color, ax=ax)
            self.draw_tile_image(ax, tile, zoom=0.9)
            if tile.frequency:
                ax.text(tile.center[0], tile.center[1], str(tile.frequency),
                        ha='center', va='center', fontsize=12, fontweight='bold', zorder=2)

        for (u, v) in self.G.edges():
            x1, y1 = self.G.nodes[u]['coordinates']
            x2, y2 = self.G.nodes[v]['coordinates']
            ax.plot([x1, x2], [y1, y2], color='gray', zorder=3)

        for node_id, data in self.G.nodes(data=True):
            x, y = data['coordinates']
            ax.plot(x, y, 'o', markersize=6, color='lightblue', markeredgecolor='black', zorder=4)
            ax.text(x, y + 0.15, str(node_id), ha='center', va='center', fontsize=8, zorder=5)

        ax.set_aspect('equal')
        plt.axis('off')
        plt.title("Enhanced Catan Board with Resources", fontsize=16)
        plt.tight_layout()
        plt.show()

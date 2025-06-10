import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
import math

resource_colors = {
    'wheat': '#F9DC5C',
    'sheep': '#A1C349',
    'wood':  '#8FBC8F',
    'brick': '#D2691E',
    'ore':   '#A9A9A9',
    'desert': '#F0E68C'
}

def draw_hex(ax, center, size=1, edgecolor='black', facecolor='none', linewidth=1.5):
    cx, cy = center
    hex_coords = [
        (cx + size * math.cos(math.radians(60 * i - 30)),
         cy + size * math.sin(math.radians(60 * i - 30)))
        for i in range(6)
    ]
    hexagon = plt.Polygon(hex_coords, closed=True,
                          edgecolor=edgecolor,
                          facecolor=facecolor,
                          linewidth=linewidth,
                          zorder=1)
    ax.add_patch(hexagon)

def draw_settlement(ax, x, y, color):
    house_width = 0.2
    house_height = 0.25

    square = patches.Rectangle((x - house_width/2, y - house_height/2),
                               house_width, house_height * 0.6,
                               facecolor=color, edgecolor='black', zorder=10)

    triangle = patches.Polygon([
        (x - house_width/2, y - house_height/2 + house_height * 0.6),
        (x + house_width/2, y - house_height/2 + house_height * 0.6),
        (x, y + house_height/2)
    ], closed=True, facecolor=color, edgecolor='black', zorder=10)

    ax.add_patch(square)
    ax.add_patch(triangle)

def render_board(G, tiles, on_node_click=None, game=None, fig=None, ax=None, redraw_only=False):
    if not fig or not ax:
        fig, ax = plt.subplots(figsize=(10, 10))
    else:
        ax.clear()

    pos = nx.get_node_attributes(G, 'coordinates')

    nx.draw(G, pos, ax=ax,
            node_color='lightblue',
            edge_color='gray',
            node_size=300,
            with_labels=True,
            font_size=8)

    for tile in tiles:
        if tile.center:
            draw_hex(ax, tile.center, size=1,
                     facecolor=resource_colors.get(tile.resource, 'white'))

            label = tile.resource
            if tile.frequency:
                label += f" ({tile.frequency})"

            ax.text(tile.center[0], tile.center[1],
                    label,
                    ha='center', va='center',
                    fontsize=9, fontweight='bold',
                    bbox=dict(facecolor='white', alpha=0.6, boxstyle='round,pad=0.2'),
                    zorder=2)

    if game:
        for player in game.players:
            for node_id in player.settlements:
                x, y = G.nodes[node_id]['coordinates']
                draw_settlement(ax, x, y, player.name.lower())
                ax.text(x, y + 0.2, f"{player.name}", color='black', fontsize=9, ha='center', zorder=11)

    if not redraw_only:
        def on_click(event):
            if event.inaxes != ax:
                return
            click_x, click_y = event.xdata, event.ydata
            threshold = 0.2
            closest_node = None
            min_dist = float('inf')

            for node_id, (x, y) in pos.items():
                dist = ((x - click_x)**2 + (y - click_y)**2)**0.5
                if dist < threshold and dist < min_dist:
                    closest_node = node_id
                    min_dist = dist

            if closest_node is not None and on_node_click:
                on_node_click(closest_node, fig, ax)

        fig.canvas.mpl_connect('button_press_event', on_click)
        plt.title("Catan Board")
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    else:
        fig.canvas.draw()

    if game:
        for player in game.players:
            for node_id in player.settlements:
                x, y = G.nodes[node_id]['coordinates']
                ax.plot(x, y, marker='o', markersize=15, color=player.name.lower(), zorder=10)
                ax.text(x, y + 0.2, f"{player.name}", color='black', fontsize=9, ha='center', zorder=11)

    plt.title("Catan Board")
    plt.axis('off')
    plt.tight_layout()
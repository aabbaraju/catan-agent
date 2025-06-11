import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
import math
import matplotlib.widgets as widgets

resource_colors = {
    'wheat': '#F9DC5C',
    'sheep': '#A1C349',
    'wood':  '#8FBC8F',
    'brick': '#D2691E',
    'ore':   '#A9A9A9',
    'desert': '#F0E68C'
}

sidebar_texts = []

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

def draw_city(ax, x, y, color):
    base_width = 0.25
    base_height = 0.2
    tower_width = 0.15
    tower_height = 0.25

    base = patches.Rectangle(
        (x - base_width/2, y - base_height/2),
        base_width, base_height,
        facecolor=color, edgecolor='black', zorder=10
    )

    tower = patches.Rectangle(
        (x - tower_width/2, y),
        tower_width, tower_height,
        facecolor=color, edgecolor='black', zorder=11
    )

    ax.add_patch(base)
    ax.add_patch(tower)

def draw_robber(ax, x, y):
    scale = 0.25 

    base = patches.Circle((x, y - scale * 1.1), radius=scale * 0.5, facecolor='red', edgecolor='black', zorder=20)
    ax.add_patch(base)

    body = patches.Ellipse((x, y - scale * 0.2), width=scale * 1.2, height=scale * 2.0,
                           facecolor='black', edgecolor='black', zorder=21)
    ax.add_patch(body)

    head = patches.Circle((x, y + scale * 0.8), radius=scale * 0.5, facecolor='black', edgecolor='black', zorder=22)
    ax.add_patch(head)

def render_board(G, tiles, on_node_click=None, game=None, fig=None, ax=None, redraw_only=False):
    global sidebar_texts
    for txt in sidebar_texts:
        txt.remove()
    sidebar_texts.clear()

    if not fig or not ax:
        fig, ax = plt.subplots(figsize=(11, 10))
        plt.subplots_adjust(right=3)
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
            if tile.has_robber:
                draw_robber(ax, tile.center[0], tile.center[1])

    if game:
        for player in game.players:
            for node_id in player.settlements:
                x, y = G.nodes[node_id]['coordinates']
                draw_settlement(ax, x, y, player.name.lower())
                ax.text(x, y + 0.2, f"{player.name}", color='black', fontsize=9, ha='center', zorder=11)

            for node_id in player.cities:
                x, y = G.nodes[node_id]['coordinates']
                draw_city(ax, x, y, player.name.lower())
                ax.text(x, y + 0.35, 'City', color='black', fontsize=8, ha='center', zorder=12)

            for node1, node2 in player.roads:
                x1, y1 = G.nodes[node1]['coordinates']
                x2, y2 = G.nodes[node2]['coordinates']
                ax.plot([x1, x2], [y1, y2], color=player.name.lower(), linewidth=3, zorder=5)
        info_x = 0.77
        info_y_start = 0.96
        y_step = 0.06

        sidebar_texts.append(
            fig.text(info_x, info_y_start, f"Current Turn: {game.current_player.name}",
                    fontsize=12, fontweight='bold', ha='left')
        )

        last_roll_str = f"{game.last_roll}" if game.last_roll is not None else "-"
        sidebar_texts.append(
            fig.text(info_x, info_y_start - y_step, f"Last Roll: {last_roll_str}",
                    fontsize=11, ha='left')
        )

        resources = game.current_player.resources
        resource_text = "\n".join([f"{res.title()}: {count}" for res, count in resources.items()])
        sidebar_texts.append(
            fig.text(info_x, info_y_start - 2 * y_step, f"Resources:\n{resource_text}",
                    fontsize=10, ha='left', va='top')
        )

    clicked_nodes = []

    def on_click(event):

        if event.inaxes != ax or not hasattr(game, 'build_mode') or game.build_mode is None:
            print("Select a build mode first.")
            return

        click_x, click_y = event.xdata, event.ydata
        threshold = 0.2
        closest_node = None
        min_dist = float('inf')
        for node_id, (x, y) in pos.items():
            dist = ((x - click_x) ** 2 + (y - click_y) ** 2) ** 0.5
            if dist < threshold and dist < min_dist:
                closest_node = node_id
                min_dist = dist

        if closest_node is not None:
            clicked_nodes.append(closest_node)
            if game.build_mode == 'road' and len(clicked_nodes) == 2:
                node1, node2 = clicked_nodes
                clicked_nodes.clear()
                if on_node_click:
                    on_node_click((node1, node2), fig, ax)
            elif game.build_mode in ['settlement', 'city']:
                if on_node_click:
                    on_node_click(closest_node, fig, ax)

    fig.canvas.mpl_connect('button_press_event', on_click)

    button_ax1 = plt.axes([0.86, 0.84, 0.12, 0.05])
    button_ax2 = plt.axes([0.86, 0.77, 0.12, 0.05])
    button_ax3 = plt.axes([0.86, 0.7, 0.12, 0.05])
    button_ax4 = plt.axes([0.86, 0.63, 0.12, 0.05])
    button_ax5 = plt.axes([0.86, 0.56, 0.12, 0.05])

    btn_settlement = widgets.Button(button_ax1, 'Place Settlement')
    btn_road = widgets.Button(button_ax2, 'Place Road')
    btn_city = widgets.Button(button_ax3, 'Place City')
    btn_roll = widgets.Button(button_ax4, 'Roll')
    btn_pass = widgets.Button(button_ax5, 'Pass Turn')

    def set_settlement(event):
        game.build_mode = 'settlement'
        print("Build mode: Settlement")

    def set_road(event):
        game.build_mode = 'road'
        print("Build mode: Road")
    
    def set_city(event):
        game.build_mode = 'city'
        print("Build mode: City")

    def pass_turn(event):   
        game.pass_turn(fig, ax)
        game.build_mode = None
    
    def roll(event):
        game.roll(fig, ax)

    btn_settlement.on_clicked(set_settlement)
    btn_road.on_clicked(set_road)
    btn_city.on_clicked(set_city)
    btn_roll.on_clicked(roll)   
    btn_pass.on_clicked(pass_turn)

    plt.axis('off')
    plt.tight_layout()
    if not redraw_only:
        plt.show()
    else:
        fig.canvas.draw()
import random
from player import Player 


class Game:
    def __init__ (self, players, tiles, graph):
        self.players = players
        self.tiles =  tiles
        self.G = graph

    def roll(self):
        roll = random.randint(1,6) + random.randint(1,6)
        print(f"\n Dice Roll: {roll}")
        
        for tile in self.tiles:
            if tile.frequency == roll:
                resource = tile.get_resource()
                if not resource :
                    continue
                for node_id in tile.corner_nodes:
                    for player in self.players:
                        if node_id in player.settlements:
                            player.add_resource(resource, 1)
                            print(f"{player.name} receives 1 {resource} from settlement on node {node_id}")
                        elif node_id in player.cities:
                            player.add_resource(resource, 2)
                            print(f"{player.name} receives 2 {resource} from city on node {node_id}")

if __name__ == "__main__":
    from catanboard import tiles, G
    from player import Player
    from game import Game
    import matplotlib.pyplot as plt
    import networkx as nx

    player1 = Player("Red")
    player2 = Player("Blue")

    player1.settlements.add(8)
    player2.cities.add(13)

    game = Game([player1, player2], tiles, G)
    game.roll()

    print(f"\nFinal Resources:")
    print(player1.name, player1.resources)
    print(player2.name, player2.resources)

    pos = nx.get_node_attributes(G, 'coordinates')

    clicked_nodes = []

    fig, ax = plt.subplots(figsize=(10, 10))
    nx.draw(G, pos, ax=ax,
            node_color='lightblue',
            edge_color='gray',
            node_size=300,
            with_labels=True,
            font_size=8)

    for tile in tiles:
        if hasattr(tile, 'center') and tile.center:
            x, y = tile.center

            label = tile.resource
            if tile.frequency:
                label += f" ({tile.frequency})"

            ax.text(x, y,
                    label,
                    ha='center', va='center',
                    fontsize=9, fontweight='bold',
                    bbox=dict(facecolor='white', alpha=0.6, boxstyle='round,pad=0.2'),
                    zorder=0)

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

        if closest_node is not None:
            print(f"✅ You clicked on node {closest_node}")
            if closest_node not in clicked_nodes:
                clicked_nodes.append(closest_node)
                ax.plot(pos[closest_node][0], pos[closest_node][1],
                        marker='o', markersize=15, color='orange', zorder=10)
                ax.text(pos[closest_node][0], pos[closest_node][1] + 0.2,
                        f"Selected", color='black', fontsize=9, ha='center')
                fig.canvas.draw()

    fig.canvas.mpl_connect('button_press_event', on_click)

    plt.title("Catan Board")
    plt.axis('off')
    plt.tight_layout()
    plt.show()
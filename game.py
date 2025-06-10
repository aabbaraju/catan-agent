import random
from player import Player 


class Game:
    def __init__(self, players, tiles, graph):
        self.players = players
        self.tiles = tiles
        self.G = graph
        self.current_index = 0 

    @property
    def current_player(self):
        return self.players[self.current_index]

    def roll(self):
        roll = random.randint(1, 6) + random.randint(1, 6)
        print(f"\n Dice Roll: {roll}")

        for tile in self.tiles:
            if tile.frequency == roll:
                resource = tile.get_resource()
                if not resource:
                    continue
                for node_id in tile.corner_nodes:
                    for player in self.players:
                        if node_id in player.settlements:
                            player.add_resource(resource, 1)
                            print(f"{player.name} receives 1 {resource} from settlement on node {node_id}")
                        elif node_id in player.cities:
                            player.add_resource(resource, 2)
                            print(f"{player.name} receives 2 {resource} from city on node {node_id}")

    def handle_node_click(self, node_id, fig, ax):
        if node_id in self.G.nodes and self.G.nodes[node_id]['occupied_by'] is None:
            self.current_player.settlements.add(node_id)
            self.G.nodes[node_id]['occupied_by'] = self.current_player.name
            print(f"🏠 {self.current_player.name} placed a settlement at node {node_id}")

            from catanboardVisualizer import render_board
            render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)

if __name__ == "__main__":
    from catanboard import tiles, G
    from player import Player
    from game import Game
    from catanboardVisualizer import render_board

    player1 = Player("Red")
    player2 = Player("Blue")

    player1.settlements.add(8)
    player2.cities.add(13)

    game = Game([player1, player2], tiles, G)
    game.roll()

    print(f"\nFinal Resources:")
    print(player1.name, player1.resources)
    print(player2.name, player2.resources)

    render_board(G, tiles, on_node_click=game.handle_node_click, game=game)
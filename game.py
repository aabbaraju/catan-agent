import random
from player import Player 


class Game:
    def __init__(self, players, tiles, graph):
        self.players = players
        self.tiles = tiles
        self.G = graph
        self.current_index = 0 
        self.build_mode = None

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

    def handle_node_click(self, node_id_or_edge, fig, ax):
        if self.build_mode == 'road':
            node1, node2 = node_id_or_edge
            self._handle_road_click((node1, node2), fig, ax)
        elif self.build_mode == 'settlement':
            self._handle_settlement_click(node_id_or_edge, fig, ax)
        elif self.build_mode == 'city':
            self._handle_city_click(node_id_or_edge, fig, ax)

    def _handle_settlement_click(self, node_id, fig, ax):
        if node_id not in self.G.nodes or self.G.nodes[node_id]['occupied_by'] is not None:
            print("Invalid or occupied node.")
            return

        for neighbor in self.G.neighbors(node_id):
            if self.G.nodes[neighbor].get('occupied_by') is not None:
                print("Too close to another settlement.")
                return

        self.current_player.settlements.add(node_id)
        self.G.nodes[node_id]['occupied_by'] = self.current_player.name
        print(f"{self.current_player.name} placed a settlement at node {node_id}")
        from catanboardVisualizer import render_board
        render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)
    
    def _handle_city_click(self, node_id, fig, ax):
        if node_id not in self.current_player.settlements:
            print("You must upgrade one of your own settlements to a city.")
            return
        self.current_player.settlements.remove(node_id)
        self.current_player.cities.add(node_id)
        self.G.nodes[node_id]['is_city'] = True
        print(f"{self.current_player.name} upgraded settlement at node {node_id} to a city.")

        from catanboardVisualizer import render_board
        render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)

    def _handle_road_click(self, edge, fig, ax):
        node1, node2 = edge
        if not self.G.has_edge(node1, node2):
            print("Invalid edge.")
            return

        if edge in self.current_player.roads or tuple(reversed(edge)) in self.current_player.roads:
            print("Road already placed.")
            return
        
        connected = (
            node1 in self.current_player.settlements or
            node2 in self.current_player.settlements or
            any(n in (node1, node2) for road in self.current_player.roads for n in road)
        )
        if not connected:
            print("Road must connect to your existing road or settlement.")
            return

        self.current_player.roads.add(edge)
        print(f"{self.current_player.name} placed a road between {node1} and {node2}")
        from catanboardVisualizer import render_board
        render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)

if __name__ == "__main__":
    from catanboard import tiles, G
    from player import Player
    from game import Game
    from catanboardVisualizer import render_board

    player1 = Player("Red")
    player2 = Player("Blue")

    game = Game([player1, player2], tiles, G)
    game.roll()

    print(f"\nFinal Resources:")
    print(player1.name, player1.resources)
    print(player2.name, player2.resources)

    render_board(G, tiles, on_node_click=game.handle_node_click, game=game)
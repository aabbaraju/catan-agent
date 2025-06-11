import random
from player import Player 


class Game:
    def __init__(self, players, tiles, graph):
        self.players = players
        self.tiles = tiles
        self.G = graph
        self.current_index = 0 
        self.build_mode = None
        self.setup_phase = True
        self.setup_stage = 0
        self.setup_placements = {player.name: 0 for player in players}
        self.forward_order = True
        self.turn_order_rolls = {}
        self.turn_order_determined = False
        self.has_rolled_this_turn = False

    COSTS = {
    'settlement': {'wood': 1, 'brick': 1, 'sheep': 1, 'wheat': 1},
    'city': {'wheat': 2, 'ore': 3},
    'road': {'wood': 1, 'brick': 1}
    }

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
    
    def _can_afford(self, structure):
        cost = self.COSTS.get(structure, {})
        return all(self.current_player.resources.get(res, 0) >= amount for res, amount in cost.items())
    
    def _deduct_cost(self, structure):
        for res, amount in self.COSTS[structure].items():
            self.current_player.resources[res] -= amount
    
    def place_initial(self, node_or_edge, fig, ax):
        player = self.current_player

        if isinstance(node_or_edge, tuple):  # road
            node1, node2 = node_or_edge
            if not (node1 in player.settlements or node2 in player.settlements):
                print("Initial road must connect to your settlement.")
                return
            if not self.G.has_edge(node1, node2):
                print("Invalid edge.")
                return
            player.roads.add((node1, node2))
            print(f"{player.name} placed initial road {node1} ↔ {node2}")
            self.setup_placements[player.name] += 1

        else: 
            node = node_or_edge
            if self.G.nodes[node].get('occupied_by') is not None:
                print("Node occupied.")
                return
            for neighbor in self.G.neighbors(node):
                if self.G.nodes[neighbor].get('occupied_by') is not None:
                    print("Too close to another settlement.")
                    return
            player.settlements.add(node)
            self.G.nodes[node]['occupied_by'] = player.name
            print(f"{player.name} placed initial settlement at {node}")
            self.setup_placements[player.name] += 1

            if self.setup_stage == 1:
                for tile in self.tiles:
                    if tile.frequency and node in tile.corner_nodes:
                        resource = tile.get_resource()
                        if resource:
                            player.add_resource(resource, 1)
                            print(f"{player.name} received 1 {resource} from starting tile")

        if self.setup_placements[player.name] == 2:
            self.setup_placements[player.name] = 0 
            self._advance_setup_turn()

        from catanboardVisualizer import render_board
        render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)
    
    def _advance_setup_turn(self):
        if self.forward_order:
            self.current_index += 1
            if self.current_index >= len(self.players):
                self.forward_order = False
                self.setup_stage = 1
                self.current_index = len(self.players) - 1
        else:
            self.current_index -= 1
            if self.current_index < 0:
                self.setup_phase = False
                self.current_index = 0

    def handle_node_click(self, node_id_or_edge, fig, ax):
        if self.setup_phase:
            self.place_initial(node_id_or_edge, fig, ax)
        else:
            if self.build_mode == 'road':
                node1, node2 = node_id_or_edge
                self._handle_road_click((node1, node2), fig, ax)
            elif self.build_mode == 'settlement':
                self._handle_settlement_click(node_id_or_edge, fig, ax)
            elif self.build_mode == 'city':
                self._handle_city_click(node_id_or_edge, fig, ax)

    def _handle_settlement_click(self, node_id, fig, ax):
        if not self._can_afford('settlement'):
            print("Not enough resources to build a settlement.")
            return
    
        if node_id not in self.G.nodes or self.G.nodes[node_id]['occupied_by'] is not None:
            print("Invalid or occupied node.")
            return

        for neighbor in self.G.neighbors(node_id):
            if self.G.nodes[neighbor].get('occupied_by') is not None:
                print("Too close to another settlement.")
                return
            
        self._deduct_cost('settlement')
        self.current_player.settlements.add(node_id)
        self.G.nodes[node_id]['occupied_by'] = self.current_player.name
        print(f"{self.current_player.name} placed a settlement at node {node_id}")
        from catanboardVisualizer import render_board
        render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)
    
    def _handle_city_click(self, node_id, fig, ax):
        if not self._can_afford('city'):
            print("Not enough resources to build a city.")
            return
        if node_id not in self.current_player.settlements:
            print("You must upgrade one of your own settlements to a city.")
            return
        
        self._deduct_cost('city')
        self.current_player.settlements.remove(node_id)
        self.current_player.cities.add(node_id)
        self.G.nodes[node_id]['is_city'] = True
        print(f"{self.current_player.name} upgraded settlement at node {node_id} to a city.")

        from catanboardVisualizer import render_board
        render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)

    def _handle_road_click(self, edge, fig, ax):

        if not self._can_afford('road'):
            print("Not enough resources to build a road.")
            return
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

        self._deduct_cost('road')
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
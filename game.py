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
        self.setup_status = {player.name: {'settlement': False, 'road': False} for player in players}
        self.forward_order = True
        self.turn_order_rolls = {}
        self.turn_order_determined = False
        self.has_rolled = {player.name: False for player in self.players}
        self.robber_tile = None
        self.last_roll = None

    COSTS = {
    'settlement': {'wood': 1, 'brick': 1, 'sheep': 1, 'wheat': 1},
    'city': {'wheat': 2, 'ore': 3},
    'road': {'wood': 1, 'brick': 1}
    }

    @property
    def current_player(self):
        return self.players[self.current_index]
    
    def _handle_robber(self, fig, ax):
        print("Click a tile to move the robber.")

        def on_tile_click(event):
            if event.inaxes != ax:
                return

            click_x, click_y = event.xdata, event.ydata
            threshold = 0.6  
            closest_tile = None
            min_dist = float('inf')

            for tile in self.tiles:
                cx, cy = tile.center
                dist = ((cx - click_x) ** 2 + (cy - click_y) ** 2) ** 0.5
                if dist < threshold and dist < min_dist:
                    closest_tile = tile
                    min_dist = dist

            if closest_tile is None:
                print("No valid tile selected.")
                return

            if closest_tile == self.robber_tile:
                print("Robber is already on this tile. Choose another.")
                return

            if self.robber_tile is not None:
                self.robber_tile.has_robber = False
                print(f"Robber removed from tile with resource: {self.robber_tile.resource}")

            self.robber_tile = closest_tile
            self.robber_tile.has_robber = True
            print(f"Robber moved to tile with resource: {closest_tile.resource}")

            victims = set()
            for node_id in closest_tile.corner_nodes:
                for player in self.players:
                    if player != self.current_player and (node_id in player.settlements or node_id in player.cities):
                        victims.add(player)

            if victims:
                victim = random.choice(list(victims))
                victim_cards = [res for res, count in victim.resources.items() for _ in range(count)]
                if victim_cards:
                    stolen_resource = random.choice(victim_cards)
                    victim.resources[stolen_resource] -= 1
                    self.current_player.resources[stolen_resource] += 1
                    print(f"{self.current_player.name} stole 1 {stolen_resource} from {victim.name}")
                else:
                    print(f"{victim.name} had no resources to steal.")
            else:
                print("No player to steal from on this tile.")

            from catanboardVisualizer import render_board
            render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)

            fig.canvas.mpl_disconnect(cid)

        cid = fig.canvas.mpl_connect('button_press_event', on_tile_click)

    def check_win_condition(self, fig, ax):
        for player in self.players:
            if player.victory_points() >= 10:
                print(f"{player.name} wins the game with {player.victory_points()} points!")
                self.disable_all_actions(fig)
                from catanboardVisualizer import render_board
                render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)
                break

    def disable_all_actions(self, fig):
        self.build_mode = None
        self.has_rolled = {player.name: True for player in self.players}
        self.game_over = True
        print("Game Over: No further actions can be taken.")

    def _discard_half_resources(self):
        for player in self.players:
            total_cards = sum(player.resources.values())
            if total_cards > 7:
                to_discard = total_cards // 2
                print(f"{player.name} has {total_cards} resources and must discard {to_discard}.")

                resource_list = []
                for res, count in player.resources.items():
                    resource_list.extend([res] * count)

                discarded = random.sample(resource_list, to_discard)
                for res in discarded:
                    player.resources[res] -= 1
                print(f"{player.name} discards: {discarded}")
    
    def update_longest_road(self):
        def longest_path_length(player):
            from networkx import Graph

            road_graph = Graph()
            for a, b in player.roads:
                road_graph.add_edge(a, b)

            def dfs(node, visited):
                visited.add(node)
                max_length = 0
                for neighbor in road_graph.neighbors(node):
                    if neighbor not in visited:
                        length = 1 + dfs(neighbor, visited.copy())
                        max_length = max(max_length, length)
                return max_length

            return max((dfs(n, set()) for n in road_graph.nodes), default=0)

        max_length = 0
        longest_player = None

        for player in self.players:
            length = longest_path_length(player)
            if length >= 5 and length > max_length:
                max_length = length
                longest_player = player

        for player in self.players:
            player.has_longest_road = (player == longest_player)

        if longest_player:
            print(f"{longest_player.name} has the Longest Road ({max_length} segments)")

    def roll(self, fig, ax):
        roll_val = random.randint(1, 6) + random.randint(1, 6)

        self.last_roll = roll_val
        from catanboardVisualizer import render_board
        render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)
        
        if not self.turn_order_determined:
            name = self.current_player.name
            if name in self.turn_order_rolls:
                print(f"{name} already rolled.")
                return

            self.last_roll = roll_val
            self.turn_order_rolls[name] = roll_val
            print(f"{name} rolled {roll_val} for turn order.")

            from catanboardVisualizer import render_board
            render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)

            self.current_index = (self.current_index + 1) % len(self.players)

            if len(self.turn_order_rolls) == len(self.players):
                self._set_turn_order()
                print("All players rolled. Turn order determined:")
                for p in self.players:
                    print(f"→ {p.name} (rolled {self.turn_order_rolls[p.name]})")
            return

        if self.setup_phase:
            print("No need to roll during setup.")
            return

        if self.has_rolled[self.current_player.name]:
            print("You already rolled this turn.")
            return

        print(f"\n{self.current_player.name} rolls: {roll_val}")
        self.has_rolled[self.current_player.name] = True

        if roll_val == 7:
            print(f"{self.current_player.name} rolled a 7! Moving the robber.")
            self._discard_half_resources()
            self._handle_robber(fig, ax)
            return
        
        for tile in self.tiles:
            if tile.frequency == roll_val:
                if tile.resource == 'desert':
                    Game.robber_tile = tile
                    break
                if tile == self.robber_tile:
                    print(f"Robber is blocking the tile with resource: {tile.resource}")
                    continue
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
    
    def pass_turn(self, fig, ax):
        if not self.turn_order_determined:
            print("Finish rolling for turn order first.")
            return

        if self.setup_phase:
            print("Can't pass manually during setup.")
            return

        if not self.has_rolled[self.current_player.name]:
            print("You must roll before passing.")
            return

        self.current_index = (self.current_index + 1) % len(self.players)
        self.has_rolled[self.current_player.name] = False

        from catanboardVisualizer import render_board
        render_board(self.G, self.tiles, game=self, fig=fig, ax=ax, redraw_only=True)

        print(f"{self.current_player.name}'s turn")
    
    def _set_turn_order(self):
        ordered_players = sorted(self.players, key=lambda p: self.turn_order_rolls[p.name], reverse=True)
        self.players = ordered_players
        self.current_index = 0
        self.turn_order_determined = True
        self.setup_phase = True
        self.setup_stage = 0
        self.forward_order = True
        self.setup_placements = {p.name: 0 for p in self.players}
        print("Turn order determined:", [p.name for p in self.players])

    def _can_afford(self, structure):
        cost = self.COSTS.get(structure, {})
        return all(self.current_player.resources.get(res, 0) >= amount for res, amount in cost.items())
    
    def _deduct_cost(self, structure):
        for res, amount in self.COSTS[structure].items():
            self.current_player.resources[res] -= amount
    
    def place_initial(self, node_or_edge, fig, ax):
        player = self.current_player

        if isinstance(node_or_edge, tuple): 
            node1, node2 = node_or_edge
            if not (
                self.G.nodes[node1].get('occupied_by') == player.name or
                self.G.nodes[node2].get('occupied_by') == player.name
            ):
                print("Initial road must connect to your settlement.")
                return
            if not self.G.has_edge(node1, node2):
                print("Invalid edge.")
                return
            if self.setup_status[player.name]['road']:
                print("You've already placed your road.")
                return
            player.roads.add((node1, node2))
            print(f"{player.name} placed initial road {node1} ↔ {node2}")
            self.setup_status[player.name]['road'] = True

        else: 
            node = node_or_edge
            if self.G.nodes[node].get('occupied_by') is not None:
                print("Node occupied.")
                return
            if self.setup_status[player.name]['settlement']:
                print("You've already placed your settlement.")
                return
            for neighbor in self.G.neighbors(node):
                if self.G.nodes[neighbor].get('occupied_by') is not None:
                    print("Too close to another settlement.")
                    return
            player.settlements.add(node)
            self.G.nodes[node]['occupied_by'] = player.name
            print(f"{player.name} placed initial settlement at {node}")
            self.setup_status[player.name]['settlement'] = True

            if self.setup_stage == 1:
                for tile in self.tiles:
                    if tile.frequency and node in tile.corner_nodes:
                        resource = tile.get_resource()
                        if resource:
                            player.add_resource(resource, 1)
                            print(f"{player.name} received 1 {resource} from starting tile")

        if all(self.setup_status[player.name].values()):
            self.setup_status[player.name] = {'settlement': False, 'road': False}
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
                self.has_rolled = {player.name: False for player in self.players}

    def handle_node_click(self, node_id_or_edge, fig, ax):
        if not self.turn_order_determined:
            print("You must roll to determine turn order before building.")
            return

        if self.setup_phase:
            self.place_initial(node_id_or_edge, fig, ax)
            return

        if not self.has_rolled[self.current_player.name]:
            print("You must roll before building.")
            return

        if self.build_mode == 'road':
            if not isinstance(node_id_or_edge, tuple) or len(node_id_or_edge) != 2:
                print("Invalid edge selection for road.")
                self.build_mode = None
                return
            self._handle_road_click(node_id_or_edge, fig, ax)
            self.build_mode = None 

        elif self.build_mode == 'settlement':
            if not isinstance(node_id_or_edge, int):
                print("Invalid node selection for settlement.")
                self.build_mode = None
                return
            self._handle_settlement_click(node_id_or_edge, fig, ax)
            self.build_mode = None

        elif self.build_mode == 'city':
            if not isinstance(node_id_or_edge, int):
                print("Invalid node selection for city.")
                self.build_mode = None
                return
            self._handle_city_click(node_id_or_edge, fig, ax)
            self.build_mode = None

        else:
            print("No build mode selected.")

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
        self.check_win_condition(fig, ax)
    
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
        self.check_win_condition(fig, ax)

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

        self.current_player.roads.add(edge)
        self.update_longest_road()
        self.check_win_condition(fig, ax)

if __name__ == "__main__":
    from catanboard import tiles, G
    from player import Player
    from game import Game
    from catanboardVisualizer import render_board

    player1 = Player("Red")
    player2 = Player("Blue")

    game = Game([player1, player2], tiles, G)

    render_board(G, tiles, on_node_click=game.handle_node_click, game=game)
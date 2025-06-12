from catanboard import tiles, G
from player import Player
from game import Game
import random

class CatanEnvironment:
    def __init__(self, game):
        self.game = game

    def get_state(self):
        return {
            "current_player": self.game.current_player.name,
            "resources": self.game.current_player.resources.copy(),
            "settlements": list(self.game.current_player.settlements),
            "cities": list(self.game.current_player.cities),
            "roads": list(self.game.current_player.roads),
            "victory_points": self.game.current_player.victory_points(),
        }

    def get_valid_actions(self):
        return self.game.get_valid_actions()

    def is_done(self):
        return self.game.game_over

    def step(self, action):
        reward = 0
        if self.game.current_player.victory_points() >= 10:
            reward = 1
        player = self.game.current_player

        if self.game.setup_phase:
            if not self.game.turn_order_determined:
                if action == "roll":
                    self.game.turn_order_rolls[player.name] = random.randint(1, 12)
                    print(f"{player.name} rolled {self.game.turn_order_rolls[player.name]} for turn order.")
                    if len(self.game.turn_order_rolls) == len(self.game.players):
                        self.game._set_turn_order()
                    else:
                        self.game.current_index = (self.game.current_index + 1) % len(self.game.players)
                    return self.get_state(), self.game.game_over
                else:
                    print(f"Must roll to determine turn order first.")
                    return self.get_state(), self.game.game_over
            else:
                status = self.game.setup_status[player.name]
                if action == "build_settlement" and not status['settlement']:
                    for node in self.game.G.nodes:
                        if self.game.G.nodes[node]['occupied_by'] is None:
                            too_close = any(
                                self.game.G.nodes[neighbor]['occupied_by'] is not None
                                for neighbor in self.game.G.neighbors(node)
                            )
                            if not too_close:
                                self.game.place_initial(node)
                                return self.get_state(), self.game.game_over
                elif action == "build_road" and status['settlement'] and not status['road']:
                    for neighbor in self.game.G.neighbors(list(player.settlements)[-1]):
                        edge = (list(player.settlements)[-1], neighbor)
                        if self.game.G.has_edge(*edge):
                            if edge not in player.roads and tuple(reversed(edge)) not in player.roads:
                                self.game.place_initial(edge)
                                return self.get_state(), self.game.game_over
                else:
                    print(f"Invalid setup action: {action}")
                    return self.get_state(), self.game.game_over

        else:
            if action == "roll":
                self.game.roll()
            elif action == "pass":
                self.game.pass_turn()
            elif action == "build_settlement":
                for node in self.game.G.nodes:
                    if self.game.G.nodes[node]['occupied_by'] is None:
                        too_close = any(
                            self.game.G.nodes[neighbor]['occupied_by'] is not None
                            for neighbor in self.game.G.neighbors(node)
                        )
                        if not too_close and self.game._can_afford("settlement"):
                            self.game._handle_settlement_click(node, None, None)
                            break
            elif action == "build_road":
                for road in list(self.game.G.edges):
                    a, b = road
                    if ((a, b) not in player.roads and (b, a) not in player.roads and
                            self.game._can_afford("road")):
                        connected = (
                            a in player.settlements or
                            b in player.settlements or
                            any(n in (a, b) for r in player.roads for n in r)
                        )
                        if connected:
                            self.game._handle_road_click((a, b), None, None)
                            break
            elif action == "build_city":
                for node in list(player.settlements):
                    if self.game._can_afford("city"):
                        self.game._handle_city_click(node, None, None)
                        break
            elif action == "bank_trade":
                for give in player.resources:
                    if player.resources[give] >= 4:
                        for receive in player.resources:
                            if receive != give:
                                self.game.bank_trade(give, receive)
                                break
                        break
            else:
                print(f"Unknown action: {action}")

        return self.get_state(), reward, self.game.game_over, {}

    def reset(self):
        p1, p2 = Player("Red"), Player("Blue")
        self.game = Game([p1, p2], tiles, G)
        return self.get_state()

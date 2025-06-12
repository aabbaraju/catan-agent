from player import Player
from game import Game
import random
from gym.spaces import Discrete, Box
import numpy as np
import torch
from catanboard import generate_board

class CatanEnvironment:
    def __init__(self, game):
        self.game = game
        self.actions = ["roll", "pass", "build_settlement", "build_road", "build_city", "bank_trade"]
        self.action_space = Discrete(len(self.actions))
        self.observation_space = Box(low=0, high=100, shape=(10,), dtype=np.float32)

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
        player = self.game.current_player
        valid = []

        if self.game.setup_phase:
            print("SETUP PHASE")
            status = self.game.setup_status[player.name]
            if not self.game.turn_order_determined:
                return ["roll"]
            elif not status['settlement']:
                return ["build_settlement"]
            elif status['settlement'] and not status['road']:
                return ["build_road"]
            else:
                return []

        if not self.game.has_rolled[player.name]:
            valid.append("roll")
        else:
            valid.append("pass")
            if self.game._can_afford("settlement", player):
                for node in self.game.G.nodes:
                    if self.game.G.nodes[node]['occupied_by'] is None:
                        too_close = any(
                            self.game.G.nodes[neighbor]['occupied_by'] is not None
                            for neighbor in self.game.G.neighbors(node)
                        )
                        if not too_close:
                            valid.append("build_settlement")
                            break

            if self.game._can_afford("road"):
                for edge in self.game.G.edges:
                    a, b = edge
                    if ((a, b) not in player.roads and (b, a) not in player.roads):
                        connected = (
                            a in player.settlements or
                            b in player.settlements or
                            any(n in (a, b) for r in player.roads for n in r)
                        )
                        if connected:
                            valid.append("build_road")
                            break

            if self.game._can_afford("city") and len(player.settlements) > 0:
                valid.append("build_city")

            for give in player.resources:
                if player.resources[give] >= 4:
                    valid.append("bank_trade")
                    break
            print(valid)
        return list(set(valid))

    def is_done(self):
        return self.game.game_over
    
    @staticmethod
    def state_to_tensor(state):
        resource_order = ['wood', 'brick', 'sheep', 'wheat', 'ore']
        resource_vec = [state["resources"].get(res, 0) for res in resource_order]

        settlements = len(state["settlements"])
        cities = len(state["cities"])
        roads = len(state["roads"])
        vps = state["victory_points"]

        player_encoding = [1 if state["current_player"] == "Red" else 0]

        vector = resource_vec + [settlements, cities, roads, vps] + player_encoding
        return torch.tensor(vector, dtype=torch.float32)

    def step(self, action):
        reward = 0
        player = self.game.current_player
        prev_vp = player.victory_points()
        prev_road_count = len(player.roads)
        reward = 0.0

        if self.game.setup_phase:
            if not self.game.turn_order_determined:
                if action == "roll":
                    self.game.turn_order_rolls[player.name] = random.randint(1, 12)
                    print(f"{player.name} rolled {self.game.turn_order_rolls[player.name]} for turn order.")
                    if len(self.game.turn_order_rolls) == len(self.game.players):
                        self.game._set_turn_order()
                    else:
                        print(f"[{player.name}] Invalid or redundant setup action: {action}. Advancing setup turn.")
                        self.game._advance_setup_turn()
                    return self.get_state(), 0.0, self.game.game_over, {}
                else:
                    print(f"Must roll to determine turn order first.")
                    return self.get_state(), 0.0, self.game.game_over, {}
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
                                return self.get_state(), 0.0, self.game.game_over, {}
                elif action == "build_road" and status['settlement'] and not status['road']:
                    for neighbor in self.game.G.neighbors(list(player.settlements)[-1]):
                        edge = (list(player.settlements)[-1], neighbor)
                        if self.game.G.has_edge(*edge):
                            if edge not in player.roads and tuple(reversed(edge)) not in player.roads:
                                self.game.place_initial(edge)
                                return self.get_state(), 0.0, self.game.game_over, {}
                else:
                    print(f"[{player.name}] Invalid or redundant setup action: {action}. Advancing turn.")
                    self.game._advance_setup_turn()
                    return self.get_state(), -0.2, self.game.game_over, {}

        else:
            if action == "roll":
                self.game.roll()
            elif action == "pass":
                self.game.pass_turn()
            elif action == "build_settlement":
                built = False
                for node in self.game.G.nodes:
                    if self.game.G.nodes[node]['occupied_by'] is None:
                        too_close = any(
                            self.game.G.nodes[neighbor]['occupied_by'] is not None
                            for neighbor in self.game.G.neighbors(node)
                        )
                        if not too_close and self.game._can_afford("settlement"):
                            self.game._handle_settlement_click(node, None, None)
                            built = True
                            break
                if not built:
                    reward -= 0.2
            elif action == "build_road":
                built = False
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
                            built = True
                            break
                if not built:
                    reward -= 0.2
            elif action == "build_city":
                built = False
                for node in list(player.settlements):
                    if self.game._can_afford("city"):
                        self.game._handle_city_click(node, None, None)
                        built = True
                        break
                if not built:
                    reward -= 0.2
            elif action == "bank_trade":
                built = False
                for give in player.resources:
                    if player.resources[give] >= 4:
                        for receive in player.resources:
                            if receive != give:
                                self.game.bank_trade(give, receive)
                                built = True
                                break
                        break
                if not built:
                    reward -= 0.2
            else:
                print(f"Unknown action: {action}")

        new_vp = player.victory_points()
        new_road_count = len(player.roads)
        reward += (new_vp - prev_vp) * 1
        reward += (new_road_count - prev_road_count) * 1

        if new_vp >= 10:
            reward += 10.0

        return self.get_state(), reward, self.game.game_over, {}

    def reset(self):
        tiles, G = generate_board()
        p1, p2 = Player("Red"), Player("Blue")
        self.game = Game([p1, p2], tiles, G)
        return self.get_state()

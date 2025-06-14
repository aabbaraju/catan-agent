import random
import numpy as np
import torch
from gym.spaces import Discrete, Box

from game import Game
from player import Player
from catanboard import generate_board

class CatanEnvironment:
    def __init__(self, game: Game):
        self.game = game
        self.actions = ["roll", "pass", "build_settlement", "build_road", "build_city", "bank_trade"]
        self.action_space = Discrete(len(self.actions))
        self.observation_space = Box(low=0, high=100, shape=(10,), dtype=np.float32)

    def get_state(self):
        player = self.game.current_player
        return {
            "current_player": player.name,
            "resources": player.resources.copy(),
            "settlements": list(player.settlements),
            "cities": list(player.cities),
            "roads": list(player.roads),
            "victory_points": player.victory_points(),
        }

    def get_valid_actions(self):
        player = self.game.current_player
        if self.game.setup_phase:
            if not self.game.turn_order_determined:
                return ["roll"]
            status = self.game.setup_status[player.name]
            if not status['settlement']:
                return ["build_settlement"]
            if status['settlement'] and not status['road']:
                return ["build_road"]
            return []
        
        valid = []
        if not self.game.has_rolled[player.name]:
            valid.append("roll")
        else:
            valid.append("pass")
            
            if self.game._can_afford("settlement", player):
                for node in self.game.G.nodes:
                    if self.game.G.nodes[node]['occupied_by'] is None:
                        too_close = any(
                            self.game.G.nodes[n]['occupied_by'] is not None
                            for n in self.game.G.neighbors(node)
                        )
                        if not too_close:
                            connected_to_player = any(
                                node in road for road in player.roads
                            )
                            if connected_to_player or not player.roads: 
                                valid.append("build_settlement")
                                break
            
            if self.game._can_afford("road"):
                for a, b in self.game.G.edges:
                    road_exists = False
                    for game_player in self.game.players:
                        if (a, b) in game_player.roads or (b, a) in game_player.roads:
                            road_exists = True
                            break
                    
                    if not road_exists:
                        connected_to_current_player = (
                            a in player.settlements or
                            b in player.settlements or
                            any(n in (a, b) for r in player.roads for n in r)
                        )
                        blocks_other_player = False
                        for other_player in self.game.players:
                            if other_player.name != player.name:
                                if a in other_player.settlements:
                                    player_has_adjacent_road = any(
                                        a in road for road in player.roads
                                    )
                                    if not player_has_adjacent_road:
                                        blocks_other_player = True
                                        break
                                
                                if b in other_player.settlements:
                                    player_has_adjacent_road = any(
                                        b in road for road in player.roads
                                    )
                                    if not player_has_adjacent_road:
                                        blocks_other_player = True
                                        break
                        
                        if connected_to_current_player and not blocks_other_player:
                            valid.append("build_road")
                            break
            
            if self.game._can_afford("city") and player.settlements:
                valid.append("build_city")
            
            for give, qty in player.resources.items():
                if qty >= 4:
                    valid.append("bank_trade")
                    break
        
        return list(set(valid))

    @staticmethod
    def state_to_tensor(state):
        resource_order = ['wood','brick','sheep','wheat','ore']
        resource_vec = [state['resources'].get(r,0) for r in resource_order]
        settlements = len(state['settlements'])
        cities = len(state['cities'])
        roads = len(state['roads'])
        vps = state['victory_points']
        player_flag = 1 if state['current_player']=='Red' else 0
        vec = resource_vec + [settlements, cities, roads, vps] + [player_flag]
        return torch.tensor(vec, dtype=torch.float32)

    def step(self, action):
        player = self.game.current_player
        if self.game.setup_phase:
            if not self.game.turn_order_determined:
                if action=='roll':
                    self.game.turn_order_rolls[player.name]=random.randint(1,12)
                    if len(self.game.turn_order_rolls)==len(self.game.players):
                        self.game._set_turn_order()
                    else:
                        self.game._advance_setup_turn()
                    return self.get_state(),0.0,self.game.game_over,{}
                return self.get_state(),0.0,self.game.game_over,{}
            status=self.game.setup_status[player.name]
            if action=='build_settlement' and not status['settlement']:
                for node in self.game.G.nodes:
                    if self.game.G.nodes[node]['occupied_by'] is None:
                        too_close=any(self.game.G.nodes[n]['occupied_by'] for n in self.game.G.neighbors(node))
                        if not too_close:
                            self.game.place_initial(node)
                            return self.get_state(),0.0,self.game.game_over,{}
            if action=='build_road' and status['settlement'] and not status['road']:
                start=list(player.settlements)[-1]
                for nbr in self.game.G.neighbors(start):
                    edge=(start,nbr)
                    if self.game.G.has_edge(*edge) and edge not in player.roads and tuple(reversed(edge)) not in player.roads:
                        self.game.place_initial(edge)
                        return self.get_state(),0.0,self.game.game_over,{}
            self.game._advance_setup_turn()
            return self.get_state(),-0.2,self.game.game_over,{}
        prev_vp=player.victory_points()
        prev_roads=len(player.roads)
        prev_settlements=len(player.settlements)
        prev_cities=len(player.cities)
        reward=0.0
        if action=='roll':
            self.game.roll()
        elif action=='pass':
            self.game.pass_turn()
        elif action=='build_settlement':
            built=False
            if self.game._can_afford('settlement'):
                for node in self.game.G.nodes:
                    if self.game.G.nodes[node]['occupied_by'] is None:
                        too_close=any(self.game.G.nodes[n]['occupied_by'] for n in self.game.G.neighbors(node))
                        if not too_close:
                            self.game._handle_settlement_click(node,None,None)
                            built=True
                            break
            if not built: reward-=0.2
        elif action=='build_road':
            built=False
            if self.game._can_afford('road'):
                for a,b in self.game.G.edges:
                    road_exists_for_any_player = False
                    for game_player in self.game.players:
                        if (a,b) in game_player.roads or (b,a) in game_player.roads:
                            road_exists_for_any_player = True
                            break
                    
                    if not road_exists_for_any_player:
                        conn=(a in player.settlements or b in player.settlements or any(n in (a,b) for r in player.roads for n in r))
                        connects_to_other_settlement = False
                        for other_player in self.game.players:
                            if other_player.name != player.name:
                                if a in other_player.settlements or b in other_player.settlements:
                                    connects_to_other_settlement = True
                                    break
                        
                        if conn and not connects_to_other_settlement:
                            self.game._handle_road_click((a,b),None,None)
                            built=True
                            break
            if not built: reward-=0.2
        elif action=='build_city':
            built=False
            if self.game._can_afford('city'):
                for node in list(player.settlements):
                    self.game._handle_city_click(node,None,None)
                    built=True
                    break
            if not built: reward-=0.2
        elif action=='bank_trade':
            built=False
            for give,qty in player.resources.items():
                if qty>=4:
                    for receive in player.resources:
                        if receive!=give:
                            self.game.bank_trade(give,receive)
                            built=True
                            break
                    break
            if not built: reward-=0.2
        else:
            reward-=0.2
        new_vp=player.victory_points()
        new_roads=len(player.roads)
        new_settlements=len(player.settlements)
        new_cities=len(player.cities)
        new_resources=sum(player.resources.values())
        build_bonus=(new_roads-prev_roads)*1.0 + (new_settlements-prev_settlements)*2.0 + (new_cities-prev_cities)*3.0
        holding_penalty=0.005*max(0,new_resources-4)
        reward+=(new_vp-prev_vp) + build_bonus - holding_penalty
        if new_vp>=10: reward+=10.0
        reward = max(-3.0, min(reward, 10.0))
        return self.get_state(),reward,self.game.game_over,{}

    def reset(self):
        tiles,G=generate_board()
        p1,p2=Player('Red'),Player('Blue')
        self.game=Game([p1,p2],tiles,G)
        return self.get_state()

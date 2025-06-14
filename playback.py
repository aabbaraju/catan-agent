import argparse
import pickle
import random
import torch
import math
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
from matplotlib.animation import FFMpegWriter, PillowWriter
from collections import OrderedDict
from io import StringIO
import sys

from catanboard import generate_board
from game import Game
from player import Player
from environment import CatanEnvironment
from dqn_agent import DQNAgent

resource_colors = {
    'wheat': '#F9DC5C',
    'sheep': '#A1C349',
    'wood': '#8FBC8F',
    'brick': '#D2691E',
    'ore': '#A9A9A9',
    'desert': '#F0E68C'
}

player_colors = {
    'Red': '#FF0000',
    'Blue': '#0000FF'
}

def load_agent(model_path):
    agent = DQNAgent(state_dim=10, action_dim=6, epsilon=0.0, epsilon_min=0.0)
    raw = torch.load(model_path)
    km = {
        "0.weight": "fc1.weight", "0.bias": "fc1.bias",
        "2.weight": "fc2.weight", "2.bias": "fc2.bias",
        "4.weight": "fc3.weight", "4.bias": "fc3.bias"
    }
    mapped = OrderedDict((km[k], v) for k, v in raw.items() if k in km)
    agent.model.load_state_dict(mapped)
    agent.model.eval()
    return agent

def simulate_and_record(actions_out, max_moves=1000, model_path="dqnCatan.pth"):
    seed = random.randint(0, 10**6)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    red_agent = load_agent(model_path)
    blue_agent = load_agent(model_path)
    tiles, G = generate_board()
    game = Game([Player("Red"), Player("Blue")], tiles, G)
    game.visual_mode = False
    env = CatanEnvironment(game)

    actions = []
    logs = []
    states = []

    for turn in range(1, max_moves + 1):
        robber_pos = next((i for i, t in enumerate(tiles) if t.has_robber), None)
        
        pre_state = {
            'resources': {p.name: dict(p.resources) for p in game.players},
            'buildings': {p.name: {
                'settlements': list(p.settlements),
                'roads': list(p.roads),
                'cities': list(getattr(p, 'cities', []))
            } for p in game.players},
            'robber': robber_pos,
            'current': game.current_player.name
        }
        states.append(pre_state)

        current = game.current_player.name
        valid = env.get_valid_actions()

        if game.setup_phase:
            act = random.choice(valid)
        elif game.robber_pending:
            valid_robber_tiles = []
            current_player = game.current_player
            
            for i, tile in enumerate(tiles):
                if tile == game.robber_tile:
                    continue 
                
                for node_id in tile.corner_nodes:
                    for player in game.players:
                        if player != current_player and (node_id in player.settlements or node_id in player.cities):
                            valid_robber_tiles.append(i)
                            break
                    else:
                        continue
                    break
            
            if valid_robber_tiles:
                tile_idx = random.choice(valid_robber_tiles)
                act = f"move_robber {tile_idx}"
            else:
                act = "pass"
        elif not game.has_rolled[current]:
            act = "roll"
        else:
            cities = [a for a in valid if "build_city" in a]
            if cities:
                act = cities[0]
            else:
                settlements = [a for a in valid if "build_settlement" in a]
                if settlements:
                    act = settlements[0]
                else:
                    strategic_roads = []
                    roads = [a for a in valid if "build_road" in a]
                    
                    if roads:
                        current_player = game.current_player
                        num_settlements = len(current_player.settlements)
                        player_resources = current_player.resources
                        can_afford_settlement_soon = (
                            player_resources.get('wood', 0) >= 1 and
                            player_resources.get('brick', 0) >= 1 and
                            player_resources.get('wheat', 0) >= 1 and
                            player_resources.get('sheep', 0) >= 1
                        )
                        
                        if num_settlements < 3 or can_afford_settlement_soon:
                            strategic_roads = roads
                    
                    if strategic_roads:
                        act = strategic_roads[0]
                    else:
                        idxs = [env.actions.index(a) for a in valid]
                        agent = red_agent if current == "Red" else blue_agent
                        choice = agent.select_action(env.state_to_tensor(env.get_state()), idxs)
                        act = env.actions[choice]

        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        env.step(act)
        sys.stdout = old_stdout
        output = mystdout.getvalue()

        actions.append(act)
        logs.append(output.strip().split("\n"))

        if game.game_over:
            break

    with open(actions_out, 'wb') as f:
        pickle.dump({
            'actions': actions,
            'seed': seed,
            'logs': logs,
            'states': states,
            'final_vps': {p.name: p.victory_points() for p in game.players},
            'tile_resources': [t.resource for t in tiles]
        }, f)
    return actions, {p.name: p.victory_points() for p in game.players}

def playback_and_export(pickle_path, output, fps=30, render_every=1):
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)

    seed = data['seed']
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    tiles, G = generate_board()
    game = Game([Player("Red"), Player("Blue")], tiles, G)
    game.visual_mode = False
    env = CatanEnvironment(game)

    plt.style.use('light_background')
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()

    pos = nx.get_node_attributes(G, 'coordinates')
    for i, t in enumerate(tiles):
        center = t.center
        poly = patches.RegularPolygon(center, numVertices=6, radius=0.95,
                                    orientation=math.radians(30),
                                    edgecolor='black', 
                                    facecolor=resource_colors.get(t.resource, 'gray'),
                                    linewidth=1.5, alpha=0.8)
        ax.add_patch(poly)
        label = f"{t.resource}\n({t.frequency})" if hasattr(t, 'frequency') and t.frequency else t.resource
        ax.text(center[0], center[1], label, ha='center', va='center', 
               fontsize=8, fontweight='bold')

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='gray', alpha=0.2, width=1)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=30, node_color='lightblue', alpha=0.5)

    turn_text = ax.text(0.02, 0.98, 'Turn 0', transform=ax.transAxes, 
                       fontsize=12, color='white', bbox=dict(facecolor='black', alpha=0.8))
    vp_text = ax.text(0.02, 0.92, 'VP: Red: 0 | Blue: 0', transform=ax.transAxes,
                     fontsize=10, color='white', bbox=dict(facecolor='black', alpha=0.8))

    metadata = dict(title='Catan Game', artist='AI Players')
    writer = PillowWriter(fps=fps, metadata=metadata) if output.endswith('.gif') else FFMpegWriter(fps=fps, metadata=metadata)
    
    dynamic_elements = []
    frame_count = 0

    with writer.saving(fig, output, dpi=100):
        for i, (act, turn_log) in enumerate(zip(data['actions'], data['logs']), 1):
            for element in dynamic_elements:
                try:
                    element.remove()
                except:
                    pass
            dynamic_elements.clear()
            
            env.step(act)
            
            turn_text.set_text(f"Turn {i}")
            vps = {p.name: p.victory_points() for p in game.players}
            vp_text.set_text(f"VP: Red: {vps['Red']} | Blue: {vps['Blue']}")
            
            robber_tile = next((t for t in tiles if t.has_robber), None)
            if robber_tile:
                robber = patches.Circle(robber_tile.center, radius=0.3, 
                                      facecolor='black', edgecolor='red', 
                                      linewidth=2, zorder=10)
                ax.add_patch(robber)
                dynamic_elements.append(robber)
            
            for player in game.players:
                color = player_colors[player.name]
                
                for node in player.settlements:
                    x, y = G.nodes[node]['coordinates']
                    settlement = patches.Rectangle((x-0.2, y-0.2), 0.4, 0.4,
                                                 facecolor=color, edgecolor='white',
                                                 linewidth=1, zorder=5)
                    ax.add_patch(settlement)
                    dynamic_elements.append(settlement)

                for node in getattr(player, 'cities', []):
                    x, y = G.nodes[node]['coordinates']
                    city = patches.Circle((x, y), radius=0.25,
                                        facecolor=color, edgecolor='white',
                                        linewidth=2, zorder=6)
                    ax.add_patch(city)
                    dynamic_elements.append(city)

                for a, b in player.roads:
                    x1, y1 = G.nodes[a]['coordinates']
                    x2, y2 = G.nodes[b]['coordinates']
                    road, = ax.plot([x1, x2], [y1, y2], color=color, 
                                  linewidth=3, zorder=4, solid_capstyle='round')
                    dynamic_elements.append(road)

            writer.grab_frame()
            frame_count += 1
            
            if frame_count % 10 == 0:
                print(f"Processed {frame_count} frames...")
            
            if game.game_over:
                print(f"Game over detected at turn {i}")
                break

    print(f"Successfully saved {frame_count} frames to {output}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="dqnCatan.pth")
    parser.add_argument("--out-actions", default="winner_actions.pkl")
    parser.add_argument("--out-video", default="winner.gif")
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    attempt = 0
    while attempt <= 20:
        attempt += 1
        print(f"[Attempt {attempt}] Starting simulation...")
        
        temp_file = f"temp_{attempt}.pkl"
        actions, vps = simulate_and_record(temp_file, model_path=args.model)
        
        max_vp = max(vps.values())
        print(f"[Attempt {attempt}] Simulation complete: VP = {vps}")
        
        if max_vp >= 5:
            print(f"[Attempt {attempt}] Winner found with {max_vp} VP!")
            os.replace(temp_file, args.out_actions)
            playback_and_export(args.out_actions, args.out_video, fps=args.fps)
            break
        else:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
        if attempt == 100:
            print("Maximum attempts reached without finding a winner")
            break

    for f in os.listdir():
        if f.startswith("temp_") and f.endswith(".pkl"):
            os.remove(f)

    print("Simulation complete")
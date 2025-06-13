#!/usr/bin/env python3
import argparse
import torch
import matplotlib.pyplot as plt
from catanboard import generate_board
from game import Game
from player import Player
from environment import CatanEnvironment
from dqn_agent import DQNAgent
from catanboardVisualizer import render_board

def simulate_bots_vs_bots_visual(delay: float = 0.1):
    # 1) Initialize two agents with deterministic policy
    red_agent = DQNAgent(state_dim=10, action_dim=6, epsilon=0.0, epsilon_min=0.0)
    blue_agent = DQNAgent(state_dim=10, action_dim=6, epsilon=0.0, epsilon_min=0.0)
    state_dict = torch.load("dqnCatan.pth")
    red_agent.model.load_state_dict(state_dict)
    blue_agent.model.load_state_dict(state_dict)
    red_agent.model.eval()
    blue_agent.model.eval()

    # 2) Set up game and environment
    tiles, G = generate_board()
    red_player = Player("Red")
    blue_player = Player("Blue")
    game = Game([red_player, blue_player], tiles, G)
    game.visual_mode = True
    env = CatanEnvironment(game)

    # 3) Non-blocking GUI setup
    plt.ion()
    fig, ax = plt.subplots(figsize=(11, 10))
    plt.subplots_adjust(right=0.3)
    render_board(
        G, tiles,
        on_node_click=None,
        game=game,
        fig=fig,
        ax=ax,
        redraw_only=True
    )
    plt.show(block=False)

    # 4) Auto-roll for turn order
    while not game.turn_order_determined:
        env.step("roll")
        render_board(G, tiles, game=game, fig=fig, ax=ax, redraw_only=True)
        plt.pause(delay)

    # 5) Auto-setup for both bots
    while game.setup_phase:
        valid = env.get_valid_actions()
        env.step(valid[0])
        render_board(G, tiles, game=game, fig=fig, ax=ax, redraw_only=True)
        plt.pause(delay)

    # 6) Main game loop with visual updates
    turn_count = 0
    MAX_TURNS = 1000
    while not game.game_over and turn_count < MAX_TURNS:
        current = game.current_player.name
        agent = red_agent if current == "Red" else blue_agent
        valid = env.get_valid_actions()
        state = env.get_state()
        tensor = env.state_to_tensor(state)
        idxs = [env.actions.index(a) for a in valid]
        choice = agent.select_action(tensor, idxs)
        action = env.actions[choice]

        env.step(action)
        render_board(G, tiles, game=game, fig=fig, ax=ax, redraw_only=True)
        plt.pause(delay)
        turn_count += 1

    # 7) End of game: final display
    print("Game Over! ", {p.name: p.victory_points() for p in game.players}, "Winner:", max(game.players, key=lambda p: p.victory_points()).name)
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate two DQN bots playing Catan visually.")
    parser.add_argument("--delay", type=float, default=0.1,
                        help="Pause duration (in seconds) between moves; lower = faster.")
    args = parser.parse_args()
    simulate_bots_vs_bots_visual(delay=args.delay)

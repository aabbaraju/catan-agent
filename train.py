from environment import CatanEnvironment
from dqn_agent import DQNAgent
from player import Player
from game import Game
from catanboard import generate_board
import torch
import matplotlib.pyplot as plt
import numpy as np

tiles, G = generate_board()
game = Game([Player("Red"), Player("Blue")], tiles, G)
env = CatanEnvironment(game)
agent = DQNAgent(state_dim=10, action_dim=6)
rewards_per_episode = []

num_episodes = 100
MAX_TURNS = 500

for episode in range(num_episodes):
    state = env.reset()
    state_tensor = env.state_to_tensor(state)
    done = False
    total_reward = 0
    turn_count = 0

    while not done and turn_count < MAX_TURNS:
        valid = env.get_valid_actions()
        valid_action_indices = [env.actions.index(a) for a in valid]
        action_idx = agent.select_action(state_tensor, valid_action_indices)
        action = env.actions[action_idx]

        print(f"Valid actions for {state['current_player']}: {valid}")
        print(f"[{state['current_player']}] Action chosen: {action} | Resources: {state['resources']} | VP: {state['victory_points']}")

        next_state, reward, done, _ = env.step(action)
        next_state_tensor = env.state_to_tensor(next_state)

        agent.remember(state_tensor, action_idx, reward, next_state_tensor, done)
        agent.replay()

        state = next_state
        state_tensor = next_state_tensor
        total_reward += reward
        turn_count += 1

    print(f"Episode {episode + 1} finished. Total Reward: {total_reward}, Winner: {state['current_player'] if reward > 0 else 'None'}\n")
    rewards_per_episode.append(total_reward)
    if episode % 10 == 0:
        avg = sum(rewards_per_episode[-10:]) / 10
        print(f"Average reward last 10 episodes: {avg:.2f}")

def replay_game(agent, env):
    agent.model.eval()
    state = env.reset()
    state_tensor = env.state_to_tensor(state)
    done = False
    while not done:
        valid = env.get_valid_actions()
        valid_action_indices = [env.actions.index(a) for a in valid]
        action_idx = agent.select_action(state_tensor, valid_action_indices)
        action = env.actions[action_idx]
        print(f"{state['current_player']} chose {action} with resources {state['resources']}")
        state, reward, done, _ = env.step(action)
        state_tensor = env.state_to_tensor(state)
    print("Replay complete.\n")
    agent.model.train()

replay_game(agent, env)

def moving_average(values, window=10):
    return [np.mean(values[max(0, i-window):(i+1)]) for i in range(len(values))]

plt.plot(rewards_per_episode, label='Raw Rewards')
plt.plot(moving_average(rewards_per_episode), label='Smoothed (window=10)', linewidth=2)
plt.xlabel("Episode")
plt.ylabel("Total Reward")
plt.title("DQN Agent Performance Over Time")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

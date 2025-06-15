# Catan-Agent

Using RL to play Settlers of Catan.

---

## Project Overview

An agentic AI system trained to play Settlers of Catan using deep reinforcement learning. Features a full game engine, strategic action selection, and a DQN-trained agent that plays autonomously with support for simulation. Includes visualizations and replay exports.

---

## Features

- Complete Catan game engine with roads, settlements, cities, robber logic, dice rolling, and victory tracking.

- Trains a Deep Q-Network (DQN) agent to play via self-play.

- Modular CatanEnvironment wrapper compatible with custom RL loops.

- Exports GIF or MP4 replays from any simulation.

- Action logging with synchronized visualization and debug printout.

- Supports AI Play for testing and evaluation.

---
## Getting Started
pip install torch matplotlib networkx numpy
python playback.py

### Training your own agent
train.py can be used to run multiple games in self-play mode using environment.py. Use an experience replay buffer and perodically update the Q-network using TD learning. May take tens of thousands of episodes to create a reasonably intelligent player. Performance after 5000 episodes of 500 turns-- 
<img width="475" alt="Screenshot 2025-06-13 222209" src="https://github.com/user-attachments/assets/bccc143c-2683-47c5-8b9b-3deb55a82ef8" />




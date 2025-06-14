import random
from collections import deque

import torch
import torch.nn as nn
import torch.nn.functional as F


class QNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(state_dim, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, action_dim)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


class DQNAgent:
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        epsilon: float = 1.0,
        epsilon_min: float = 0.1,
        epsilon_decay: float = 0.995,
        lr: float = 1e-4,
        gamma: float = 0.99,
        batch_size: int = 64,
        memory_size: int = 10000,
        target_update_every: int = 100,
    ):
        self.epsilon       = epsilon
        self.epsilon_min   = epsilon_min
        self.epsilon_decay = epsilon_decay

        self.gamma        = gamma
        self.batch_size   = batch_size
        self.memory       = deque(maxlen=memory_size)

        self.model        = QNetwork(state_dim, action_dim)
        self.target_model = QNetwork(state_dim, action_dim)
        self.target_model.load_state_dict(self.model.state_dict())
        self.target_model.eval()

        self.optimizer            = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.update_target_every  = target_update_every
        self.step_count           = 0

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return

        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states      = torch.stack(states)             
        next_states = torch.stack(next_states)
        actions     = torch.tensor(actions, dtype=torch.long)   
        rewards     = torch.tensor(rewards, dtype=torch.float32)
        dones       = torch.tensor(dones, dtype=torch.float32)   

        q_vals = self.model(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            next_q = self.target_model(next_states).max(1)[0]
        target = rewards + (1.0 - dones) * self.gamma * next_q

        loss = F.mse_loss(q_vals, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.step_count += 1
        if self.step_count % self.update_target_every == 0:
            self.target_model.load_state_dict(self.model.state_dict())

    def select_action(self, state: torch.Tensor, valid_action_indices):
        if random.random() < self.epsilon:
            choice = random.choice(valid_action_indices)
        else:
            with torch.no_grad():
                q_values = self.model(state.unsqueeze(0)).squeeze(0)
            mask = torch.full_like(q_values, -float('inf'))
            for idx in valid_action_indices:
                mask[idx] = q_values[idx]
            choice = torch.argmax(mask).item()

        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        return choice

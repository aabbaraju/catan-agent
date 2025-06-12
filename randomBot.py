import random

class RandomBot:
    def select_action(self, state, valid_actions):
        return random.choice(valid_actions)
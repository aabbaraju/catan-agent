from environment import CatanEnvironment
from randomBot import RandomBot
from catanboard import tiles, G
from player import Player
from game import Game

p1, p2 = Player("Red"), Player("Blue")
game = Game([p1, p2], tiles, G)
env = CatanEnvironment(game)

bot1 = RandomBot()
bot2 = RandomBot()

for _ in range(100): 
    state = env.get_state()
    valid = env.get_valid_actions()
    bot = bot1 if state['current_player'] == 'Red' else bot2
    action = bot.select_action(state, valid)
    print(f"{state['current_player']} chose: {action}")
    state, done = env.step(action)
    if done:
        print("Game over")
        break
from catanboard import tiles, G
from player import Player
from game import Game
from catanboardVisualizer import render_board
import matplotlib.pyplot as plt

player1 = Player("Red")
player2 = Player("Blue")
game = Game([player1, player2], tiles, G)
game.visual_mode = True

fig, ax = plt.subplots(figsize=(10, 8))
render_board(G, tiles, on_node_click=game.handle_node_click, game=game, fig=fig, ax=ax)

plt.show()

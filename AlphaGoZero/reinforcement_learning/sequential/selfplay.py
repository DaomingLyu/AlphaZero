import os
import numpy as np
from AlphaGoZero.game.nn_eval import NNEvaluator
from AlphaGoZero.game.gameplay import Game


def selfplay(best_player_name, base_dir='data', num_games=25000):
    """ Generate self play data and search probabilities. 
        Results are stored in data/selfplay/<best_player_name>/
        Game records are stored as sgf files.
        Search probabilities are stored as pickle files.

    Args:
        best_player_name: the name of the best player
        num_games: number of games to play

    Returns:
        None

    """
    best_player = NNEvaluator(os.path.join(base_dir, 'models', best_player_name))
    # This can be parallelized
    match = Game(best_player, best_player)
    state_dataset = np.zeros((0, 17, 19, 19))
    probs_dataset = np.zeros((0, 362))
    result_dataset = np.zeros(0)

    for num_game in range(num_games):
        # TODO: indicate this is a selfplay, not yet implemented in gameplay.Game
        result = match.start()
        state_np, probs_np, result_np = match.get_history()
        state_dataset = np.concatenate([state_dataset, state_np])
        probs_dataset = np.concatenate([probs_dataset, probs_np])
        result_dataset = np.concatenate([result_dataset, result_np])

        # TODO: auto resignation should be implemented
    with open(os.path.join(base_dir, 'selfplay', best_player_name, 'train.npy'), 'wb+') as f:
        np.save(f, (state_dataset, probs_dataset, result_dataset))
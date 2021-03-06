from copy import deepcopy

import numpy as np
import yaml
import os

WHITE = -1
BLACK = +1
PASS_MOVE = None
EMPTY = 0

with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'mnk.yaml')) as f:
    game_config = yaml.load(f)


class GameState(object):
    """ Game state of mnk Game.

    """

    def __init__(self, history_length=8):
        self.width = game_config['board_width']
        self.height = game_config['board_height']
        self.k = game_config['k']
        self.board = np.zeros((self.height, self.width), dtype=int)
        self.board.fill(EMPTY)
        self.current_player = BLACK
        self.history = []
        # Keeps 8 history board for fast feature extraction
        # Fill zeros for non-existing histories
        # board_history does not include the current board while the feature does,
        self.history_length = history_length
        self.board_history = [np.zeros((self.height, self.width), dtype=int) for _ in range(history_length - 1)]
        self.is_end_of_game = False
        self.winner = None
        self.turns = 0

    def _on_board(self, position):
        """

        Args:
            position: a tuple of (x, y)

        Returns:
            bool: returns True iff position is within the bounds of [0, self.size)
        """
        (x, y) = position
        return x >= 0 and y >= 0 and x < self.height and y < self.width

    def copy(self):
        """Gets a copy of this Game state

        Returns:
            AlphaZero.env.mnk.GameState: a copy of this Game state
        """
        other = GameState()
        other.board = self.board.copy()
        other.current_player = self.current_player
        other.history = list(self.history)
        other.board_history = deepcopy(self.board_history)
        other.turns = self.turns
        other.is_end_of_game = self.is_end_of_game
        other.winner = self.winner
        return other

    def is_legal(self, action):
        """
        Determines if the given action (x,y) is a legal move
        Args:
            action: a tuple of (x, y)

        Returns:
            bool: if the move is legal.
        """
        (x, y) = action
        if not self._on_board(action):
            return False
        if self.board[x][y] != EMPTY:
            return False
        return True

    def get_legal_moves(self):
        """

        Returns:
            list: a list of legal moves.
        """
        legal_moves = [(i, j) for i in range(self.height) for j in range(self.width) if self.is_legal((i, j))]
        return legal_moves

    def get_winner(self):
        """

        Returns: The winner, None if the game is not ended yet

        """
        return self.winner

    def do_move(self, action, color=None):
        """Play stone at action=(x,y). If color is not specified, current_player is used
        If it is a legal move, current_player switches to the opposite color
        If not, an IllegalMove exception is raised

        Args:
            action: a tuple of (x, y)
            color: the color of the move

        Returns:
            bool: if it is the end of game.
        """
        color = color or self.current_player
        reset_player = self.current_player
        self.current_player = color
        if self.is_legal(action):
            # save current board to history before it is modified
            self.board_history.append(self.board.copy())
            self.board_history.pop(0)
            self.history.append(action)

            # do action
            (x, y) = action
            self.board[x][y] = color
            self.turns += 1

            # check if the current player wins by the move
            # check horizontal
            h_count, v_count, diag1_count, diag2_count = 1, 1, 1, 1
            xp, yp = x + 1, y
            while self._on_board((xp, yp)) and self.board[xp][yp] == self.current_player:
                xp += 1
                h_count += 1
            xp, yp = x - 1, y
            while self._on_board((xp, yp)) and self.board[xp][yp] == self.current_player:
                xp -= 1
                h_count += 1
            # check vertical
            xp, yp = x, y + 1
            while self._on_board((xp, yp)) and self.board[xp][yp] == self.current_player:
                yp += 1
                v_count += 1
            xp, yp = x, y - 1
            while self._on_board((xp, yp)) and self.board[xp][yp] == self.current_player:
                yp -= 1
                v_count += 1
            # check diagonal 1 \
            xp, yp = x + 1, y + 1
            while self._on_board((xp, yp)) and self.board[xp][yp] == self.current_player:
                xp += 1
                yp += 1
                diag1_count += 1
            xp, yp = x - 1, y - 1
            while self._on_board((xp, yp)) and self.board[xp][yp] == self.current_player:
                xp -= 1
                yp -= 1
                diag1_count += 1
            # check diagonal 2 /
            xp, yp = x + 1, y - 1
            while self._on_board((xp, yp)) and self.board[xp][yp] == self.current_player:
                xp += 1
                yp -= 1
                diag2_count += 1
            xp, yp = x - 1, y + 1
            while self._on_board((xp, yp)) and self.board[xp][yp] == self.current_player:
                xp -= 1
                yp += 1
                diag2_count += 1

            # winning condition
            if h_count >= self.k or v_count >= self.k or diag1_count >= self.k or diag2_count >= self.k:
                self.is_end_of_game = True
                self.winner = self.current_player

            # check if stone has filled the board if no one wins yet
            elif self.turns == self.height * self.width:
                self.is_end_of_game = True
                self.winner = 0

            # next turn
            self.current_player = -color

        else:
            self.current_player = reset_player
            raise IllegalMove(str(action))

        return self.is_end_of_game

    def transform(self, transform_id):
        """Transform the current board and the history boards according to D(4).
            Caution: self.history (action history) is not modified, thus this function
            should ONLY be used for state evaluation.

        Args:
            transform_id: integer in range [0, 7]

        Returns:
            None

        """
        assert self.height == self.width

        def _transform(b):
            # Performs reflection
            if transform_id // 4 == 1:
                b = np.fliplr(b)
            # Performs rotation
            b = np.rot90(b, transform_id % 4)
            return b

        # List of boards to transform
        self.board = _transform(self.board)
        self.board_history = [_transform(b) for b in self.board_history]


class IllegalMove(Exception):
    pass

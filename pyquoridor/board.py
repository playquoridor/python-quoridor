from pyquoridor.pawn import Pawn
from pyquoridor.utils import BoolGrid
from pyquoridor.square import *
from pyquoridor.exceptions import *
from collections import deque


class Board:
    def __init__(self):
        # Set up board
        self.board = [[Square(row, col) for col in range(MAX_COL)] for row in
                      range(MAX_ROW)]

        # Place neighbours
        for row in range(MAX_ROW):
            for col in range(MAX_COL):
                left_square = self.get_square_or_none(row, col - 1)
                right_square = self.get_square_or_none(row, col + 1)
                up_square = self.get_square_or_none(row + 1, col)
                down_square = self.get_square_or_none(row - 1, col)
                neighbours = {s for s in [up_square, right_square, down_square, left_square] if s is not None}
                self[(row, col)].set_physical_neighbours(neighbours)
                self[(row, col)].add_neighbours(neighbours)

        # Initialise fences. These are utilised to check whether fences exist
        self.horizontal_fence_grid = BoolGrid(MAX_ROW, MAX_COL)
        self.vertical_fence_grid = BoolGrid(MAX_ROW, MAX_COL)
        self.fence_center_grid = BoolGrid(MAX_ROW, MAX_COL)

        # Initialise pawns
        self.pawns = {'white': Pawn(square=self[(WHITE_INIT_ROW, WHITE_INIT_COL)], color='white'),
                      # WHITE_INIT_ROW, WHITE_INIT_COL
                      'black': Pawn(square=self[(BLACK_INIT_ROW, BLACK_INIT_COL)],
                                    color='black')}  # BLACK_INIT_ROW, BLACK_INIT_COL

        # Update possible moves based on initial pawn positions
        self.update_neighbours(self.black_pawn.square)
        self.update_neighbours(self.white_pawn.square)

        # Initialise grids indicating whether there is a path for every player
        self.path_exists = {}
        for player in self.pawns.keys():
            self.path_exists[player] = BoolGrid(MAX_ROW, MAX_COL, init_value=True)

    @property
    def white_pawn(self):
        return self.pawns['white']

    @property
    def black_pawn(self):
        return self.pawns['black']

    def check_winner(self):
        for player, pawn in self.pawns.items():
            if pawn.square.winning_square(player):
                raise GameOver(player, last_move=False, message=f'Player {player} wins the game')

    def game_finished(self):
        try:
            self.check_winner()
            return False
        except GameOver:
            return True

    def partial_FEN(self):
        """
        Format: [1] / [2] / [3.1] [3.2] [3.3*] [3.4*] / [4.1] [4.2] [4.3*] [4.4*] / [5]
        1. Horizontal wall positions
        2. Vertical wall positions
        3. Pawn positions:
            3.1 Player 1 pawn position
            3.2 Player 2 pawn position
            3.3 Player 3 pawn position*
            3.4 Player 4 pawn position*
        4. Walls available: (not included here)
            4.1 player 1 walls available
            4.2 player 2 walls available
            4.3 player 3 walls available*
            4.4 player 4 walls available*
        5. Active player (not included here)
        * Four player only.
        """
        # Walls
        vertical_fences = sorted(self.vertical_fence_grid.argwhere_str())
        horizontal_fences = sorted(self.horizontal_fence_grid.argwhere_str(), key=lambda x: x[1])
        # Remove even positions in lists -- only first coordinate is used in the FEN
        del vertical_fences[1::2]
        del horizontal_fences[1::2]

        # Pawn positions and walls available
        white_position = self.pawns['white'].square.square2str()
        black_position = self.pawns['black'].square.square2str()
        pawn_positions = white_position + black_position

        # Construct FEN
        fen = f'{"".join(sorted(horizontal_fences))}/{"".join(sorted(vertical_fences))}/{pawn_positions}'
        return fen

    def from_FEN(self, FEN):
        raise NotImplementedError('From FEN not implemented')

    def __getitem__(self, location):
        row, col = location
        # Check whether new square is valid
        if not Square.valid_square(row, col):
            raise InvalidSquare(f'Invalid square ({row}, {col})')

        return self.board[row][col]

    def get_square_or_none(self, row, col):
        try:
            square = self[(row, col)]
        except InvalidSquare:
            square = None
        return square

    def legal_moves(self):
        raise NotImplementedError()

    def fence_exists(self, row, col, orientation):
        if orientation == 'v':
            return self.vertical_fence_grid[(row, col)] \
                   or self.vertical_fence_grid[(row + 1, col)] \
                   or self.fence_center_grid[(row, col)]
        return self.horizontal_fence_grid[(row, col)] \
               or self.horizontal_fence_grid[(row, col + 1)] \
               or self.fence_center_grid[(row, col)]

    def _set_pawn_location(self, player, target_row, target_col):
        target_square = self[(target_row, target_col)]
        self.pawns[player].move(target_square)

        # Reset neighbours of all pawns
        for pawn in self.pawns.values():
            pawn.square.reset_neighbours()

        # Update neighbours of all pawns
        for pawn in self.pawns.values():
            self.update_neighbours(pawn.square)

    def _add_or_remove_neighbours(self, source_row, source_col, target_row, target_col, add):
        """
        Removes mutual neighbours (source, target) in neighbours and physical neighbours
        """
        source_square = self.get_square_or_none(source_row, source_col)
        target_square = self.get_square_or_none(target_row, target_col)
        if source_square is not None and target_square is not None:
            source_square.add_or_remove_neighbours(target_square, add=add)
            target_square.add_or_remove_neighbours(source_square, add=add)
            source_square.add_or_remove_physical_neighbours(target_square, add=add)
            target_square.add_or_remove_physical_neighbours(source_square, add=add)

    def _remove_diagonal_neighbours(self, square):
        """
        Removes mutual neighbours (source, target) in neighbours and physical neighbours
        """
        self._add_or_remove_neighbours(square.row, square.col, square.row + 1, square.col - 1, add=False)
        self._add_or_remove_neighbours(square.row, square.col, square.row + 1, square.col + 1, add=False)
        self._add_or_remove_neighbours(square.row, square.col, square.row - 1, square.col - 1, add=False)
        self._add_or_remove_neighbours(square.row, square.col, square.row - 1, square.col + 1, add=False)

    def _pawn_conditional_remove_neighbours(self, source_row, source_col,
                                            target_row, target_col,
                                            cond_row, cond_col):
        """
        Adds or removes a particular neighbourhood connection between source and target only if there is a pawn
        in the cond square.
        """
        target_square = self.get_square_or_none(target_row, target_col)
        cond_square = self.get_square_or_none(cond_row, cond_col)
        if target_square is not None and cond_square is not None and not cond_square.has_pawn():
            self._add_or_remove_neighbours(source_row, source_col, target_row, target_col, add=False)

    def _place_or_remove_fence(self, row, col, orientation, place=True):
        """
        Places or removes a fence and updates the square neighbourhoods accordingly.
        """
        # Assumes valid fence
        if orientation == 'h':
            self._add_or_remove_neighbours(row, col, row + 1, col, add=not place)
            self._add_or_remove_neighbours(row, col + 1, row + 1, col + 1, add=not place)

            # Remove distant straight neighbours (pawn in between)
            if place:
                self._add_or_remove_neighbours(row, col, row + 2, col, add=False)
                self._add_or_remove_neighbours(row, col + 1, row + 2, col + 1, add=False)
                self._add_or_remove_neighbours(row + 1, col, row - 1, col, add=False)
                self._add_or_remove_neighbours(row + 1, col + 1, row - 1, col + 1, add=False)

                # Remove distant diagonal neighbours (pawn in between)
                self._pawn_conditional_remove_neighbours(row, col, row + 1, col - 1, row, col - 1)
                self._pawn_conditional_remove_neighbours(row + 1, col, row, col - 1, row + 1, col - 1)
                self._pawn_conditional_remove_neighbours(row, col + 1, row + 1, col + 2, row, col + 2)
                self._pawn_conditional_remove_neighbours(row + 1, col + 1, row, col + 2, row + 1, col + 2)
                self._add_or_remove_neighbours(row, col + 1, row + 1, col, add=False)
                self._add_or_remove_neighbours(row + 1, col + 1, row, col, add=False)

            # Place fence
            self.horizontal_fence_grid[(row, col)] = place
            self.horizontal_fence_grid[(row, col + 1)] = place
            self.fence_center_grid[(row, col)] = place

        else:  # Vertical fence
            self._add_or_remove_neighbours(row, col, row, col + 1, add=not place)
            self._add_or_remove_neighbours(row + 1, col, row + 1, col + 1, add=not place)

            if place:
                # Remove distant straight neighbours (pawn in between)
                self._add_or_remove_neighbours(row, col, row, col + 2, add=False)
                self._add_or_remove_neighbours(row + 1, col, row + 1, col + 2, add=False)
                self._add_or_remove_neighbours(row, col + 1, row, col - 1, add=False)
                self._add_or_remove_neighbours(row + 1, col + 1, row + 1, col - 1, add=False)

                # Remove distant diagonal neighbours (pawn in between)
                self._pawn_conditional_remove_neighbours(row - 1, col, row, col + 1, row - 1, col + 1)
                self._pawn_conditional_remove_neighbours(row - 1, col + 1, row, col, row - 1, col)
                self._pawn_conditional_remove_neighbours(row + 1, col, row + 2, col + 1, row + 2, col)
                self._pawn_conditional_remove_neighbours(row + 1, col + 1, row + 2, col, row + 2, col + 1)
                self._add_or_remove_neighbours(row + 1, col, row, col + 1, add=not place)
                self._add_or_remove_neighbours(row, col, row + 1, col + 1, add=not place)

            # Place fence
            self.vertical_fence_grid[(row, col)] = place
            self.vertical_fence_grid[(row + 1, col)] = place
            self.fence_center_grid[(row, col)] = place

        # Update connections of all pawns (accounts for straight and diagonal jumps)
        for _, pawn in self.pawns.items():
            self.update_neighbours(pawn.square)

    def BFS_all(self, player):
        """
        Breadth-first search from end squares to all squares in the board.
        """
        path_exists = BoolGrid(MAX_ROW, MAX_COL, init_value=False)
        visited_squares = BoolGrid(MAX_ROW, MAX_COL, init_value=False)
        square_queue = deque()

        # Set end row according to player
        end_row = 0
        if player == 'white':
            end_row = MAX_ROW - 1

        # Initialise paths, visited squares and queue
        for i in range(MAX_COL):
            path_exists[(end_row, i)] = True
            visited_squares[(end_row, i)] = True
            square_queue.append(self[(end_row, i)])

        # Keep popping neighbours until the queue is empty. All remaining unvisited squares have no path to the goal
        while len(square_queue) != 0:
            square = square_queue.popleft()
            for neighbour in square.neighbours_iter():
                row = neighbour.row
                col = neighbour.col
                if not visited_squares[(row, col)]:
                    path_exists[(row, col)] = True
                    square_queue.append(neighbour)
                    visited_squares[(row, col)] = True

        return path_exists

    def BFS_player(self, player):
        """
        Breadth-first search from player pawn square.
        """
        visited_squares = BoolGrid(MAX_ROW, MAX_COL, init_value=False)
        square_queue = deque()

        # Set end row according to player
        end_row = 0
        if player == 'white':
            end_row = MAX_ROW - 1

        # Initialise paths, visited squares and queue
        pawn_square = self.pawns[player].square
        visited_squares[(pawn_square.row, pawn_square.col)] = True
        square_queue.append(pawn_square)

        # Keep popping neighbours until the queue is empty. All remaining unvisited squares have no path to the goal
        can_reach = False
        while len(square_queue) != 0 and not can_reach:
            square = square_queue.popleft()
            for neighbour in square.neighbours_iter():
                row = neighbour.row
                col = neighbour.col
                if row == end_row:
                    can_reach = True
                    break
                if not visited_squares[(row, col)]:
                    square_queue.append(neighbour)
                    visited_squares[(row, col)] = True

        return can_reach

    def place_fence(self, row, col, orientation, check_winner=True, run_BFS=True):
        """
        Places a fence or raises InvalidFence exception if the fence is invalid.
        """
        if check_winner:
            self.check_winner()

        # Check if neighbouring squares are valid
        try:
            squares = [self[row, col],
                       self[row + 1, col],
                       self[row, col + 1],
                       self[row + 1, col + 1]]
        except InvalidSquare:
            raise InvalidFence(f'Invalid fence ({row}, {col}): Fence out of bounds')

        # Check if fence position is occupied
        invalid = self.fence_exists(row, col, orientation)
        if invalid:
            raise InvalidFence(f'Invalid fence ({row}, {col}): Fence overlap')

        # Place fence temporarily
        self._place_or_remove_fence(row, col, orientation, place=True)

        # Check that path exists for all pawns
        valid_fence = True
        if run_BFS:  # In some cases where BFS has been ran in another process, we don't want to repeat
            for player in self.pawns.keys():
                valid_fence = self.BFS_player(player)
                if not valid_fence:
                    break

        # Undo the fence if one of the players can't reach the end
        if not valid_fence:
            self._place_or_remove_fence(row, col, orientation, place=False)
            raise InvalidFence(f'Invalid fence ({row}, {col}): Fence blocks {player} pawn path')

    def _add_diagonal_skip_neighbours(self, square, next_square, orientation='h'):
        """
        When straight skip connection is not possible, adds skip diagonal connections (neighbours of square)
        to next_square
        """
        if square is not None and next_square is not None and \
                square.has_pawn() and next_square.has_neighbour(square):
            row = square.row
            col = square.col
            diff_row = 0
            diff_col = 1
            if orientation == 'v':
                diff_row = 1
                diff_col = 0

            # Add diagonal skip neighbours to next_square
            neighbour_1 = self.get_square_or_none(row + diff_row, col + diff_col)
            neighbour_2 = self.get_square_or_none(row - diff_row, col - diff_col)
            if neighbour_1 is not None and square.has_neighbour(neighbour_1):
                next_square.add_neighbours(neighbour_1)
            if neighbour_2 is not None and square.has_neighbour(neighbour_2):
                next_square.add_neighbours(neighbour_2)

    def update_neighbours(self, target_square):
        """
        Updates neighbours of a target square occupied by a pawn
        :param target_square: target square for which to update neighbours
        :return squares of neighbour squares occupied by pawns
        """
        occupied_squares = []

        # Update neighbours of final square
        for square in target_square.physical_neighbours_iter():
            # Increasing neighbourhood radius
            if square.has_pawn():  # square.is_neighbour(target_square) and
                occupied_squares.append(square)

                # Make jump connections
                diff_row = square.row - target_square.row
                diff_col = square.col - target_square.col
                next_square = self.get_square_or_none(square.row + diff_row, square.col + diff_col)

                # No fence behind pawn
                if next_square is not None and square.has_neighbour(next_square):
                    target_square.add_neighbours(next_square)
                    # square.add_neighbours(source_square)
                else:  # Fence behind the pawn. Get two other neighbours
                    self._add_diagonal_skip_neighbours(square=square,
                                                       next_square=target_square,
                                                       orientation='h')
                    self._add_diagonal_skip_neighbours(square=square,
                                                       next_square=target_square,
                                                       orientation='v')
        return occupied_squares

    def move_pawn(self, player, target_row, target_col, check_winner=True):
        """
        Moves a pawn or raises InvalidMove exception if the move is invalid.
        """
        if check_winner:
            self.check_winner()

        pawn = self.pawns[player]
        source_square = pawn.square
        target_square = self[(target_row, target_col)]
        if target_square.has_pawn() or not source_square.has_neighbour(target_square):
            raise InvalidMove(f'Cannot move {player} pawn to square ({target_row}, {target_col})')

        # Execute transaction: Move pawn
        pawn.move(target_square)

        # Check if game is over
        if target_square.winning_square(player=player):
            raise GameOver(player, last_move=True, message=f'Player {player} wins the game')

        # Remove diagonal neighbours of final square
        # self._remove_diagonal_neighbours(target_square)

        # Reset neighbours of all pawns
        for pawn in self.pawns.values():
            pawn.square.reset_neighbours()

        # Update neighbours of all pawns
        for pawn in self.pawns.values():
            self.update_neighbours(pawn.square)

    def valid_pawn_moves(self, player, check_winner=True):
        """
        Returns a list of valid move squares of a pawn.
        """
        if check_winner:
            self.check_winner()

        pawn = self.pawns[player]
        # return pawn.square.neighbours
        return {s for s in pawn.square.neighbours if not s.has_pawn()}

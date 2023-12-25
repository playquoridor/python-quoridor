import unittest
from utils import print_board
from exceptions import *
from board_setups import *


class BoardIntegrity(unittest.TestCase):
    def test_invalid_fences(self):
        # Board set up
        board = board_setup1()

        # Overlapping horizontal fences
        with self.assertRaises(InvalidFence):
            board.place_fence(row=1, col=0, orientation='h')

        # Overlapping vertical fences
        with self.assertRaises(InvalidFence):
            board.place_fence(row=3, col=2, orientation='h')

        # Horizontal fence out of board
        with self.assertRaises(InvalidFence):
            board.place_fence(row=8, col=1, orientation='h')

        # Vertical fence out of board
        with self.assertRaises(InvalidFence):
            board.place_fence(row=2, col=8, orientation='v')

        # Horizontal fence on edge of the board
        with self.assertRaises(InvalidFence):
            board.place_fence(row=4, col=8, orientation='h')

        # Vertical fence on edge of the board
        with self.assertRaises(InvalidFence):
            board.place_fence(row=8, col=4, orientation='v')

        # Vertical edge crossing horizontal edge
        with self.assertRaises(InvalidFence):
            board.place_fence(row=0, col=0, orientation='v')

        # Horizontal edge crossing vertical edge
        with self.assertRaises(InvalidFence):
            board.place_fence(row=3, col=2, orientation='h')

    def test_invalid_moves(self):
        # Board set up
        board = board_setup1()

        # Fence down
        board.place_fence(row=2, col=4, orientation='h')
        with self.assertRaises(InvalidMove):
            board.move_pawn(player='white', target_row=2, target_col=4)

        board.move_pawn(player='white', target_row=4, target_col=4)
        board.move_pawn(player='white', target_row=6, target_col=4)

        # Fence left
        board.place_fence(row=5, col=3, orientation='v')
        with self.assertRaises(InvalidMove):
            board.move_pawn(player='white', target_row=6, target_col=3)

        # Fence up
        board.place_fence(row=6, col=4, orientation='h')
        with self.assertRaises(InvalidMove):
            board.move_pawn(player='white', target_row=7, target_col=4)

        # Fence right
        board.place_fence(row=5, col=4, orientation='v')
        with self.assertRaises(InvalidMove):
            board.move_pawn(player='white', target_row=6, target_col=5)

    def test_invalid_jump_moves(self):
        # Board set up
        board = board_setup1()
        board.move_pawn(player='black', target_row=4, target_col=4)
        board.move_pawn(player='black', target_row=2, target_col=4)
        board.move_pawn(player='black', target_row=2, target_col=3)
        board.move_pawn(player='white', target_row=3, target_col=3)
        board.move_pawn(player='white', target_row=4, target_col=3)
        # board.update_neighbours(board.black_pawn.square)
        # board.update_neighbours(board.white_pawn.square)

        # Move pawns
        board.move_pawn(player='white', target_row=3, target_col=3)
        board.move_pawn(player='white', target_row=1, target_col=3)
        with self.assertRaises(GameOver):
            board.move_pawn(player='black', target_row=0, target_col=3)

        # White pawn cannot jump over black pawn - fence in the middle
        board.place_fence(row=1, col=2, orientation='h', check_winner=False)
        with self.assertRaises(InvalidMove):
            board.move_pawn(player='black', target_row=2, target_col=3, check_winner=False)

        # Black pawn moves diagonally
        board.move_pawn(player='black', target_row=1, target_col=2, check_winner=False)

        # White pawn jumps black pawn
        board.move_pawn(player='white', target_row=1, target_col=1)

        # Black pawn straight jumps white pawn
        with self.assertRaises(InvalidMove):
            board.move_pawn(player='black', target_row=1, target_col=0)

        # Black pawn moves diagonally
        board.move_pawn(player='black', target_row=2, target_col=1)

        # White pawn tries to jump diagonally
        with self.assertRaises(InvalidMove):
            board.move_pawn(player='white', target_row=2, target_col=2)

        # White pawn jumps straight
        board.move_pawn(player='white', target_row=3, target_col=1)

        # Black pawn jumps diagonally
        board.place_fence(row=3, col=1, orientation='h')
        board.move_pawn(player='black', target_row=3, target_col=2)

        # White pawn jumps diagonally
        board.move_pawn(player='white', target_row=2, target_col=2)

        # Black pawn jumps diagonally
        board.move_pawn(player='black', target_row=2, target_col=3)
        # print_board(board)

    def test_more_invalid_moves(self):
        # Board set up
        board = Board()
        board._set_pawn_location('white', target_row=3, target_col=4)
        board._set_pawn_location('black', target_row=5, target_col=4)
        board.move_pawn(player='white', target_row=4, target_col=4)

        # White pawn can jump black. Move black pawn so that it's no longer possible
        board.move_pawn(player='black', target_row=5, target_col=5)
        with self.assertRaises(InvalidMove):
            board.move_pawn(player='white', target_row=6, target_col=4)

    def test_path_exists(self):
        # Board set up
        board = board_setup1()
        board.update_neighbours(board.black_pawn.square)
        board.update_neighbours(board.white_pawn.square)

        # Place fences to block path for black pawn
        board.place_fence(row=2, col=1, orientation='h')
        board.place_fence(row=2, col=3, orientation='h')
        board.place_fence(row=2, col=5, orientation='h')

        # Fence blocks black pawn's path
        with self.assertRaises(InvalidFence):
            board.place_fence(row=2, col=7, orientation='h')

        # Move pawn white upwards and place a fence that blocks white's path
        board.move_pawn(player='white', target_row=4, target_col=4)
        board.place_fence(row=5, col=2, orientation='v')
        board.place_fence(row=5, col=5, orientation='h')
        board.place_fence(row=5, col=7, orientation='h')

        # Fence blocks white pawn's path
        with self.assertRaises(InvalidFence):
            board.place_fence(row=5, col=3, orientation='h')

        # Check that the fence is undone properly, i.e. white pawn can jump over black
        board.move_pawn(player='white', target_row=6, target_col=4)
        board.move_pawn(player='white', target_row=4, target_col=4)
        board.move_pawn(player='white', target_row=4, target_col=5)
        board.move_pawn(player='white', target_row=5, target_col=5)

        # Check that we can put vertical fence that doesn't block the path
        board.place_fence(row=4, col=3, orientation='v')

        # Check that we can jump diagonally with white pawn
        board.move_pawn(player='white', target_row=6, target_col=4)

        # Check that we can now put the fence that separates white and black pawns
        board.place_fence(row=5, col=3, orientation='h')
        # print_board(board, player_path_check='black')

    def test_path_exists_2(self):
        # Board set up
        board = Board()

        # Place fences to block path for black pawn
        board.place_fence(row=5, col=0, orientation='h')
        board.place_fence(row=5, col=2, orientation='h')
        board.place_fence(row=5, col=4, orientation='h')
        board.place_fence(row=5, col=6, orientation='h')
        board.place_fence(row=5, col=7, orientation='v')
        # print_board(board, player_path_check='white')

        # Fence blocks black pawn's path
        with self.assertRaises(InvalidFence):
            board.place_fence(row=6, col=7, orientation='h')

        # Fence blocks black pawn's path
        with self.assertRaises(InvalidFence):
            # print([(s.row, s.col) for s in board[(5, 7)].neighbours])
            board.place_fence(row=4, col=7, orientation='h')
            # print_board(board, player_path_check='white')
        # print([(s.row, s.col) for s in board[(5, 7)].neighbours])
        # print([(s.row, s.col) for s in board[(4, 4)].neighbours])

        with self.assertRaises(InvalidFence):
            board.place_fence(row=4, col=7, orientation='h')

        print_board(board, player_path_check='white')
        # print(board.partial_FEN())


if __name__ == '__main__':
    unittest.main()

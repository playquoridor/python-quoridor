from board_setups import *
from utils import print_board


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    board = Board()

    board.place_fence(row=0, col=0, orientation='h')
    board.place_fence(row=7, col=0, orientation='h')
    board.place_fence(row=3, col=2, orientation='v')
    board.place_fence(row=1, col=0, orientation='v')

    print()
    board._set_pawn_location('white', target_row=3, target_col=4)
    board._set_pawn_location('black', target_row=5, target_col=4)
    print_board(board)
    board.move_pawn(player='white', target_row=1, target_col=4)
    print_board(board)



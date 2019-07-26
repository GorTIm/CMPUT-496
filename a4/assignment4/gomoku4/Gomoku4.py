#!/usr/bin/env python
#/usr/local/bin/python3
# Set the path to your python3 above

current_color = 1
from math import pow, sqrt
from timeit import default_timer as timer
from gtp_connection import GtpConnection, point_to_coord
from board_util import GoBoardUtil, EMPTY, coord_to_point
from simple_board import SimpleGoBoard

import random
import numpy as np

def undo(board,move):
    board.board[move]=EMPTY
    board.current_player=GoBoardUtil.opponent(board.current_player)

def play_move(board, move, color):
    board.play_move_gomoku(move, color)

def game_result(board):
    game_end, winner = board.check_game_end_gomoku()
    moves = board.get_empty_points()
    board_full = (len(moves) == 0)
    if game_end:
        #return 1 if winner == board.current_player else -1
        return winner
    if board_full:
        return 'draw'
    return None

class GomokuSimulationPlayer(object):
    """
    For each move do `n_simualtions_per_move` playouts,
    then select the one with best win-rate.
    playout could be either random or rule_based (i.e., uses pre-defined patterns) 
    """
    def __init__(self, n_simualtions_per_move=5, playout_policy='rule_based', board_size=7):
        assert(playout_policy in ['random', 'rule_based'])
        self.n_simualtions_per_move=n_simualtions_per_move
        self.board_size=board_size
        self.playout_policy=playout_policy

        #NOTE: pattern has preference, later pattern is ignored if an earlier pattern is found
        self.pattern_list=['Win', 'BlockWin', 'OpenFour', 'BlockOpenFour', 'Random']

        self.name="Gomoku3"
        self.version = 3.0
        self.best_move=None
    
    def set_playout_policy(self, playout_policy='rule_based'):
        assert(playout_policy in ['random', 'rule_based'])
        self.playout_policy=playout_policy

    # def _random_moves(self, board, color_to_play):
    #     return GoBoardUtil.generate_legal_moves_gomoku(board)

    def _random_moves(self, board, color_to_play):
        global current_color

        legal_moves = GoBoardUtil.generate_legal_moves_gomoku(board)

        opponent_color_old_moves = GoBoardUtil.find_old_moves_gomoku(board, GoBoardUtil.opponent(current_color))
        player_color_old_moves = GoBoardUtil.find_old_moves_gomoku(board, current_color)
        
        legal_moves_2d = []
        player_color_old_moves_2d = []
        opponent_color_old_moves_2d = []

        # create 2d lists
        for i in legal_moves:
            legal_moves_2d.append(point_to_coord(i, board.size))
        for i in player_color_old_moves:
            player_color_old_moves_2d.append(point_to_coord(i, board.size))
        for i in opponent_color_old_moves:
            opponent_color_old_moves_2d.append(point_to_coord(i, board.size))

        possible_moves = []
        hit_three_moves = []
        start_moves = []

        # calculate triangle attack case
        for i in player_color_old_moves_2d:
            candidates = [[(i[0]-1, i[1]-1), (i[0]-1, i[1]), (i[0]-1, i[1]+1)],\
                [(i[0]-1, i[1]-1), (i[0], i[1]-1), (i[0]+1, i[1]-1)],\
                [(i[0]+1, i[1]-1), (i[0]+1, i[1]), (i[0]+1, i[1]+1)],\
                [(i[0]-1, i[1]+1), (i[0], i[1]+1), (i[0]+1, i[1]+1)]]

            for j in candidates:
                if  (j[0] in player_color_old_moves_2d) and \
                    (j[1] not in opponent_color_old_moves_2d) and \
                    (j[2] in legal_moves_2d):
                    possible_moves.append(j[2])

                if  (j[2] in player_color_old_moves_2d) and \
                    (j[1] not in opponent_color_old_moves_2d) and \
                    (j[0] in legal_moves_2d):
                    possible_moves.append(j[0])

        # calculate the hit three case
        # case 1 for a exist move
        for i in player_color_old_moves_2d:
            candidates = [[(i[0]-1, i[1]-1), (i[0]+1, i[1]+1)],\
                [(i[0]-1, i[1]+1), (i[0]+1, i[1]-1)],  [(i[0]-1, i[1]), (i[0]+1, i[1])], \
                [(i[0], i[1]-1), (i[0], i[1]+1)]]

            for j in candidates:
                if (j[0] in player_color_old_moves_2d) and (j[1] in legal_moves_2d):
                    hit_three_moves.append(j[1])
                if (j[0] in legal_moves_2d) and (j[1] in player_color_old_moves_2d):
                    hit_three_moves.append(j[0])

        # case 2 for a legal move
        for i in legal_moves_2d:
            candidates = [[(i[0]-1, i[1]-1), (i[0]+1, i[1]+1)],\
                [(i[0]-1, i[1]+1), (i[0]+1, i[1]-1)],  [(i[0]-1, i[1]), (i[0]+1, i[1])], \
                [(i[0], i[1]-1), (i[0], i[1]+1)]]

            for j in candidates:
                if (j[0] in player_color_old_moves_2d) and (j[1] in player_color_old_moves_2d):
                    hit_three_moves.append(i)
        
        # calculate the case that game just starts
        if len(player_color_old_moves_2d) == 1:
            c_move = player_color_old_moves_2d[0]
            candidates = [(c_move[0]-1, c_move[1]-1), (c_move[0]+1, c_move[1]-1),\
                (c_move[0]-1, c_move[1]+1), (c_move[0]+1, c_move[1]+1)]
            for i in candidates:
                if i in legal_moves_2d:
                    start_moves.append(i)


        # remove duplicate
        hit_three_moves = remove(hit_three_moves)
        possible_moves = remove(possible_moves)
        start_moves = remove(start_moves)

        # print("legal move", legal_moves_2d)
        # print("player color moves", player_color_old_moves_2d)
        # print("opponent color moves", opponent_color_old_moves_2d)
        # print("start move", start_moves)
        # print("possible move", possible_moves)
        # print("hit three", hit_three_moves)
        # print("___")
        
        # check double three move
        
        # check if pattern moves will be created
        moves_can_create_pattern_move = []
        copyboard = board.copy()
        
        for i in legal_moves_2d:
            move_point = coord_to_point(i[0], i[1], copyboard.size)
            copyboard.play_move_gomoku(move_point, current_color)
            ret = copyboard.get_pattern_moves()
            if ret != None:
                moves_can_create_pattern_move.append(i)
            copyboard = board.copy()
            
        must_win_move = []
        for i in legal_moves_2d:
            move_point = coord_to_point(i[0], i[1], copyboard.size)
            copyboard.play_move_gomoku(move_point, current_color)
            ret = copyboard.get_pattern_moves()
            if ret != None:
                second_copy_board = copyboard.copy()
                for j in ret[1]:
                    second_copy_board.play_move_gomoku(j, GoBoardUtil.opponent(current_color))
                    ret2 = second_copy_board.get_pattern_moves()
                    if ret2 != None:
                        must_win_move.append(i)
                    second_copy_board = copyboard.copy()
            copyboard = board.copy()
            
        # handle white start
        if (len(player_color_old_moves_2d) == 0) and (len(opponent_color_old_moves_2d) == 1) \
            and ((4,4) in legal_moves_2d):
            return [random.choice(self.twod_to_oned_list([(4,4)],board.size))]

        elif (len(player_color_old_moves_2d) == 0) and (len(opponent_color_old_moves_2d) == 1) \
            and ((3,3) in legal_moves_2d):
            return [random.choice(self.twod_to_oned_list([(3,3)],board.size))]

        # handle black start
        elif len(player_color_old_moves_2d) == 0 and len(opponent_color_old_moves_2d) == 0:
            return [random.choice(self.twod_to_oned_list([(4,4)],board.size))]
        
        #handle must win moves
        elif len(must_win_move) > 0:
            cloest_must_win_move = find_move_close_to_center(must_win_move, center = (3.5, 3.5))
            return [random.choice(self.twod_to_oned_list(cloest_must_win_move,board.size))]

        # go create pattern move
        elif len(moves_can_create_pattern_move) > 0:
            cloest_create_pattern_move = find_move_close_to_center(moves_can_create_pattern_move, center = (3.5, 3.5))
            return [random.choice(self.twod_to_oned_list(cloest_create_pattern_move,board.size))]

        # hit three if good enough
        elif len(hit_three_moves) > 4:
            cloest_hit_three_move = find_move_close_to_center(hit_three_moves, center = (3.5, 3.5))
            return [random.choice(self.twod_to_oned_list(cloest_hit_three_move,board.size))]

        # create best move for hit three
        elif len(possible_moves) > 0:
            cloest_possible_move = find_move_close_to_center(possible_moves, center = (3.5, 3.5))
            return [random.choice(self.twod_to_oned_list(cloest_possible_move,board.size))]

        # handle the second move
        elif len(start_moves) > 0:
            cloest_start_move = find_move_close_to_center(start_moves, center = (3.5, 3.5))
            return [random.choice(self.twod_to_oned_list(cloest_start_move, board.size))]
            
        # random case
        else:
            return legal_moves

    
    def twod_to_oned_list(self, twod_list, size):
        oned_list = []
        for i in twod_list:
            oned_list.append(coord_to_point(i[0], i[1], size))
        return oned_list


    def policy_moves(self, board, color_to_play):
        if(self.playout_policy=='random'):
            return "Random", self._random_moves(board, color_to_play)
        else:
            assert(self.playout_policy=='rule_based')
            assert(isinstance(board, SimpleGoBoard))
            ret=board.get_pattern_moves()
            if ret is None:
                return "Random", self._random_moves(board, color_to_play)
            movetype_id, moves=ret
            return self.pattern_list[movetype_id], moves
    
    def _do_playout(self, board, color_to_play):
        res=game_result(board)
        simulation_moves=[]
        while(res is None):
            _ , candidate_moves = self.policy_moves(board, board.current_player)
            playout_move=random.choice(candidate_moves)
            play_move(board, playout_move, board.current_player)
            simulation_moves.append(playout_move)
            res=game_result(board)
        for m in simulation_moves[::-1]:
            undo(board, m)
        if res == color_to_play:
            return 1.0
        elif res == 'draw':
            return 0.0
        else:
            assert(res == GoBoardUtil.opponent(color_to_play))
            return -1.0

    def get_move(self, board, color_to_play):
        """
        The genmove function called by gtp_connection
        """
        global current_color
        current_color = color_to_play
        moves=GoBoardUtil.generate_legal_moves_gomoku(board)
        toplay=board.current_player
        best_result, best_move=-1.1, None
        best_move=None
        wins = np.zeros(len(moves))
        visits = np.zeros(len(moves))
        start_time = timer()
        total_time = 0.0
        bad_simulation = False
        while total_time < 55.0 and bad_simulation:
            for i, move in enumerate(moves):
                print(total_time)
                end_time = timer()
                total_time = end_time - start_time
                play_move(board, move, toplay)
                res=game_result(board)
                if res == toplay:
                    undo(board, move)
                    #This move is a immediate win
                    self.best_move=move
                    return move
                ret=self._do_playout(board, toplay)
                wins[i] += ret
                visits[i] += 1
                win_rate = wins[i] / visits[i]
                if win_rate > best_result:
                    best_result=win_rate
                    best_move=move
                    self.best_move=best_move
                undo(board, move)
                if total_time > 54.9:
                    bad_simulation = True

        if (best_move!= None) and (bad_simulation==False):
            print("best move", best_move)
            return best_move
        else:
            _ , candidate_moves = self.policy_moves(board, board.current_player)
            print("candidate move", candidate_moves)
            playout_move=random.choice(candidate_moves)
            return playout_move

# https://www.geeksforgeeks.org/python-remove-duplicates-list/
def remove(duplicate): 
    final_list = [] 
    for num in duplicate: 
        if num not in final_list: 
            final_list.append(num) 
    return final_list
    

def find_move_close_to_center(candidate_list, center = (3.5, 3.5)):
    unsorted_dic = {}
    for i in candidate_list:
        dist = sqrt((pow((i[0]-center[0]), 2) + pow((i[1]-center[1]), 2)))
        unsorted_dic.update({i : dist})
    
    sorted_list = []
    for key, value in sorted(unsorted_dic.items(), key=lambda item: (item[1], item[0])):
        sorted_list.append(key)
    
    return [sorted_list[0]]

    

def run():
    """
    start the gtp connection and wait for commands.
    """
    board = SimpleGoBoard(7)
    con = GtpConnection(GomokuSimulationPlayer(), board)
    con.start_connection()

if __name__=='__main__':
    run()

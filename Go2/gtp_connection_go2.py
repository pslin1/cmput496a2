"""
Module for playing games of Go using GoTextProtocol

This code is based off of the gtp module in the Deep-Go project
by Isaac Henrion and Aamos Storkey at the University of Edinburgh.
"""
import traceback
import sys
import os
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, FLOODFILL
import gtp_connection
import numpy as np
import re
import time

class GtpConnectionGo2(gtp_connection.GtpConnection):

    def __init__(self, go_engine, board, outfile = 'gtp_log', debug_mode = False):
        """
        GTP connection of Go1

        Parameters
        ----------
        go_engine : GoPlayer
            a program that is capable of playing go by reading GTP commands
        komi : float
            komi used for the current game
        board: GoBoard
            SIZExSIZE array representing the current board state
        """
        gtp_connection.GtpConnection.__init__(self, go_engine, board, outfile, debug_mode)
        self.go_engine.con = self
        self.timelimit = 1
        self.commands["timelimit"] = self.timelimit_cmd
        self.argmap["timelimit"] = (1, "Usage: timelimit {time in seconds}")
        self.commands["go_safe"] = self.safety_cmd
        self.argmap["go_safe"] = (1, 'Usage: go_safe {w,b}')
        self.commands["solve"] = self.solve_cmd

    def safety_cmd(self, args):
        try:
            color= GoBoardUtil.color_to_int(args[0].lower())
            safety_list = self.board.find_safety(color)
            safety_points = []
            for point in safety_list:
                x,y = self.board._point_to_coord(point)
                safety_points.append(GoBoardUtil.format_point((x,y)))
            self.respond(safety_points)
        except Exception as e:
            self.respond('Error: {}'.format(str(e)))

    def timelimit_cmd(self, args):
        new_limit = int(args[0])
        if new_limit < 1 or new_limit > 100:
            self.respond("Usage: timelimit must be between 1 and 100 inclusive")
            return
        self.timelimit = new_limit
        self.respond()

    def negamaxBoolean(self, colour):
        time_spent = time.process_time() - self.entry_time     
        if time_spent > self.timelimit:
            self.timed_out = True
            return False, None
        
        if self.board.end_of_game():
            col, score = self.board.score(self.go_engine.komi)
            # we don't need the score or the move. We are simply returning which colour has won from the perspective of this colour
            if col == colour:
                return True, None
            else:
                return False, None
            
        non_eye_moves = GoBoardUtil.generate_legal_moves(self.board, colour).strip().split(" ")
        if non_eye_moves[0] == '':
            # the game isn't over but this colour has no moves to take and will pass
            non_eye_moves = []
        non_eye_moves = [GoBoardUtil.move_to_coord(m, self.board.size) for m in non_eye_moves]
        non_eye_moves = [self.board._coord_to_point(m[0], m[1]) for m in non_eye_moves]
        non_eye_moves = [m for m in non_eye_moves if not self.board.is_eye(m,colour)]
        non_eye_moves.sort(key=self.my_key, reverse=True)
        if non_eye_moves == []:
            # since the player has no moves, instead make it pass
            non_eye_moves = [None]
        for m in non_eye_moves:
            self.board.move(m, colour)
            opponent_success, move = self.negamaxBoolean(GoBoardUtil.opponent(colour))
            success = not opponent_success
            self.board.undo_move()
            if success:
                # most interested in obtaining the move that generated the win for the first iteration into this method, the other sequence of moves are lost
                return True, m
        # we don't need to know which move results in a loss
        return False, None        
        
    def get_benson_score(self, colour):
        return len(self.board.find_safety(colour))

    def get_capture_score(self):
        caps = self.board.captured_stones[-1]
        if caps:
            return len(caps)
        else:
            return 0

    def my_key(self, move):
        colour = self.board.current_player
        self.board.move(move, colour)
        benson_score = self.get_benson_score(colour)
        capture_score = self.get_capture_score()
        self.board.undo_move()
        return (benson_score, capture_score)

    def solve(self, args=None):
        colour = self.board.current_player
        self.entry_time = time.process_time()
        self.timed_out = False
        can_win, move = self.negamaxBoolean(colour)
        if self.timed_out:
            return(False, None)
        return(can_win, move) 
    
    def solve_cmd(self, args=None):
        colour = self.board.current_player
        can_win, move = self.solve(args)
        if self.timed_out:
            self.respond("unknown")
        else:
            if can_win:
                if move:
                    formatted_move = GoBoardUtil.format_point(self.board._point_to_coord(move))
                else:
                    formatted_move = GoBoardUtil.format_point(move)
                    self.respond(GoBoardUtil.int_to_color(colour) + ' ' + formatted_move)
            else:
                self.respond(GoBoardUtil.int_to_color(GoBoardUtil.opponent(colour)))


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
        self.respond(self.timelimit)

    def negamaxBoolean(self, colour):
        time_spent = time.process_time() - self.entry_time     
        if time_spent > self.timelimit:
            return "unknown"
        
        if self.board.end_of_game():
            return self.board.score(self.go_engine.komi) 
        
        non_eye_moves = GoBoardUtil.generate_legal_moves(self.board, colour).strip().split(" ")
        if non_eye_moves[0] == '':
            return False
        non_eye_moves = [GoBoardUtil.move_to_coord(m, self.board.size) for m in non_eye_moves]
        non_eye_moves = [self.board._coord_to_point(m[0], m[1]) for m in non_eye_moves]
        non_eye_moves = [m for m in non_eye_moves if not self.board.is_eye(m,colour)]
        print(non_eye_moves)
        for m in non_eye_moves:
            self.board.move(m, colour)
            success = not self.negamaxBoolean(GoBoardUtil.opponent(colour))
            #print(success, colour)
            self.board.undo_move()
            if success:
                return True
        return False        
        
    def solve_cmd(self, args):
        self.entry_time = time.process_time()
        game_end = False
        while not game_end:
            game_end = self.negamaxBoolean(1)
            print(game_end)


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
        self.timelimit = float(args[0])
        print(type(self.timelimit))

    def negamaxBoolean(self, colour):
        #if endofgame
        #return false

        legal_moves = GoBoardUtil.generate_legal_moves(self.board, colour)
        for m in legal_moves:
            print(m)
        

    def solve_cmd(self, args):
        self.negamaxBoolean(1)
        #print(self.board.current_player) #1 is black, 2 is white
        #print("solve_cmd")


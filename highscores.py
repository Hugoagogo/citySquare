# -*- coding: utf-8 -*-

# @name: highscore.py
# @summary: This is a simple Python module using SQLite to store and retrieve highscores
# @author: Morten André Steinsland 
# @contact: www.mortenblog.net 

# @license: GNU Lesser General Public License
# @copyright: Copyright 2009 Morten André Steinsland
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/

# @version: 1.3
# @since: 25.10.2009
# @status: Working, Not perfect

# @note: Examples
# DATABASE = HighScoreFile('highscores.dat')
# DATABASE.addscore(3543,'PlayerName')
# DATABASE.gethighestscore()
# DATABASE.getlowestscore()
# DATABASE.gettopscores(10)

import sqlite3
from os import path

class HighScoreFile:
    def __init__(self, filename):
        """Does the connecting and construction if database does not already exist"""
        self.databasename = filename

        if path.exists(self.databasename) and path.isfile(self.databasename):
            # database already exist, go ahead and connect
            self.database = sqlite3.connect(self.databasename)
            self.dbcursor = self.database.cursor()

        else:
            # we need to construct the database for the first time
            # @todo: create some default data(?)
            self.database = sqlite3.connect(self.databasename)
            self.dbcursor = self.database.cursor()
            sqlstatement = u"""CREATE TABLE highscores(score FLOAT, playername TEXT);"""
            self.dbcursor.execute(sqlstatement)
            self.database.commit()

    def getlowestscore(self):
        """Returns the lowest ranking player and his score"""
        sqlstatement = u"""SELECT score,playername FROM highscores WHERE score = (SELECT min(score) FROM highscores) LIMIT 1;"""
        self.dbcursor.execute(sqlstatement)

        for row in self.dbcursor:
            return (row[0],unicode(str(row[1])))

    def gethighestscore(self):
        """Returns the highest ranking player and his score"""
        sqlstatement = u"""SELECT score,playername FROM highscores WHERE score = (SELECT max(score) FROM highscores) LIMIT 1;"""
        self.dbcursor.execute(sqlstatement)

        for row in self.dbcursor:
            return (row[0],unicode(str(row[1])))

    def gettopscores(self,scores):
        """Returns top X scores"""
        # @todo: handle scores variable being bigger than number of rows(?)
        sqlstatement = u"""SELECT score,playername FROM highscores ORDER BY score DESC LIMIT %s;""" % scores
        self.dbcursor.execute(sqlstatement)
        toplist = []

        for row in self.dbcursor:
            toplist.append((row[0],unicode(row[1])))

        toplist.sort(key=lambda x:x[1].lower()) #sort by name
        toplist.sort(key=lambda x:x[0], reverse=True) #sort by score

        return toplist

    def addscore(self,playername,playerscore):
        """Add the players name and score to the database"""
        sqlstatement = u"""INSERT INTO highscores(score,playername) values (%s,'%s');""" % (str(playerscore), str(playername))
        self.dbcursor.execute(sqlstatement)
        self.maintenance()

    def maintenance(self):
        """Sorts the highscorelist , removes duplicates and commits changes"""
        keeptopscores = 10 #keep this many top scores
        sqlstatement = u"""SELECT score, playername FROM highscores ORDER BY score DESC LIMIT %s;""" % (keeptopscores)
        self.dbcursor.execute(sqlstatement)
        highscores = []

        for row in self.dbcursor:
            highscores.append((row[0],unicode(row[1])))

        highscores.sort(key=lambda x:x[1].lower()) #sort by name
        highscores.sort(key=lambda x:x[0],reverse=True) #sort by score

        ###DELETES THE CONTENTS OF THE highscores TABLE###
        sqlstatement = u"""DELETE FROM highscores WHERE rowid > -1;"""
        self.dbcursor.execute(sqlstatement)
        #########################################################

        del highscores[keeptopscores:] #remove unwanted scores

        #insert sorted data into score table
        for each in highscores:
            sqlstatement = u"""INSERT INTO highscores(score,playername) values (%s,'%s');""" % (str(each[0]),str(each[1]))
            self.dbcursor.execute(sqlstatement)

        #finish up
        del highscores
        self.database.commit()
# -*- coding: utf-8 -*-

# @name: highscore.py
# @summary: This is a simple Python module using SQLite to store and retrieve highscores
# @author: Morten André Steinsl and made to use pickle instead of sqlite3 by hugoagogo
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

import pickle
from os import path

class HighScoreFile:
    def __init__(self, filename):
        """Does the connecting and construction if database does not already exist"""
        self.databasename = filename

        if path.exists(self.databasename) and path.isfile(self.databasename):
            # database already exist, go ahead and connect
            f = open(self.databasename)
            self.results = pickle.load(f)
            f.close()
            

        else:
            # we need to construct the database for the first time
            self.results = []
            f = open(self.databasename,"w")
            pickle.dump(self.results,f)
            f.close()
            

    def getlowestscore(self):
        print "Not implimented"

    def gethighestscore(self):
        print "Not implimented"
        
    def on_table(self,score):
        if len(self.results[:10]) < 10:
            return True
        for result in self.results[:10]:
            if score > result[0]:
                return True
        return False

    def gettopscores(self,scores):
        """Returns top X scores"""
        # @todo: handle scores variable being bigger than number of rows(?)
        if len(self.results) >= scores:
            toplist = self.results[:10]
        else:
            toplist = self.results

        return toplist

    def addscore(self,playername,playerscore):
        """Add the players name and score to the database"""
        self.results.append([playerscore,playername])
        self.maintenance()

    def maintenance(self):
        """Sorts the highscorelist , removes duplicates and commits changes"""
        keeptopscores = 10 #keep this many top scores
        highscores = self.results[:keeptopscores]

        highscores.sort(key=lambda x:x[1].lower()) #sort by name
        highscores.sort(key=lambda x:x[0],reverse=True) #sort by score

        self.results = highscores
        f = open(self.databasename,"w")
        pickle.dump(self.results,f)
        f.close()
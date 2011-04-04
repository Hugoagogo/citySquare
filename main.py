import pyglet
import os

SIDE_TYPES = ["g","c","r"]


def load_tiles(directory):
    tiles = []
    for dirpath, dirnames, filenames in os.walk("directory"):
        for file in filenames:
            tiles.append(Tile(os.path.join(dirpath,file)))

class TileLoadError(Exception):
    "This is raised when loading a tile fails for whatever reason"
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class Tile(object):
    def __init__(self,filename):
        head, tail = os.path.split(filename)
        head = head[:head.rfind(".")]
        
        self.sides = []
        
        for side in head[:4]:
            if not side in SIDE_TYPES:
                raise TileLoadError("Invalid Side Data")
            else:
                self.sides.append(side)
        
        linked = []
        for link in head[5:].split("-"):
            link = [int() for x in list(link)]
            if max(link) > len(self.sides):
                raise TileLoadError("Invalid Link Data")
                

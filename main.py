import pyglet
import os

SIDE_TYPES = ["g","c","r"]


def load_tiles(directory):
    tiles = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for file in filenames:
            tiles.append(Tile(os.path.join(dirpath,file)))
    return tiles

class TileLoadError(Exception):
    "This is raised when loading a tile fails for whatever reason"
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class Tile(object):
    def __init__(self,filename):
        head, tail = os.path.split(filename)
        tail = tail[:tail.rfind(".")]
        
        self.sides = []
        
        for side in tail[:4]:
            if not side in SIDE_TYPES:
                raise TileLoadError("Invalid Side Data")
            else:
                self.sides.append(side)
        
        self.links = []
        for link in tail[5:].split("-"):
            link = [int(x) for x in list(link)]
            if link and max(link) > len(self.sides) and min(link) > 0:
                raise TileLoadError("Invalid Link Data")
            self.links.append(link)
        print len(self.links)
    def __repr__(self):
        return "<Tile %s with links %s>"%("".join(self.sides),str(["-".join(map(str,x)) for x in self.links]))
        
print load_tiles("res/tiles/")
                

import pyglet
import os

WINDOW_SIZE = (800,600)
TILE_SIZE = 128

SIDE_TYPES = ["g","c","r"]

CW, CCW = 1, -1

def load_tiles(directory):
    tiles = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for file in filenames:
            if file[file.rfind("."):] == ".png":
                tiles.append(Tile(os.path.join(dirpath,file)))
    return tiles

def cycle_list(tlist,direction):
    tlist = tlist[:]
    for x in range(abs(direction)):
        if direction > 0:
            tlist.insert(0,tlist.pop(-1))
        else:
            tlist.append(tlist.pop())
    return tlist

def cycle_int(tint,direction,cap):
    print tint
    tint = (direction+tint)%cap
    if tint < 1: tint = cap-tint
    return tint

def build_2darray(x,y):
    return [[None]*x for x in range(y)]

class TileLoadError(Exception):
    "This is raised when loading a tile fails for whatever reason"
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class Tile(pyglet.sprite.Sprite):
    def __init__(self,filename):
        head, tail = os.path.split(filename)
        tail = tail[:tail.rfind(".")]
        
        self.sides = []
        
        for side in tail[:4]:
            if not side in SIDE_TYPES:
                raise TileLoadError("Invalid Side Data: "+tail)
            else:
                self.sides.append(side)
        
        self.links = []
        for link in tail[5:].split("-"):
            link = [int(x) for x in list(link)]
            if link and max(link) > len(self.sides) and min(link) > 0:
                raise TileLoadError("Invalid Link Data: "+ tail)
            self.links.append(link)
            
        image = pyglet.image.load(filename)
        image.anchor_x = image.width  // 2
        image.anchor_y = image.height // 2
        
        pyglet.sprite.Sprite.__init__(self,image)

            
    def __repr__(self):
        return "<Tile %s with links %s>"%("".join(self.sides),str(["-".join(map(str,x)) for x in self.links]))
        
    def rotate(self,direction):
        self.sides = cycle_list(self.sides,direction)
        self.links = [[cycle_int(y,direction,len(self.sides)) for y in x] for x in self.links]
        self.rotation += 90*direction
        
class Grid(object):
    def __init__(self,scale):
        self.grid = build_2dgrid(9,9)
        self.unused_tiles = []
        self.scale = scale
        
    def drop_tile(self,x,y):
        x *= self.scale
        y *= self.scale
        
load_tiles("res/tiles/")

grid = Grid((TILE_SIZE*9) / WINDOW_SIZE[1])
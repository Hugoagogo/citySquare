import pyglet
from pyglet import gl

import random

import os

WINDOW_SIZE = (1024,768)
TILE_SIZE = 128
HALF_TILE_SIZE = TILE_SIZE // 2

SIDE_TYPES = ["g","c","r"]

CW, CCW = 1, -1

def load_tiles(directory):
    tiles = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for file in filenames:
            if file[file.rfind("."):] == ".png":
                tiles.append(Tile(os.path.join(dirpath,file)))
                tiles[-1].x,tiles[-1].y = 200,200
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
    return [[None]*x for y in range(y)]

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
    def __init__(self,win,scale):
        self.grid = build_2darray(9,9)
        print self.grid
        self.win = win
        self.unused_tiles = []
        self.scale = scale
        
    def drop(self,tile,x,y):
        print tile, x
        if tile.x < (9*self.win.height*self.scale):
            x = self.win.screen2grid(x-(TILE_SIZE*self.scale)/2)
            y = self.win.screen2grid(y-(TILE_SIZE*self.scale)/2)
            print x
            tile.scale = self.scale
            tile.x = (x+0.5)*TILE_SIZE*self.scale
            print x*TILE_SIZE*self.scale
            tile.y = (y+0.5)*TILE_SIZE*self.scale

            self.grid[x][y] = tile
        else:
            tile.scale
        
    def draw(self):
        gl.glBegin(gl.GL_LINES)
        for x in range(10):
            gl.glColor3ub(125,125,125)
            gl.glColor3ub(125,125,125)
            gl.glColor3ub(125,125,125)
            gl.glColor3ub(125,125,125)
            
            gl.glVertex2f(x*TILE_SIZE*self.scale,0)
            gl.glVertex2f(x*TILE_SIZE*self.scale,self.win.height)
            gl.glVertex2f(0,x*TILE_SIZE*self.scale)
            gl.glVertex2f(self.win.height,x*TILE_SIZE*self.scale)
        gl.glEnd()
            
        
        for line in self.grid:
            for tile in line:
                if tile:
                    tile.draw()
        
        for tile in self.unused_tiles:
            tile.draw()

class GameWindow(pyglet.window.Window):
    def __init__(self,*args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.all_tiles = load_tiles("res/tiles/")
        self.setup()
        
    def setup(self):
        self.grid = Grid(self,(self.height/float(9*TILE_SIZE)))
        
        for x in range(3):
            self.grid.drop(random.choice(self.all_tiles),int(x*(TILE_SIZE*self.grid.scale))+5,20)
        
    def on_mouse_down(self):
        pass
    
    def on_mouse_move(self):
        print screen2grid(x), screen2grid(y)
    
    def on_draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.grid.draw()
        
    def screen2grid(self,val):
        val = int(round((val/self.grid.scale)/TILE_SIZE))
        return val
    
#win = GameWindow(fullscreen=True)
win = GameWindow(width=WINDOW_SIZE[0],height=WINDOW_SIZE[1])
pyglet.app.run()


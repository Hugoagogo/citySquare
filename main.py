import pyglet
from pyglet import gl

import random
import copy

import os,sys

# open our log file
so = se = open("test.log", 'w', 0)

# re-open stdout without buffering
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

# redirect stdout and stderr to the log file opened above
os.dup2(so.fileno(), sys.stdout.fileno())

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
    tint = (direction+tint)%cap
    if tint < 1: tint = cap-tint
    return tint

def build_2darray(x,y):
    return [[None]*x for y in range(y)]

def build_perfect_grid(grid,tiles):
    grid.pprint()
    print
    for row in range(len(grid.grid)):
        for col in range(len(grid.grid[row])):
            print col,row
            if grid[row][col] == None:
                sides = grid.edges_at(col,row)
                print sides
                possibles = []
                
                for tile in tiles:
                    cmp = compare_sides(sides, tile.sides)
                    if cmp != -1:
                        print tile
                        tile.rotate(cmp)
                        print tile
                        possibles.append(copy.deepcopy(tile))
                random.shuffle(possibles)
                print possibles
                for possible in possibles:
                    grid.place(possible,col,row)
                    done, grid2 = build_perfect_grid(grid,tiles)
                    if done:
                        return True, grid2
                grid[col][row] = None
                return False, None
    return True, grid
        
def compare_sides(sides1,sides2):
    sides2 = sides2[:]
    for x in range(len(sides1)):
        if same_sides(sides1, sides2):
            return x
        sides2 = cycle_list(sides2,1)
    else:
        return -1

def same_sides(sides1,sides2):
    for s1, s2 in zip(sides1,sides2):
        if not (s1 == s2 or s1 == "#" or s2 == "#"):
            return False
    return True
        

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
        
    def tiles_to_fill(self):
        print "STARTED"
        flag, grid = build_perfect_grid(Grid(self.win,self.scale),self.win.all_tiles)
        if flag:
            self.win.grid = grid
            print "DONE"
        else:
            print "DAMIT"
        
    def drop(self,tile,x,y):
        if tile.x < (9*self.win.height*self.scale):
            x = self.win.screen2grid(x-(TILE_SIZE*self.scale)/2)
            y = self.win.screen2grid(y-(TILE_SIZE*self.scale)/2)
            self.place(tile,x,y)
        else:
            tile.scale = self.scale/2
            tile.x = x
            tile.y = y
        
    def place(self,tile,x,y):
        tile.scale = self.scale
        tile.x = (x+0.5)*TILE_SIZE*self.scale
        tile.y = (y+0.5)*TILE_SIZE*self.scale
        self.grid[y][x] = tile
        
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
    
    def edges_at(self,x,y):
         edges = []
         for deltano, delta in enumerate([(0,1),(1,0),(0,-1),(-1,0)]):
             px, py = x+delta[0],y+delta[1]
             print "++>",px,py, delta,
             if 0 <= px < len(self.grid[0]) and 0 <= py < len(self.grid):
                 print self.grid[py][px]
                 if self.grid[py][px]:
                     edges.append(self.grid[py][px].sides[(deltano+2)%len(self.grid[py][px].sides)])
                 else:
                     edges.append("#")
                 print "IN"
             else:
                 edges.append("g")
                 print "bang"
                 print "OUT"
         return edges
    
    def __getitem__(self,key):
        return self.grid[key]
        
    def pprint(self):
        print "GRID OBJECT"
        for line in reversed(self.grid): print line
                
        

class GameWindow(pyglet.window.Window):
    def __init__(self,*args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.all_tiles = load_tiles("res/tiles/")
        self.setup()
        
    def setup(self):
        self.grid = Grid(self,(self.height/float(9*TILE_SIZE)))
        
        for x in range(3):
            self.grid.drop(random.choice(self.all_tiles),int(x*(TILE_SIZE*self.grid.scale))+5,20)
        
    def on_mouse_press(self,x,y,button,modifiers):
        self.grid.tiles_to_fill()
    
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


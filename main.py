import pyglet
from pyglet import gl

import random
import copy

import os,sys

## open our log file
#so = se = open("test.log", 'w', 0)
#
## re-open stdout without buffering
#sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
#
## redirect stdout and stderr to the log file opened above
#os.dup2(so.fileno(), sys.stdout.fileno())

WINDOW_SIZE = (920,720)
TILE_SIZE = 128
HALF_TILE_SIZE = TILE_SIZE // 2

SIDE_TYPES = ["g","c","r"]

CW, CCW = 1, -1

def load_tiles(directory):
    tiles = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for file in filenames:
            if file[file.rfind("."):] == ".png":
                tiles.append(DummyTile(os.path.join(dirpath,file)))
    return tiles

def cycle_list(tlist,direction):
    tlist = tlist[:]
    for x in range(abs(direction)):
        if direction > 0:
            tlist.insert(0,tlist.pop())
        else:
            tlist.append(tlist.pop(0))
    return tlist

def cycle_int(tint,direction,cap):
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

class DummyTile(object):
    def __init__(self,filename):
        self.filename = filename
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
    
    def compare_sides(self,sides):
        sides = sides[:]
        for x in range(len(self.sides)):
            if self.same_sides(sides):
                return x
            sides = cycle_list(sides,1)
        else:
            return -1

    def same_sides(self,sides):
        for s1, s2 in zip(self.sides,sides):
            if not (s1 == s2 or s1 == "#" or s2 == "#"):
                return False
        return True
        
    def rotate(self,direction):
        self.sides = cycle_list(self.sides,direction)
        self.links = [[cycle_int(y,direction,len(self.sides)) for y in x] for x in self.links]
        
    def print_square(self):
        return [
            " "+str(self.sides[0])+" ",
            str(self.sides[3])+"#"+str(self.sides[1]),
            " "+str(self.sides[2])+" "
            ]
        
    def __repr__(self):
        return "<Tile %s, %s>"%("".join(self.sides),str(["-".join(map(str,x)) for x in self.links]))
        #return str(id(self))

class Tile(DummyTile,pyglet.sprite.Sprite):
    def __init__(self,filename):
        DummyTile.__init__(self,filename)
        image = pyglet.image.load(self.filename)
        image.anchor_x = image.width  // 2
        image.anchor_y = image.height // 2
        pyglet.sprite.Sprite.__init__(self,image)
        
    def rotate(self,direction):
        super(Tile, self).rotate(direction)
        self.rotation += 90*direction
        
    def draw(self,x,y,scale=1):
        self.x = x
        self.y = y
        self.scale = scale
        pyglet.sprite.Sprite.draw(self)
        
class Grid(object):
    def __init__(self,win,width,height):
        self.grid = build_2darray(width,height)
        self.width, self.height = width, height
        
        self.win = win
        self.scale = (self.win.height/float(self.height*TILE_SIZE))
        
        self.unused_tiles = []
        
    def __call__(self,x,y,tile=-123):
        if tile != -123:
            self.grid[y][x] = tile
        return self.grid[y][x]
    
    def build_perfect_grid(self):
        print "Building Grid"
        flag = self._build_perfect_grid(load_tiles("res/tiles/"))
        if flag:
            print "Generated Grid"
        else:
            print "Darn somethings broken couldnt generate grid"
    
    def _build_perfect_grid(self, tiles):
        random.shuffle(tiles)
        for y in range(self.height):
            for x in range(self.width):
                if self(x,y) == None:
                    to_fit = self.edges_at(x,y)
                    for tile in tiles:
                        cmp = tile.compare_sides(to_fit)
                        if cmp != -1:
                            self(x,y,Tile(tile.filename)).rotate(-cmp)
                            self.print_square()
                            print to_fit
                            flag = self._build_perfect_grid(tiles)
                            if flag:
                                return True
                    self(x,y,None)
                    return False
        return True
                        
                            
                    
    def edges_at(self,x,y):
        edges = []
        self.print_square()
        print "+"*20
        for deltano, delta in enumerate([(0,1),(1,0),(0,-1),(-1,0)]):
            px, py = x+delta[0],y+delta[1]
            if 0 <= px < len(self.grid[0]) and 0 <= py < len(self.grid):
                if self.grid[py][px]:
                    print "===>",len(edges),(deltano+2)%4,self.grid[py][px].sides[(deltano+2)%4]
                    edges.append(self.grid[py][px].sides[(deltano+2)%4])
                else:
                    edges.append("#")
            else:
                print "arg"
                edges.append("g")
        return edges

    def draw(self):
        gl.glBegin(gl.GL_LINES)
        for x in range(10):
            gl.glColor3ub(125,125,125)
            
            gl.glVertex2f(x*TILE_SIZE*self.scale,0)
            gl.glVertex2f(x*TILE_SIZE*self.scale,self.win.height)
            gl.glVertex2f(0,x*TILE_SIZE*self.scale)
            gl.glVertex2f(self.win.height,x*TILE_SIZE*self.scale)
        gl.glEnd()
            
        
        for y in range(self.width):
            for x in range(self.height):
                if self(x,y):
                    #print tile.position, tile.rotation
                    self(x,y).draw((x+0.5)*TILE_SIZE*self.scale,(y+0.5)*TILE_SIZE*self.scale,self.scale)
        
        for tile in self.unused_tiles:
            tile.draw()
            print "SIGH"
    
    def print_square(self):
        big = []
        for line in reversed(self.grid):
            reline = []
            for tile in line:
                if tile:
                    reline.append(tile.print_square())
                else:
                    reline.append(["   "]*3)
            big.extend(zip(*reline))
        print "\n".join(("".join(x) for x in big))

#class Grid(object):
#    def __init__(self,win,scale):
#        self.grid = build_2darray(9,9)
#        self.win = win
#        self.unused_tiles = []
#        self.scale = scale
#        
#    def print_places(self):
#        for line in self.grid:
#            for square in line:
#                print square, square.position
#                self.drop(square,square.x,square.y)
#    
#    def print_square(self):
#        big = []
#        for line in reversed(self.grid):
#            big.extend(zip(*[tile.print_square() for tile in line]))
#        print "\n".join(("".join(x) for x in big))
#              
#    def drop(self,tile,x,y):
#        if tile.x < (9*self.win.height*self.scale):
#            x = self.win.screen2grid(x-(TILE_SIZE*self.scale)/2)
#            y = self.win.screen2grid(y-(TILE_SIZE*self.scale)/2)
#            self.place(tile,x,y)
#        else:
#            tile.scale = self.scale/2
#            tile.x = x
#            tile.y = y
#        
#    def place(self,tile,x,y):
#        tile.scale = self.scale
#        tile.x = (x+0.5)*TILE_SIZE*self.scale
#        tile.y = (y+0.5)*TILE_SIZE*self.scale
#        print x,y, tile.x, tile.y
#        self.grid[y][x] = tile
#        
#    def draw(self):
#        gl.glBegin(gl.GL_LINES)
#        for x in range(10):
#            gl.glColor3ub(125,125,125)
#            gl.glColor3ub(125,125,125)
#            gl.glColor3ub(125,125,125)
#            gl.glColor3ub(125,125,125)
#            
#            gl.glVertex2f(x*TILE_SIZE*self.scale,0)
#            gl.glVertex2f(x*TILE_SIZE*self.scale,self.win.height)
#            gl.glVertex2f(0,x*TILE_SIZE*self.scale)
#            gl.glVertex2f(self.win.height,x*TILE_SIZE*self.scale)
#        gl.glEnd()
#            
#        
#        for line in self.grid:
#            for tile in line:
#                if tile:
#                    #print tile.position, tile.rotation
#                    tile.draw()
#        
#        for tile in self.unused_tiles:
#            tile.draw()
#            print "SIGH"
    #
    #def __getitem__(self,key):
    #    return self.grid[key]
    #    
    #def pprint(self):
    #    print "GRID OBJECT"
    #    for line in reversed(self.grid): print line
    #            
    #    

class GameWindow(pyglet.window.Window):
    def __init__(self,*args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.setup()
        
    def setup(self):
        self.grid = Grid(self,9,9)
        self.grid.build_perfect_grid()
        #
        #for x in range(3):
        #    self.grid.drop(random.choice(self.all_tiles),int(x*(TILE_SIZE*self.grid.scale))+5,20)
        
    def on_mouse_press(self,x,y,button,modifiers):
        print "STARTED"
        flag, grid = build_perfect_grid(self.grid,self.all_tiles)
        if flag:
            self.grid = grid
            grid.print_places()
            print grid.grid
            print "DONE"
        else:
            print "DAMIT"
            
    def on_mouse_motion(self,x,y,dx,dy):
    #    self.grid.print_square()
        x,y = self.screen2grid(x), self.screen2grid(y)
        print x,y,self.grid.edges_at(x,y)
    #    print x,y,
    #    if self.grid(x,y):
    #        print self.grid(x,y).x,self.grid(x,y).y,self.grid(x,y).rotation,self.grid(x,y)
    #    else:
    #        print
        #self.grid(x,y).x,self.grid(x,y).y = (x+0.5)*TILE_SIZE*self.grid.scale,(y+0.5)*TILE_SIZE*self.grid.scale
        #self.grid.print_places()
    
    def on_draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.grid.draw()
        
    def screen2grid(self,val):
        val = int(round(((val/self.grid.scale)-HALF_TILE_SIZE)/TILE_SIZE))
        return val
    
#win = GameWindow(fullscreen=True)
win = GameWindow(width=WINDOW_SIZE[0],height=WINDOW_SIZE[1])
pyglet.app.run()


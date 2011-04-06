import pyglet
from pyglet import gl
from pyglet.window import key

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

WINDOW_SIZE = (800,600)
TILE_SIZE = 128
HALF_TILE_SIZE = TILE_SIZE // 2
TRAY_SCALE = .5
DRAG_SCALE = .9

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

def custom_shuffle(tiles):
    tile_vals = [random.triangular(0, 5, x.rarity/2) for x in tiles]
    return zip(*sorted(zip(tile_vals,tiles)))[1]

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
        
        self.rarity = int(tail[4])
        
        self.sides = []
        
        for side in tail[:4]:
            if not side in SIDE_TYPES:
                raise TileLoadError("Invalid Side Data: "+tail)
            else:
                self.sides.append(side)
        
        self.links = []
        for link in tail[6:].split("-"):
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
        self.rotation = self.rotation%360
    
    def point_over(self,x,y):
        ## NOTE THIS IS AS IT WAS LAST DRAWN
        d = (self.height//2)
        return x-d <= self.x <= x+d and y-d <= self.y <= y+d
    
    def draw(self,x,y,scale=1):
        self.x = int(x)
        self.y = int(y)
        self.scale = scale
        pyglet.sprite.Sprite.draw(self)
        
class Grid(object):
    def __init__(self,win,width,height):
        self.grid = build_2darray(width,height)
        self.width, self.height = width, height
        
        self.win = win
        self.scale = (self.win.height/float(self.height*TILE_SIZE))
        
        self.dragging = None
        
        self.tray_init()
        
    def tray_init(self,wipe = True):
        if wipe: self.tray = []
        self.tray_start_x = self.width*TILE_SIZE*self.scale
        self.tray_width = self.win.width-self.tray_start_x
        self.tray_cols = int(self.tray_width/(TRAY_SCALE*self.scale*TILE_SIZE))
        self.tray_cols_width = self.tray_width/self.tray_cols
        self.tray_max_rows = int(self.win.height/self.tray_cols_width)
    
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
        tiles = custom_shuffle(tiles)
        for y in range(self.height):
            for x in range(self.width):
                if self(x,y) == None:
                    to_fit = self.edges_at(x,y)
                    for tile in tiles:
                        cmp = tile.compare_sides(to_fit)
                        if cmp != -1:
                            self(x,y,Tile(tile.filename)).rotate(-cmp)
                            flag = self._build_perfect_grid(tiles)
                            if flag:
                                return True
                    self(x,y,None)
                    return False
        return True
                        
                            
                    
    def edges_at(self,x,y):
        edges = []
        for deltano, delta in enumerate([(0,1),(1,0),(0,-1),(-1,0)]):
            px, py = x+delta[0],y+delta[1]
            if 0 <= px < len(self.grid[0]) and 0 <= py < len(self.grid):
                if self.grid[py][px]:
                    edges.append(self.grid[py][px].sides[(deltano+2)%4])
                else:
                    edges.append("#")
            else:
                edges.append("g")
        return edges
    
    def degrid_all(self):
        for y in range(self.height):
            for x in range(self.width):
                self.tray.append(self(x,y))
                self(x,y,None)
                
    def shuffle_tray(self):
        random.shuffle(self.tray)
        for tile in self.tray:
            tile.rotate(random.randint(0,3))
            
    
    def grab(self,x,y):
        tile = self.tile_at(x,y)
        if tile:
            self.dragging = tile
            if tile in self.tray:
                self.tray.remove(tile)
                
            for y in range(self.height):
                for x in range(self.width):
                    if self(x,y) == tile:
                        self(x,y,None)
    
    def drop(self,x,y):
        x,y = self.win.screen2grid(x),self.win.screen2grid(y)
        
        if x < self.width:
            if self(x,y) == None:
                self(x,y,self.dragging)
                self.dragging = None
        else:
            self.tray.append(self.dragging)
            self.dragging = None
        
    
    def tile_at(self,x,y):
        for tile in self.tray:
            if tile.point_over(x,y):
                return tile
        
        for line in self.grid:
            for tile in line:
                if tile and tile.point_over(x,y):
                    return tile
        
    
    def draw(self):
        for y in range(self.height):
            for x in range(self.width):
                gl.glBegin(gl.GL_POLYGON)
                gl.glColor3ub(*[30+((x+y)%2)*50]*3)
                gl.glVertex2f(int(x*TILE_SIZE*self.scale),int(y*TILE_SIZE*self.scale))
                gl.glVertex2f(int((x+1)*TILE_SIZE*self.scale),int(y*TILE_SIZE*self.scale))
                gl.glVertex2f(int((x+1)*TILE_SIZE*self.scale),int((y+1)*TILE_SIZE*self.scale))
                gl.glVertex2f(int(x*TILE_SIZE*self.scale),int((y+1)*TILE_SIZE*self.scale))
                gl.glEnd()
            
        
        for y in range(self.height):
            for x in range(self.width):
                if self(x,y):
                    self(x,y).draw((x+0.5)*TILE_SIZE*self.scale,(y+0.5)*TILE_SIZE*self.scale,self.scale)
        
        row = 0
        col = 0
        for tile in self.tray:
            if col == self.tray_cols:
                col = 0
                row += 1
            x = self.tray_start_x + ((col+0.5)*self.tray_cols_width)
            y = self.win.height - ((row+0.5)*self.tray_cols_width)
            tile.draw(x,y,TRAY_SCALE*self.scale*9/10)
            col += 1
            
        if self.dragging: self.dragging.draw(self.dragging.x,self.dragging.y,self.scale*DRAG_SCALE)
            
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

class GameWindow(pyglet.window.Window):
    def __init__(self,*args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.grid = Grid(self,5,5)
        self.grid.build_perfect_grid()
        self.grid.degrid_all()
        
    def on_mouse_press(self,x,y,button,modifiers):
        if not self.grid.dragging: self.grid.grab(x,y)
        else: self.grid.drop(x,y)
            
    def on_mouse_motion(self,x,y,dx,dy):
        if self.grid.dragging: self.grid.dragging.set_position(x,y)
        
    #    self.grid.print_square()
        x,y = self.screen2grid(x), self.screen2grid(y)
        #print x,y,self.grid.edges_at(x,y)
    
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.grid.dragging:
            if scroll_y < 0:
                self.grid.dragging.rotate(CCW)
            else:
                self.grid.dragging.rotate(CW)
        
    def on_key_press(self,symbol, modifiers):
        if symbol == key.SPACE:
            self.grid.shuffle_tray()
        elif symbol == key.UP:
            self.grid.grid = cycle_list(self.grid.grid,1)
        elif symbol == key.DOWN:
            self.grid.grid = cycle_list(self.grid.grid,-1)
        elif symbol == key.LEFT:
            self.grid.grid = [cycle_list(x,-1) for x in self.grid.grid]
        elif symbol == key.RIGHT:
            self.grid.grid = [cycle_list(x,1) for x in self.grid.grid]
                
            
    
    def on_draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.grid.draw()
        
    def screen2grid(self,val):
        val = int(round(((val/self.grid.scale)-HALF_TILE_SIZE)/TILE_SIZE))
        return val
    
##win = GameWindow(fullscreen=True)
win = GameWindow(width=WINDOW_SIZE[0],height=WINDOW_SIZE[1])
pyglet.app.run()


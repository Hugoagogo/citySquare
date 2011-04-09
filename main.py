import pyglet
from pyglet import gl
from pyglet.window import key

import random
import copy
import time
import pickle

import os,sys

WINDOW_SIZE = (768,616) ## None For Fullscreen

TILE_SIZE = 128
HALF_TILE_SIZE = TILE_SIZE // 2
TRAY_SCALE = .5
DRAG_SCALE = .9

SIDE_TYPES = ["g","c","r"]

CW, CCW = 1, -1

pyglet.font.add_file('res/Square 721 BT.TTF')
square_font = pyglet.font.load('Square721 BT')

def load_tiles(directory):
    """ Returns a list of dummy tiles """
    tiles = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for file in filenames:
            if file[file.rfind("."):] == ".png":
                tiles.append(DummyTile(os.path.join(dirpath,file)))
    return tiles

def cycle_list(tlist,direction):
    """ Cycles a list fowards or backwards """
    tlist = tlist[:]
    for x in range(abs(direction)):
        if direction > 0:
            tlist.insert(0,tlist.pop())
        else:
            tlist.append(tlist.pop(0))
    return tlist

def cycle_int(tint,direction,cap):
    """ Cycles an int by direction so that it is never larger cap or less than 1"""
    tint = (direction+tint)%cap
    if tint < 1: tint = cap-tint
    return tint

def custom_shuffle(tiles):
    """ My custom method to sort tiles in a weighted way """
    tile_vals = [random.triangular(0, 5, x.rarity/2) for x in tiles]
    return zip(*sorted(zip(tile_vals,tiles)))[1]
    
def cmp_tilelist(a, b):
    if a == None: return 10000
    elif b == None: return -10000
    else: return (a.x*100+a.y)-(b.x*100+b.y)

def build_2darray(x,y):
    return [[None]*x for y in range(y)]
    
def city_score(num_tiles):
    return sum(range(num_tiles+1))

class TileLoadError(Exception):
    """ This is raised when loading a tile fails for whatever reason """
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class DummyTile(object):
    """ Only used for the purposes of building a grid """
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
        
        self.links = [[x+1] for x in range(len(self.sides)) if self.sides[x] != 'g']
        for link in tail[6:].split("-"):
            link = [int(x) for x in list(link)]
            if link:
                if max(link) > len(self.sides) and min(link) > 0:
                    raise TileLoadError("Invalid Link Data: "+ tail)
                else:
                    for part in link:
                        if [part] in self.links: self.links.remove([part])
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
        return "<Tile %s, %s>"%("".join(self.sides),str(self.links))
        #return str(id(self))

class Tile(DummyTile,pyglet.sprite.Sprite):
    """ Represent the tiles placed into the grid during gameplay """
    def __init__(self,filename):
        DummyTile.__init__(self,filename)
        image = pyglet.image.load(self.filename)
        image.anchor_x = image.width  // 2
        image.anchor_y = image.height // 2
        pyglet.sprite.Sprite.__init__(self,image)
        
        self.highlighted = False
        
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
    """ Very important represents the whole grid as well as the tray """
    def __init__(self,win,rect,width,height):
        self.grid = build_2darray(width,height)
        self.width, self.height = width, height
        
        self.win = win
        self.rect = rect
        self.scale = (self.rect.height/float(self.height*TILE_SIZE))
        
        self.dragging = None
        
        self.deltas = [(0,1),(1,0),(0,-1),(-1,0)]
                
        self.tray_init()
        
        self.scores = pyglet.text.layout.TextLayout(pyglet.text.decode_attributed('Hello, {bold True}world'),width=500,multiline=True)
        self.scores.anchor_x="center"
        self.scores.anchor_y="center"
        self.scores.x=(self.rect.width/2)+self.rect.x
        self.scores.y=(self.rect.height/2)+self.rect.y
        
    def tray_init(self,wipe = True):
        if wipe: self.tray = []
        self.tray_start_x = self.width*TILE_SIZE*self.scale
        self.tray_width = self.rect.width-self.tray_start_x
        self.tray_cols = int(self.tray_width/(TRAY_SCALE*self.scale*TILE_SIZE))
        self.tray_cols_width = self.tray_width/self.tray_cols
        self.tray_max_rows = int(self.rect.height/self.tray_cols_width)
    
    def __call__(self,x,y,tile=-123):
        if 0 <= x < self.width and 0 <= y < self.height:
            if tile != -123:
                self.grid[y][x] = tile
            return self.grid[y][x]
    
    def build_perfect_grid(self):
        """ A recursive way to fill the grid with tiles from its current state """
        print "Building Grid"
        flag = self._build_perfect_grid(load_tiles("res/tiles/"))
        if flag:
            print "Generated Grid"
        else:
            print "Darn somethings broken couldnt generate grid"
        self.max = 0
        self.max = self.score()
            
    
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
    
    def connected_to(self,x,y):
        #print "="*80
        all_attached = []
        tile = self(x,y)
        #print "CHECKING",tile,x,y
        if tile and tile.compare_sides(self.edges_at(x,y)) == 0:
            for link in tile.links:
                attached = [tile]
                for side in link:
                    side -= 1
                    dx, dy = x+self.deltas[side][0], y+self.deltas[side][1]
                    #print self.deltas[side], side, side+1, cycle_int(side+1,2,4)+1
                    self._connected_to(dx,dy,attached,cycle_int(side+1,2,4),tile.sides[side])
                all_attached.append([tile.sides[link[0]-1],attached])
            
        return all_attached
                
                    
    def _connected_to(self,x,y,attached,pside,type):
        tile = self(x,y)
        if not tile in attached:
            #print "--Spread",tile,x,y
            if tile and tile.compare_sides(self.edges_at(x,y)) == 0:
                for link in tile.links:
                    #print "HERE", pside, link
                    if pside in link:
                        attached.append(tile)
                        for side in link:
                            side -= 1
                            dx, dy = x+self.deltas[side][0], y+self.deltas[side][1]
                            self._connected_to(dx,dy,attached,cycle_int(side+1,2,4),type)
            elif not None in attached:
                #print x,y,tile
                attached.append(None)
                
    def score(self,final=False):
        score_text = "{color (255,255,255,255)}{font_name Arial}{font_size 20}Score distribution\n\n{font_size 14}"
        cities = []
        unfinished_cities = []
        roads = []
        unfinished_roads = []
        bonus = 0
        for y in range(self.height):
            for x in range(self.width):
                raw = self.connected_to(x,y)
                tile = self(x,y)
                if tile and tile.compare_sides(self.edges_at(x,y)) == 0: bonus += 1
                for type, links in raw:
                    #links = sorted(links,cmp=cmp_tilelist)
                    links = set(links)
                    if type == "c":
                            if None in links:
                                if not links in unfinished_cities:
                                    unfinished_cities.append(links)
                            else:
                                if not links in cities:
                                    cities.append(links)
                    elif type == "r":
                        if None in links:
                            for link in links:
                                if link and not link in unfinished_roads:
                                    unfinished_roads.append(link)
                        else: 
                            for link in links:
                                if not link in roads:
                                    roads.append(link)

        temp = sum([city_score(len(city)) for city in cities])
        score = temp
        score_text+="Finished Cities:\t\t%d points\n\n"%temp
        
        temp = sum([city_score(len(city)-1) for city in unfinished_cities])
        score -= temp
        score_text+="Uninished Cities:\t\t%d points\n\n"%temp
        
        temp = len(roads)
        score += temp
        score_text+="Finished Roads:\t\t%d points\n\n"%temp
        
        temp = len(unfinished_roads)
        score -= temp
        score_text+="Unfinished Roads:\t%d points\n\n"%temp
        
        if bonus == self.width*self.height:
            score += self.width*self.height
            score_text+="End of level Bonus:\t%d points\n\n"%(self.width*self.height)
        
        score_text+="Total:\t\t\t\t%d\n\n"%score
        if self.max: score_text+="Compleate:\t\t\t%.2f%%\n\n"%(100*float(score)/self.max)
        if final: score_text += "{font_size 12}<Press any key to finish>"
        self.scores.document = pyglet.text.decode_attributed(score_text)
        return score
                    
    def edges_at(self,x,y):
        """ Finds the edges that a tile would need to have to fit into a given square """
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
        """ Pushes all tiles to the tray """
        for y in range(self.height):
            for x in range(self.width):
                self.tray.append(self(x,y))
                self(x,y,None)
                
    def degrid_invalid(self):
        for tile, x, y in self.invalids():
            self.tray.append(tile)
            self(x,y,None)
            
    def highlight_invalids(self):
        for y in range(self.height):
            for x in range(self.width):
                tile = self(x,y)
                if tile:
                    if tile.compare_sides(self.edges_at(x,y)) != 0:
                        tile.highlighted = True
                    else:
                        tile.highlighted = False
            
    def invalids(self):
        invalids = []
        for y in range(self.height):
            for x in range(self.width):
                tile = self(x,y)
                if tile and tile.compare_sides(self.edges_at(x,y)) != 0:
                    invalids.append((tile,x,y))
        return invalids
        
                
    def shuffle_tray(self):
        """ Shuffles up the tray, couldnt have tiles being put back to easily could we """
        random.shuffle(self.tray)
        for tile in self.tray:
            tile.rotate(random.randint(0,3))
            
    
    def grab(self,x,y):
        """ Pick up a tile, if any at the given coordinates """
        tile = self.tile_at(x,y)
        if self.dragging and tile in self.tray: return False
        if tile:
            temp = None
            if self.dragging: temp = self.dragging
            self.dragging = tile
            if tile in self.tray:
                self.tray.remove(tile)
                return True
            for y in range(self.height):
                for x in range(self.width):
                    if self(x,y) == tile:
                        self(x,y,temp)
                        return True
    
    def drop(self,x,y):
        """ Drop the currently held tile to the board if possible """
        if self.dragging:
            x,y = self.screen2grid(x,y)
            temp = self.dragging
            if 0 <= x < self.width and 0 <= y < self.height:
                if self(x,y) == None:
                    self(x,y,self.dragging)
                    self.dragging = None
            else:
                self.tray.append(self.dragging)
                self.dragging = None
            return temp
    
    def tile_at(self,x,y):
        x -= self.rect.x
        y -= self.rect.y
        for tile in self.tray:
            if tile.point_over(x,y):
                return tile
        
        for line in self.grid:
            for tile in line:
                if tile and tile.point_over(x,y):
                    return tile        
    
    def draw(self):
        gl.glPushMatrix()
        gl.glTranslated(self.rect.x,self.rect.y,0)
        for y in range(self.height):
            for x in range(self.width):
                gl.glBegin(gl.GL_QUADS)
                gl.glColor3ub(*[30+((x+y)%2)*50]*3)
                gl.glVertex2f(int(x*TILE_SIZE*self.scale),int(y*TILE_SIZE*self.scale))
                gl.glVertex2f(int((x+1)*TILE_SIZE*self.scale),int(y*TILE_SIZE*self.scale))
                gl.glVertex2f(int((x+1)*TILE_SIZE*self.scale),int((y+1)*TILE_SIZE*self.scale))
                gl.glVertex2f(int(x*TILE_SIZE*self.scale),int((y+1)*TILE_SIZE*self.scale))
                gl.glEnd()
                
        
        for y in range(self.height):
            for x in range(self.width):
                if self(x,y):
                    self(x,y).draw(int((x+0.5)*TILE_SIZE*self.scale),int((y+0.5)*TILE_SIZE*self.scale),self.scale) 
                    if self(x,y).highlighted:
                        gl.glBegin(gl.GL_QUADS)
                        gl.glColor4ub(*[255,0,0,180])
                        gl.glVertex2f(int(x*TILE_SIZE*self.scale),int(y*TILE_SIZE*self.scale))
                        gl.glVertex2f(int((x+1)*TILE_SIZE*self.scale),int(y*TILE_SIZE*self.scale))
                        gl.glVertex2f(int((x+1)*TILE_SIZE*self.scale),int((y+1)*TILE_SIZE*self.scale))
                        gl.glVertex2f(int(x*TILE_SIZE*self.scale),int((y+1)*TILE_SIZE*self.scale))
                        gl.glEnd()
        
        row = 0
        col = 0
        for tile in self.tray:
            if col == self.tray_cols:
                col = 0
                row += 1
            x = self.tray_start_x + ((col+0.5)*self.tray_cols_width)
            y = self.rect.height - ((row+0.5)*self.tray_cols_width)
            tile.draw(x,y,TRAY_SCALE*self.scale*9/10)
            col += 1
        gl.glPopMatrix()
        if self.dragging: self.dragging.draw(self.dragging.x,self.dragging.y,self.scale*DRAG_SCALE)
    
    def draw_scores(self):
        gl.glBegin(gl.GL_QUADS)
        gl.glColor4ub(*[0,0,0,180])
        gl.glVertex2f(0,0)
        gl.glVertex2f(0,self.win.height)
        gl.glVertex2f(self.win.width,self.win.height)
        gl.glVertex2f(self.win.width,0)
        gl.glEnd()
            
        self.scores.draw()
    
    def screen2grid(self,x,y):
        x = int(round((((x-self.rect.x)/self.scale)-HALF_TILE_SIZE)/TILE_SIZE))
        y = int(round((((y-self.rect.y)/self.scale)-HALF_TILE_SIZE)/TILE_SIZE))
        return (x,y)
    
    def print_square(self):
        """ an ascii Representation of the grid """
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
class Rect(object):
    def __init__(self,pos,size):
        self.pos = pos
        self.x, self.y = pos
        self.size = size
        self.width, self.height = size
        
class ProgressBar(object):
    def __init__(self,rect,min,max,start_col,end_col,val=None):
        if val == None: val = max
        self.rect = rect
        self.rect.x += 1
        self.rect.y += 1
        self.min = min
        self.max = max
        self.start_col = start_col
        self.end_col = end_col
        self.col = (0,0,0)
               
        self.label = pyglet.text.Label('Hello, world',
                  font_name='Arial',
                  font_size=int(self.rect.height*.6),
                  anchor_x="center",
                  anchor_y="center",
                  bold = True,
                  color = (255,255,255,255),
                  x=(self.rect.width/2)+self.rect.x,
                  y=(self.rect.height/2)+self.rect.y)
        
        self.val = val
    
    def get_val(self):
        return self._val
    def set_val(self,val):
        self._val = val
        self.filled = abs((self.val-self.min)/float(self.max-self.min))
        
        if val >= 0:
            self.col = [int((x-y)*self.filled + y) for x,y in zip(self.start_col, self.end_col)]
        else:
            self.col = (180,180,180)
        self.label.text = self.text()
    val = property(get_val,set_val)
    
    def text(self):
        return "%d / %d"%(self.val, self.max)
        
    def draw(self):
        gl.glColor3ub(*self.col)
        gl.glBegin(gl.GL_LINE_LOOP)
        gl.glVertex2f(int(self.rect.x),int(self.rect.y))
        gl.glVertex2f(int(self.rect.x),int(self.rect.y+self.rect.height))
        gl.glVertex2f(int(self.rect.x+self.rect.width),int(self.rect.y+self.rect.height))
        gl.glVertex2f(int(self.rect.x+self.rect.width),int(self.rect.y))
        gl.glEnd()
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(int((self.rect.x)*self.filled),int(self.rect.y))
        gl.glVertex2f(int((self.rect.x)*self.filled),int(self.rect.y+self.rect.height))
        gl.glVertex2f(int((self.rect.x+self.rect.width)*self.filled),int(self.rect.y+self.rect.height))
        gl.glVertex2f(int((self.rect.x+self.rect.width)*self.filled),int(self.rect.y))
        gl.glEnd()

        self.label.draw()
        
class TimeBar(ProgressBar):
    def text(self):
        return str(int(self.val/60))+":"+str(int(self.val%60)).zfill(2)
        
#class HighScores(object):
#    def __init__(self,file):
#        self.file = file
#    
#    def load(self):
#        f = open(self.file)
#        self.data = pickle.load(f)
#        f.close()
#        
#    def save(self):
#        f = open(self.file,"w")
#        pickle.dump(self.data,f)
#        f.close()
        

class GameWindow(pyglet.window.Window):
    def __init__(self,*args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        pyglet.clock.schedule_interval(lambda _: None, 0)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        self.states = [MainMenu(self)] #PlayLevel(self,*GRID_SIZE)
    
    def push_scene(self,state):
        self.states[-1].deactivate()
        self.states.append(state)
        self.states[-1].activate()
    
    def pop_scene(self):
        self.states[-1].deactivate()
        self.states.pop()
        if not len(self.states):
            exit()
        else:
            self.states[-1].activate()
        
    def on_draw(self):
        if hasattr(self.states[-1],"on_draw"):
            self.states[-1].on_draw()
    
    def on_mouse_press(self,*args):
        if hasattr(self.states[-1],"on_mouse_press"):
            self.states[-1].on_mouse_press(*args)
    
    def on_mouse_motion(self,*args):
        if hasattr(self.states[-1],"on_mouse_motion"):
            self.states[-1].on_mouse_motion(*args)
    
    def on_mouse_scroll(self,*args):
        if hasattr(self.states[-1],"on_mouse_scroll"):
            self.states[-1].on_mouse_scroll(*args)
    
    def on_key_press(self,*args):
        if hasattr(self.states[-1],"on_key_press"):
            self.states[-1].on_key_press(*args)
            
    def on_key_release(self,*args):                 
        if hasattr(self.states[-1],"on_key_release"):
            self.states[-1].on_key_release(*args)
    
class PlayLevel(object):
    def __init__(self,win,x,y):
        self.win = win
        self.grid = Grid(self.win,Rect((0,20),(self.win.width,self.win.height-40)),x,y)
        self.grid.build_perfect_grid()
        
        allowed_time = 60*max((x,y))
        #allowed_time = 5
        
        self.score_bar = ProgressBar(Rect((0,0),(self.win.width,20)),0,self.grid.max,(0,255,0),(255,0,0),0)
        self.time_bar = TimeBar(Rect((0,self.win.height-20),(self.win.width,20)),0,allowed_time,(0,255,0),(255,0,0))
        self.grid.degrid_all()
        
        self.show_scores = False
        
    def activate(self):
        pyglet.clock.schedule_interval(self.tick_down, .1)
    
    def deactivate(self):
        pyglet.clock.unschedule(self.tick_down)
        
    def tick_down(self,something):
        self.time_bar.val-=.1
        if self.time_bar.val < 0:
            self.end()
            self.time_bar.val = 0
        elif self.score_bar.val >= self.score_bar.max:
            self.end()
            
    def end(self):
        pyglet.clock.unschedule(self.tick_down)
        self.grid.highlight_invalids()
        self.show_scores = True
        if self.grid.score(True) == self.score_bar.max:
            print "YOU ARE AWSOME"
        else:
            print "YOU LOSE"
            
    def update(self):
        self.score_bar.val = self.grid.score()
        
        
        
    def on_mouse_press(self,x,y,button,modifiers):
        if not self.show_scores > 0:
            if button == pyglet.window.mouse.LEFT:
                if not self.grid.grab(x,y):
                    self.grid.drop(x,y)
            else:
                if self.grid.dragging:
                    self.grid.dragging.rotate(1)
                else:
                    tile = self.grid.tile_at(x,y)
                    if tile:
                        tile.rotate(1)
    
            self.update()
            self.on_mouse_motion(x,y,0,0)
        elif self.show_scores > 0:
            self.win.pop_scene()
            
            
    def on_mouse_motion(self,x,y,dx,dy):
        if (not self.show_scores > 0) and self.grid.dragging: self.grid.dragging.set_position(x,y)
    
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if not self.show_scores > 0:
            if self.grid.dragging:
                if scroll_y < 0:
                    self.grid.dragging.rotate(CCW)
                else:
                    self.grid.dragging.rotate(CW)
            self.update()
        
    def on_key_press(self,symbol, modifiers):
        if symbol == key.TAB:
                self.show_scores = -1
        elif not self.show_scores > 0:
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
            elif symbol == key.ENTER:
                self.grid.degrid_invalid()
            elif symbol == key.ESCAPE:
                self.win.push_scene(PauseMenu(self.win,self))
            self.update()
        else:
            self.win.pop_scene()
            
    def on_key_release(self,symbol,modifiers):
        if symbol == key.TAB:
            self.show_scores = 0
            
    
    def on_draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.grid.draw()
        self.score_bar.draw()
        self.time_bar.draw()
        if self.show_scores:
            self.grid.draw_scores()

class ZenLevel(PlayLevel):
    def __init__(self,win,x,y):
        self.win = win
        self.grid = Grid(self.win,Rect((0,20),(self.win.width,self.win.height-20)),x,y)
        self.grid.build_perfect_grid()
        
        self.score_bar = ProgressBar(Rect((0,0),(self.win.width,20)),0,self.grid.max,(0,255,0),(255,0,0),0)
        self.grid.degrid_all()
        
        self.show_scores = False
        
    def activate(self):
        pass
    
    def update(self):
        super(ZenLevel,self).update()
        self.grid.highlight_invalids()
        
    def on_draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.grid.draw()
        self.score_bar.draw()
        if self.show_scores:
            self.grid.draw_scores()
    
        
class Menu(object):
    def __init__(self, win):
        self.items = []
        self.win = win
        
        self.pad_x = 150
        self.pad_y = 25
        
        self.heading = pyglet.text.Label("Testing",
                  font_name='Square721 BT',
                  font_size=60,
                  anchor_x="center",
                  anchor_y="center",
                  x=self.win.width//2,
                  y=int(self.win.height*0.85))
        
    def activate(self):
        pass
    
    def deactivate(self):
        pass

    def set_heading(self,text):
        self.heading.text = text
    
    def add_item(self,text,func):
        item = pyglet.text.Label(text,
                  font_name='Square721 BT',
                  font_size=25,
                  anchor_x="center",
                  anchor_y="center",
                  x=self.win.width/2,
                  y=self.heading.y-140-len(self.items)*3*self.pad_y)
        self.items.append([item,func])
        
    def on_mouse_press(self,x,y,buttons,modifiers):
        for item, func in self.items:
            if abs(item.y-y) < self.pad_y and abs(item.x-x) < self.pad_x:
                func()
                return
        
    def on_draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glColor3ub(255,255,255)
        self.heading.draw()
        for label, func in self.items:
            label.draw()
            gl.glBegin(gl.GL_LINE_LOOP)
            gl.glVertex2f(label.x-self.pad_x,label.y-self.pad_y)
            gl.glVertex2f(label.x+self.pad_x,label.y-self.pad_y)
            gl.glVertex2f(label.x+self.pad_x,label.y+self.pad_y)
            gl.glVertex2f(label.x-self.pad_x,label.y+self.pad_y)
            gl.glEnd()
        
class MainMenu(Menu):
    def __init__(self,win):
        super(MainMenu,self).__init__(win)
        
        self.set_heading("citySquare")
        self.heading.font_size = 80
        self.add_item("Time Challenge",self.time_challenge)
        self.add_item("Zen Mode",self.zen_mode)
        self.add_item("How to play",self.how_to_play)
    
    def time_challenge(self):
        self.win.push_scene(TimeLevelMenu(self.win))
    
    def zen_mode(self):
        self.win.push_scene(ZenMenu(self.win))
        
    def how_to_play(self):
        try:
            os.startfile(os.path.abspath("res/how-to-play.html"))
        except AttributeError:
            os.system("open " + os.path.abspath("res/how-to-play.html"))
            
class TimeLevelMenu(Menu):
    def __init__(self,win):
        super(TimeLevelMenu,self).__init__(win)
        self.set_heading("Difficulty")
        self.add_item("Easy 3x3",self.play3)
        self.add_item("Challenging 5x5",self.play5)
        self.add_item("Damn Hard 7x7",self.play7)
        self.add_item("Nightmare 9x9",self.play9)
        self.add_item("Back",self.back)
    
    def play3(self):
        self.win.push_scene(PlayLevel(self.win,3,3))
    def play5(self):
        self.win.push_scene(PlayLevel(self.win,5,5))
    def play7(self):
        self.win.push_scene(PlayLevel(self.win,7,7))
    def play9(self):
        self.win.push_scene(PlayLevel(self.win,9,9))
    def back(self):
        self.win.pop_scene()
        
class ZenMenu(Menu):
    def __init__(self,win):
        super(ZenMenu,self).__init__(win)
        self.set_heading("Difficulty")
        self.add_item("+",self.increase)
        self.add_item("Play 5x5",self.play)
        self.add_item("-",self.decrease)
        self.difficulty = 5
    
    def decrease(self):
        self.difficulty = max(2,self.difficulty-1)
        self.items[1][0].text = "Play %dx%d"%(self.difficulty,self.difficulty)
    def increase(self):
        self.difficulty = min(9,self.difficulty+1)
        self.items[1][0].text = "Play %dx%d"%(self.difficulty,self.difficulty)
    def play(self):
        self.win.push_scene(ZenLevel(self.win,self.difficulty,self.difficulty))
    
        
class PauseMenu(Menu):
    def __init__(self,win,game):
        super(PauseMenu,self).__init__(win)
        self.game = game
        self.set_heading("Paused")
        self.add_item("Resume",self.resume)
        self.add_item("End Game",self.end_game)
    def end_game(self):
        self.win.pop_scene()
        self.game.end()
    def resume(self):
        self.win.pop_scene()

    
if WINDOW_SIZE == None:
    win = GameWindow(fullscreen=True)
else:
    win = GameWindow(width=WINDOW_SIZE[0],height=WINDOW_SIZE[1])
pyglet.app.run()


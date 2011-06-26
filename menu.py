import pyglet
from pyglet import gl

## TextLayout.content_width
class Menu(object):
    def __init__(self,win,x_margin=20, y_margin = 20, top = 220):
        self.win = win
        self.x_margin = x_margin
        self.y_margin = y_margin
        self.top = top
        self.items = []
        
        self.heading = pyglet.text.Label("Placeholder",
                  font_name='Square721 BT',
                  font_size=70,
                  anchor_x="center",
                  anchor_y="center",
                  x=self.win.width//2,
                  y=self.win.height-100)
    
    def activate(self):
        pass   
    def deactivate(self):
        pass
    def _arrange(self):
        y = self.win.height-self.top
        for row in self.items:
            y-= row[0].text.content_height//2
            row_width = sum([item.text.width + item.x_pad*2 for item in row],(len(row)-1)*self.x_margin)
            x = (self.win.width-row_width)//2
            for item in row:
                x += item.text.width//2 +item.x_pad
                item.text.y = y
                item.text.x = x
                x += item.text.width//2 + self.x_margin + item.x_pad
            y -= row[0].text.content_height//2 + row[0].y_pad + self.y_margin

    def set_heading(self,heading):
        self.heading.text = heading

    def add_items(self,items,row=None):
        if type(items) != list:
            items = [items]
        if row == None:
            self.items.append(items)
        else:
            self.items[row].extend(items)
            
        self._arrange()
    def on_mouse_press(self,x,y,button,modifiers):
        for row in self.items:
            for item in row:
                if item.point_over(x,y):
                    item.function()
    def on_draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glColor3ub(255,255,255)
        self.heading.draw()
        for row in self.items:
            for item in row:
                item.draw()
    
class MenuItem(object):
    def __init__(self, text, func, width=360, height=None, x_pad=10, y_pad=5, size=30, border=True, multiline=False):
        self.function = func
        self.x_pad = x_pad
        self.y_pad = y_pad
        self.border = border
        
        self.x = self.y = 0
        
        self.text = pyglet.text.Label(text,
                  font_name='Square721 BT',
                  font_size=size,
                  anchor_x="center",
                  #halign = "center",
                  anchor_y="center",
                  width = width,
                  height = height,
                  multiline = multiline)
        
        font = self.text.document.get_font()
        #self.text.height =  font.ascent - font.descent
        
    def point_over(self,x,y):
        w = (self.text.width)//2 + self.x_pad
        h = (self.text.content_height)//2 + self.y_pad
        if self.text.x-w <= x <= self.text.x+w and self.text.y-h <= y <= self.text.y+h:
            return True
        return False
        
        
    def draw(self):
        self.text.draw()
        if self.border:
            x = self.text.x
            y = self.text.y-2
            w = self.text.width//2 + self.x_pad
            h = self.text.content_height//2 + self.y_pad
            gl.glBegin(gl.GL_LINE_LOOP)
            gl.glVertex2f(x-w,y-h)
            gl.glVertex2f(x-w,y+h)
            gl.glVertex2f(x+w,y+h)
            gl.glVertex2f(x+w,y-h)
            gl.glEnd()
        
class EditableMenuItem(MenuItem):
    def __init__(self, text, func, menu, width=360, height=30, x_pad=10, y_pad=5, size=30, border=True, multiline=False):
        self.function = func
        self.menu = menu
        self.x_pad = x_pad
        self.y_pad = y_pad
        self.border = border
        
        self.x = self.y = 0
        
        self.default = True
        
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.document.set_style(0,
                                len(self.document.text),
                                dict(color=(100, 100, 100, 255),
                                     font_name='Square721 BT',
                                     font_size=size,
                                     align="center")
                                )
        font = self.document.get_font()

        self.text = pyglet.text.layout.IncrementalTextLayout(self.document,
                                                             width = width,
                                                             height = font.ascent - font.descent,
                                                             multiline=True)
        self.text.anchor_x="center"
        self.text.anchor_y="center"
        self.caret = pyglet.text.caret.Caret(self.text,color=(255, 255, 255))
        self.caret.visible=True
        self.caret.mark=self.caret.position=len(self.text.document.text)
        
    def wipe_default(self):
        if self.default:
            self.text.document.text = ""
            self.text.document.set_style(0,-1,{"color":(255, 255, 255, 255)})
        self.default = False
    
    def on_text(self,text):
        self.caret.on_text(text)
        self.text.anchor_x="center"
        self.text.anchor_y="center"
        self.menu._arrange()
        
    def on_text_motion(self,motion):
        self.caret.on_text_motion(motion)
        self.text.anchor_x="center"
        self.text.anchor_y="center"
        self.menu._arrange()

    def hit_test(self, x, y):
        return (0 < x - self.layout.x < self.layout.width and
                0 < y - self.layout.y < self.layout.height)
# citySquare #

This is my entry for PyWeek 2011, more info can be found at its [homepage](http://www.pyweek.org/e/citySquare/) on the PyWeek website.

## Requirements ##

+ pyglet

**Note** resolution can be easily adjusted at the start of `main.py`, specifically the following:

    WINDOW_SIZE = (768,616)

Set this to `None` to enter fullscreen mode
    
## How to Play ##


The aim of citySquare is to match up the tiles from the tray on the right on the grid as best as is possible in a given amount of time. Points are awarded for **completed** cities (the somewhat poorly drawn orange bits) and roads. They are however taken away if the city or road is **incomplete**.

Also note that scoring is skewed to give more points to **large** cities, so you should really be trying to make your cities as large as possible within the time limit. Finally, ensure that all of your tiles match up, and that any tiles touching the edge of the grid are grass, any invalid ignored for scoring purposes, *don't waste those tiles!*

### Controls ###

The controls are fairly straigtforward, click a tile to pick it up click again to drop it. Dragging and dropping will not work, you actually have to click and let go.

Tiles can be rotated by right-clicking them or by by picking up a tile and scrolling. All of the tiles currently on the grid can be shifted around using the arrow keys. To view a breakdown of your score so far you can press hold tab.
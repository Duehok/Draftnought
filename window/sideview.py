"""Side view display of the ship"""

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from window.framework import Subscriber

_WIDTH = 701
_MAX_HEIGHT = 5000
_GRID_STEPS = 25
_GRID_RGBA = (0, 0, 0, 125)

class SideView(tk.Canvas, Subscriber):
    """Display the side view picture if one is defined in the ship data

    Can pan with mouse drag
    TODO:debug the initial height calculations

    Args:
        parent (tk.Frame): the parent frame where the picture goes
        shipdata (model.shipdata): shipdata that has, or does not have, a side_pict
        parameters: all the parameters for the program
    """
    def __init__(self, parent, ship_data, parameters, sideview):
        self._parameters = parameters
        Subscriber.__init__(self, sideview)
        if ship_data.side_pict:
            self._image = ship_data.side_pict
            borderwidth = 2
        else:
            self._image = Image.new(mode="RGBA", size=(1, 1), color=(0, 0, 0, 0))
            borderwidth = 0
        self._tkimage = ImageTk.PhotoImage(self._image)
        height = min(self._tkimage.height(), _MAX_HEIGHT)
        tk.Canvas.__init__(self, parent,
                           width=_WIDTH,
                           height=height,
                           cursor="fleur",
                           borderwidth=borderwidth,
                           xscrollincrement=1,
                           yscrollincrement=1
                           )

        self.xview(tk.SCROLL, round(parameters.sideview_offset), tk.UNITS)

        image_center = (0, round(self._image.height/2.0))
        self._image_id = self.create_image(image_center, image=self._tkimage)
        self.grid()
        self.bind("<B1-Motion>", self._on_move)
        self.bind("<ButtonPress-1>", self._on_click)
        self._left_button_down = False
        self._half_length = ship_data.half_length

        self._grid_on = False
        self._grid = make_grid(self.winfo_reqwidth(), self.winfo_reqheight())
        self._grid_id = -1

        self.bind("<MouseWheel>", self._on_mousewheel)
        self._re_zoom(self._parameters.sideview_zoom)

    def _on_click(self, event):
        """Mark the start of the pan
        no pan along y axis
        """
        self.scan_mark(event.x, 0)

    def _on_move(self, event):
        """If the button is down, pan the view
        no pan along y axis
        """
        self.scan_dragto(event.x, 0, gain=1)
        self._parameters.sideview_offset = self.canvasx(0)
        self.refresh_grid(self._grid_on)

    def _on_mousewheel(self, event):
        """Mouse wheel changes the zoom"""
        if event.delta > 0:
            self._parameters.sideview_zoom = self._parameters.sideview_zoom*1.01
        else:
            self._parameters.sideview_zoom = self._parameters.sideview_zoom*0.99
        self._re_zoom(self._parameters.sideview_zoom)

    def _re_zoom(self, new_zoom):
        """When changing zoom, redraw the pict to the new zoom, resize the canvas"""
        corrected_zoom = new_zoom/self._half_length
        new_size = [round(coord*corrected_zoom) for coord in  self._image.size]
        self._tkimage = ImageTk.PhotoImage(self._image.resize(new_size))
        height = min(self._tkimage.height(), _MAX_HEIGHT)
        self.configure(height=height)
        offset = (self.coords(self._image_id)[0], round(self.winfo_reqheight()/2.0))
        self.delete(self._image_id)
        self._image_id = self.create_image(*offset, image=self._tkimage)
        self._parameters.sideview_offset = self.canvasx(0)
        self.refresh_grid(self._grid_on)

    def refresh_grid(self, grid_on):
        """Update the grid according to grid_on
        Resize the grid if the previous grid was too small
        No resize if the grid is too big!
        """
        self._grid_on = grid_on
        if self._grid_id != -1:
            self.delete(self._grid_id)
        if grid_on:
            if (self._grid.height() < self.winfo_reqheight() or
                    self._grid.width() < self.winfo_reqwidth()):
                self._grid = make_grid(self.winfo_reqwidth(), self.winfo_reqheight())
            self._grid_id = self.create_image((self.canvasx(0),
                                               self.canvasy(0)),
                                              image=self._grid, anchor=tk.NW)

    def _on_notification(self, observable, event_type, event_info):
        if event_type == "Drag":
            self.xview(tk.SCROLL, round(event_info["x"]), tk.UNITS)
            self._parameters.sideview_offset = self.canvasx(0)
            self.refresh_grid(self._grid_on)
        if event_type == "Apply_zoom":
            self._parameters.sideview_zoom = self._parameters.sideview_zoom*event_info["factor"]
            self._re_zoom(self._parameters.sideview_zoom)

def make_grid(width, height, horizontal=False):
    """Build a semi-transparent grid in a picture

    Args:
        width (int): width of final image
        height (int): height of final image
        horizontal (bool): if true, the grid has horizontal and vertical lines
            if false, vertical only
    """
    grid = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid)
    for x_coord in range(0, width, _GRID_STEPS):
        draw.line([(x_coord, 0), (x_coord, height)], width=1, fill=_GRID_RGBA)

    if horizontal:
        draw.line([(0, height/2+1), (width, height/2+1)], width=1, fill=_GRID_RGBA)
        for delta_y in range(_GRID_STEPS, int(height/2), _GRID_STEPS):
            draw.line([(0, delta_y+ int(height/2)+1), (width, delta_y+ int(height/2)+1)],
                      width=1, fill=_GRID_RGBA)
            draw.line([(0, int(height/2)+1- delta_y), (width, int(height/2)+1- delta_y)],
                      width=1, fill=_GRID_RGBA)
    return ImageTk.PhotoImage(grid)

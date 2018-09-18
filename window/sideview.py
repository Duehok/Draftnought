"""Side view display of the ship"""

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw

_WIDTH = 701
_GRID_STEPS = 25
_GRID_RGBA = (0, 0, 0, 125)

class SideView(tk.Frame):
    """Display the side view picture if one is defined in the ship data

    Can pan with mouse drag
    TODO:debug the initial height calculations

    Args:
        parent (tk.Frame): the parent frame where the picture goes
        shipdata (model.shipdata): shipdata that has, or does not have, a side_pict
    """
    def __init__(self, parent, ship_data, parameters):
        super().__init__(parent)
        self._parameters = parameters
        self._ship_data = ship_data
        self._image = ImageTk.PhotoImage(ship_data.side_pict)
        self._canvas = tk.Canvas(self, width=_WIDTH, height=self._image.height())

        self._image_id = self._canvas.create_image((0, 0), image=self._image, anchor=tk.NW)
        self._canvas.grid()
        self._canvas.bind("<Motion>", self._on_move)
        self._canvas.bind("<ButtonPress-1>", self._on_click)
        self._canvas.bind("<ButtonRelease-1>", self._on_unclick)
        self._left_button_down = False

        self._grid_on = False
        self._grid = make_grid(self._canvas.winfo_reqwidth(), self._canvas.winfo_reqheight())
        self._grid_id = -1

        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._re_zoom(self._parameters.zoom)
        self._canvas.coords(self._image_id, *self._parameters.offset)

    def _on_click(self, event):
        self._left_button_down = True
        self._canvas.scan_mark(event.x, event.y)

    def _on_unclick(self, _event):
        self._left_button_down = False

    def _on_move(self, event):
        if self._left_button_down:
            self._canvas.scan_dragto(event.x, event.y, gain=1)
            pict_ccord = self._canvas.coords(self._image_id)
            self._parameters.offset = (-self._canvas.canvasx(-pict_ccord[0]),
                                       -self._canvas.canvasy(-pict_ccord[1]))
            self.switch_grid(self._grid_on)

    def _on_mousewheel(self, event):
        if event.delta > 0:
            self._parameters.zoom = self._parameters.zoom*1.01
        else:
            self._parameters.zoom = self._parameters.zoom*0.99
        self._re_zoom(self._parameters.zoom)

    def _re_zoom(self, new_zoom):
        offset = self._canvas.coords(self._image_id)
        self._canvas.delete(self._image_id)
        new_size = [round(coord*new_zoom) for coord in self._ship_data.side_pict.size]
        self._image = ImageTk.PhotoImage(self._ship_data.side_pict.resize(new_size))
        self._image_id = self._canvas.create_image(*offset, image=self._image, anchor=tk.NW)
        self.switch_grid(self._grid_on)


    def switch_grid(self, grid_on):
        """Display or hide the grid according to grid_on"""
        self._grid_on = grid_on
        if self._grid_id != -1:
            self._canvas.delete(self._grid_id)
        if grid_on:
            self._grid_id = self._canvas.create_image((self._canvas.canvasx(0),
                                                       self._canvas.canvasy(0)),
                                                      image=self._grid, anchor=tk.NW)

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

"""Side view display of the ship"""

import tkinter as tk
from PIL import Image, ImageTk

_WIDTH = 700

class SideView(tk.Frame):
    """Display the side view picture if one is defined in the ship data

    Can pan with mouse drag
    TODO: zoom
    TODO: ensure width is same as top view
    TODO: sane default so that generated picture from RTW align with the top view
    TODO: link pan and zoom to top view
    TODO: grid to help alignement with top view

    Args:
        parent (tk.Frame): the parent frame where the picture goes
        shipdata (model.shipdata): shipdata that has, or does not have, a side_pict
    """
    def __init__(self, parent, ship_data):
        super().__init__(parent)
        if ship_data.side_pict is not None:
            self._ship_data = ship_data
            self._image = ImageTk.PhotoImage(ship_data.side_pict)
            self._ratio = 1.0
            self._canvas = tk.Canvas(self, width=_WIDTH, height=self._image.height())
            self._pict_id = self._canvas.create_image((0, 0), image=self._image, anchor=tk.NW)
            self._canvas.grid()
            self._canvas.bind("<Motion>", self._on_move)
            self._canvas.bind("<ButtonPress-1>", self._on_click)
            self._canvas.bind("<ButtonRelease-1>", self._on_unclick)
            self._left_button_down = False

            self._canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_click(self, event):
        self._left_button_down = True
        self._canvas.scan_mark(event.x, event.y)

    def _on_unclick(self, _event):
        self._left_button_down = False

    def _on_move(self, event):
        if self._left_button_down:
            self._canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_mousewheel(self, event):
        if event.delta >0:
            self._ratio = self._ratio*1.05
        else:
            self._ratio = self._ratio*0.95
        self._canvas.delete(self._pict_id)
        new_size = [round(coord*self._ratio) for coord in self._ship_data.side_pict.size]
        self._image = ImageTk.PhotoImage(self._ship_data.side_pict.resize(new_size))
        self._pict_id = self._canvas.create_image((0, 0), image=self._image, anchor=tk.NW)


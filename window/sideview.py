"""Side view display of the ship"""

import tkinter as tk
from PIL import ImageTk

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
            self._image = ImageTk.PhotoImage(ship_data.side_pict)
            self._canvas = tk.Canvas(self, width=self._image.width(), height=self._image.height())
            self._canvas.create_image((0, 0), image=self._image, anchor=tk.NW)
            self._canvas.grid()
            self._canvas.bind("<Motion>", self._on_move)
            self._canvas.bind("<ButtonPress-1>", self._on_click)
            self._canvas.bind("<ButtonRelease-1>", self._on_unclick)
            self._left_button_down = False

    def _on_click(self, event):
        self._left_button_down = True
        self._canvas.scan_mark(event.x, event.y)

    def _on_unclick(self, _event):
        self._left_button_down = False

    def _on_move(self, event):
        if self._left_button_down:
            self._canvas.scan_dragto(event.x, event.y, gain=1)

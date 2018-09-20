"""Everything to edit the funnels"""

import tkinter as tk
from tkinter.ttk import Checkbutton, Entry, Label
from window.framework import Subscriber, Observable, is_int
import model.funnel


class FunnelEditor(tk.Frame, Subscriber, Observable):
    """Editor for one funnel
    Args:
        parent (tk.Frame): parent widget
        funnel (model.shipdata.Funnel): self explanatory
        index (int): just a number to indicate the funnel's number. Display only
        command_stack (framework.Command_stack): undo/redo stack
    """
    def __init__(self, parent, funnel, index, command_stack):
        tk.Frame.__init__(self, parent, borderwidth=4)
        Subscriber.__init__(self, funnel)
        Observable.__init__(self)
        self._funnel = funnel
        self._command_stack = command_stack
        self._active_var = tk.IntVar()
        self._active_var.trace_add("write", self._switch_active)
        self._position_var = tk.StringVar()
        self._position_var.trace_add("write", self._set_position)
        self._oval_var = tk.IntVar()
        self._oval_var.trace_add("write", self._switch_oval)

        self._update()
        self.bind("<Button-1>", self._update)

        Checkbutton(self, text=f"Funnel n°{index}:  ", variable=self._active_var).grid(columnspan=3)
        pos_label = Label(self, text="  Position: ")
        pos_label.grid(sticky=tk.E)
        pos_label.bind("<Button-1>", self._update)
        pos_entry = Entry(self, textvariable=self._position_var, width=6)
        pos_entry.grid(row=1, column=1, sticky=tk.W)
        pos_entry.bind("<FocusIn>", self._update)
        Checkbutton(self, text="Is Oval", variable=self._oval_var).grid(row=1, column=2)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

    def _on_notification(self, observable, event_type, event_info):
        self._update()

    def _update(self, *_args):
        """Set all the displayed info to what is in the funnel data
        """
        #flags to avoid circular update of the values
        self._updating = True
        self._active_var.set(int(self._funnel.position != 0))
        self._position_var.set(round(self._funnel.position, 1))
        self._oval_var.set(self._funnel.oval)
        self._notify("Update", {"Position":self.position, "Oval": self.oval})
        self._updating = False

    def _set_position(self, _var_name, _list_index, _operation):
        """Called when the position of a funnel is modified
        """
        if not self._updating and is_int(self._position_var.get()):
            self._command_stack.do(model.funnel.MoveFunnel(self._funnel,
                                                           int(self._position_var.get())))

    def _switch_active(self, _var_name, _list_index, _operation):
        """Called when switching the funnel on and off
        """
        if not self._updating:
            if not bool(self._active_var.get()):
                self._command_stack.do(model.funnel.MoveFunnel(self._funnel, 0))
            else:
                self._command_stack.do(model.funnel.MoveFunnel(self._funnel, 1))

    def _switch_oval(self, _var_name, _list_index, _operation):
        """Called when switching the funnel from oval to circular and vice-versa
        """
        if not self._updating:
            self._command_stack.do(model.funnel.OvalFunnel(self._funnel,
                                                           bool(self._oval_var.get())))

    def update_to_coord(self, point):
        """Move the funnel to the Y position of the given point

        Intended to be called from click on the top view
        point in funnel coordinates
        """
        self._command_stack.do(model.funnel.MoveFunnel(self._funnel,
                                                       point[1]))

    @property
    def oval(self):
        """Pipe throught the funnel's data state"""
        return self._funnel.oval

    @property
    def position(self):
        """Pipe throught the funnel's data state"""
        return self._funnel.position

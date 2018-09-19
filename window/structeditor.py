"""All the classes to display the points and properties of a structure and edti them
"""
import tkinter as tk
from tkinter.ttk import Treeview, Scrollbar, Entry, Label, Checkbutton, Button, Style
import model.shipdata
import model.structure
from window.framework import Subscriber, Observable

VISIBLE_POINTS = 10
EDIT_ZONE_COL = 0
POINTS_TABLE_COL = EDIT_ZONE_COL+1
SCROLL_COL = POINTS_TABLE_COL+1

class StructEditor(tk.Frame, Subscriber, Observable):
    """Displays and allow editing of the coordinates and points of one superstructure

    Args:
        parent (tk.Frame): widget that is the parent of the editor
        structure (model.structure.Structure): the ship superstructure that will be edited
    """
    def __init__(self, parent, structure, command_stack):
        Subscriber.__init__(self, structure)
        Observable.__init__(self)
        tk.Frame.__init__(self, parent, borderwidth=4, relief="raised")
        self._structure = structure
        self._command_stack = command_stack

        self.bind("<Button-1>", self._on_get_focus)

        self._tree = Treeview(self, columns=["#", "X", "Y"], selectmode="browse")
        #kill the icon column
        self._tree.column("#0", minwidth=0, width=0)

        style = Style()
        style.configure("Treeview.Heading", font=(None, 16))

        self._tree.column("#", minwidth=20, width=40)
        self._tree.column("X", minwidth=20, width=40)
        self._tree.column("Y", minwidth=20, width=40)
        self._tree.heading("#", text="#")
        self._tree.heading("X", text="\u21d5")
        self._tree.heading("Y", text="\u21d4")
        self._tree.grid(row=0, column=POINTS_TABLE_COL, sticky=tk.N+tk.S)

        self._tree.bind("<<TreeviewSelect>>", self._on_point_selected)
        self._tree.bind("<FocusIn>", self._on_get_focus)

        scroll = Scrollbar(self, command=self._tree.yview)
        scroll.grid(row=0, column=SCROLL_COL, sticky=tk.N+tk.S)
        scroll.bind("<FocusIn>", self._on_get_focus)

        self._tree.configure(yscrollcommand=scroll.set)

        self._index_of_sel_point = -1
        self._fill_tree()

        self._edit_zone = EditZone(self, self._structure, command_stack, self._on_get_focus)
        self._edit_zone.grid(column=EDIT_ZONE_COL, row=0, sticky=tk.N)

    def _force_selection(self, new_sel_index):
        """Set the selected point to the new_sel_index

        Gives correct focus, update, etc to the editor's widgets
        if the index is outside of the self.points, does nothing
        """
        if new_sel_index >= 0 and new_sel_index <= len(self.points) -1:
            iid = self._tree.get_children()[new_sel_index]
            self._tree.focus(iid)
            self._tree.selection_set(iid)

    def _on_get_focus(self, *_args):
        if self._index_of_sel_point == -1:
            self._force_selection(0)
        self._notify("focus", {})

    def _on_point_selected(self, _event):
        """called back when a point is selected in the table/treeview

        Updates the editable fields
        """
        selected_iid = self._tree.focus()
        self._index_of_sel_point = self._tree.index(selected_iid)
        self._edit_zone.set_editable_point(self._tree.item(selected_iid)["values"][0])
        self._notify("focus", {})

    def _fill_tree(self):
        """fills the treeview with data from the structure
        """
        self._tree.delete(*self._tree.get_children())
        for point_index, point in enumerate(self._structure.points):
            self._tree.insert('', 'end', values=[point_index, round(point[0]), round(point[1])])
            if point_index == self._index_of_sel_point:
                self._force_selection(point_index)

    def _on_notification(self, observable, event_type, event_info):
        """Rebuild the treeview on structure update
        Depending on the structure state and the operation, change the selcted point
        """
        if event_type == "add_point":
            self._index_of_sel_point = event_info["index"]
            self._fill_tree()
        else:
            if self._index_of_sel_point >= len(self._structure.points):
                self._index_of_sel_point = len(self._structure.points)
                self._edit_zone.unset_point()
            self._fill_tree()
        self._notify("focus", {})

    def update_to_coord(self, point):
        """Move the selected point to the position of the given point

        Intended to be called from click on the top view
        Args:
            point (x, y): new position in funnel coordinates
        """
        if self._index_of_sel_point != -1 and self._index_of_sel_point <= len(self.points)-1:
            self._command_stack.do(model.structure.UpdatePoint(
                self._structure, self._index_of_sel_point, point[0], point[1]))
        elif self._index_of_sel_point == len(self.points) or not self.points:
            self._command_stack.do(model.structure.AddPoint(self._structure,
                                                            self._index_of_sel_point+1,
                                                            *point))
        if self._index_of_sel_point+1 >= len(self.points):
            self.winfo_toplevel().update()
            self._index_of_sel_point = len(self.points)
        else:
            self._force_selection(self._index_of_sel_point+1)
            self.winfo_toplevel().update()

    @property
    def points(self):
        """Pipe throught the struct's properties"""
        return self._structure.points

    @property
    def fill(self):
        """Pipe throught the struct's properties"""
        return self._structure.fill

    @property
    def selected_index(self):
        """the index in the struct's point list of the currently selected point

        Should be -1 if none selected
        """
        return self._index_of_sel_point

class EditZone(tk.Frame):
    """The data in the treeview cannot be edited in place, so there is an area for editable fields

    Args:
        parent (tk.Frame): widget that is the parent of the editor
        struct_editor (StructEditor): the struct_editor instance in which this widget will be placed
    """
    #TODO: rename constants with an underscore_
    FILL_CHECK_ROW = 0
    POINT_INDEX_ROW = FILL_CHECK_ROW+1
    X_ROW = POINT_INDEX_ROW+1
    Y_ROW = X_ROW+1
    ADD_ROW = Y_ROW+1
    DEL_ROW = ADD_ROW+1
    SYMM_ROW = DEL_ROW+1

    def __init__(self, parent, structure, command_stack, on_get_focus):
        tk.Frame.__init__(self, parent)
        self.command_stack = command_stack
        self._structure = structure
        self._fill_var = tk.IntVar()
        self._fill_var.set(self._structure.fill)

        (Checkbutton(self, text="Fill", variable=self._fill_var)
         .grid(row=EditZone.FILL_CHECK_ROW, column=0, columnspan=2))

        self._fill_var.trace_add("write", self._set_fill)

        self._point_index = -1
        self._point_index_var = tk.StringVar()
        top_label = Label(self, textvariable=self._point_index_var)
        top_label.grid(row=EditZone.POINT_INDEX_ROW, column=0, columnspan=2)
        top_label.bind("<Button-1>", on_get_focus)

        x_label = Label(self, text="\u21d5:")
        x_label.grid(row=EditZone.X_ROW, column=0, sticky=tk.E)
        x_label.bind("<Button-1>", on_get_focus)
        y_label = Label(self, text="\u21d4:")
        y_label.grid(row=EditZone.Y_ROW, column=0, sticky=tk.E)
        y_label.bind("<Button-1>", on_get_focus)
        #the updating_ booleans allow to detect if the stringvars are edited
        #because the point is selected
        #or if the user changed their value
        self.inhibit_callbacks = True
        self.editable_x = tk.StringVar()
        self.editable_y = tk.StringVar()

        setx = Entry(self, textvariable=self.editable_x, width=6)
        setx.grid(row=EditZone.X_ROW, column=1, sticky=tk.W)
        setx.bind("<FocusIn>", on_get_focus)
        sety = Entry(self, textvariable=self.editable_y, width=6)
        sety.grid(row=EditZone.Y_ROW, column=1, sticky=tk.W)
        sety.bind("<FocusIn>", on_get_focus)

        self.editable_x.trace_add("write", self._point_edited)
        self.editable_y.trace_add("write", self._point_edited)

        (Button(self, text="Add Point", command=self._add_point)
         .grid(row=EditZone.ADD_ROW, column=0, columnspan=2))
        (Button(self, text="Delete", command=self._delete_point)
         .grid(row=EditZone.DEL_ROW, column=0, columnspan=2))
        (Button(self, text="Apply Symmetry", command=self._apply_symmetry)
         .grid(row=EditZone.SYMM_ROW, column=0, columnspan=2))

    def set_editable_point(self, point_index):
        """Called when another point is selected

        set the editable fields and point index display

        Args:
            point-index (int): the index of the point in the superstructure
            x (number): x coordinate of the point
            y (number): y coordinate of the point
        """
        self._point_index = point_index
        #flags: the stringvar will change because the point is selected
        #checked in the callback to only modify the structure if the user edits the fields
        self.inhibit_callbacks = True

        self._point_index_var.set(f"Vertex {self._point_index}")
        self.editable_x.set(round(self._structure.points[point_index][0], 1))
        self.editable_y.set(round(self._structure.points[point_index][1], 1))

        self.inhibit_callbacks = False

    def unset_point(self):
        """Empty the fields when no point is selected (eg: structure is empty)
        """
        self.inhibit_callbacks = True
        self._point_index = -1
        self._point_index_var.set("")
        self.editable_x.set("")
        self.editable_y.set("")

    def _point_edited(self, _var_name, _list_index, _operation):
        """called back by the stringvar of the point's coordinates

        the parameters are there only to swallow the events' params
        """
        #update the point only if:
        #- the user edited the var (not just a point selection)
        #- the input string can be parsed to ints
        if (not self.inhibit_callbacks and
                is_float(self.editable_x.get()) and is_float(self.editable_y.get())):
            self.command_stack.do(model.structure.UpdatePoint(self._structure,
                                                              self._point_index,
                                                              float(self.editable_x.get()),
                                                              float(self.editable_y.get())))

    def _set_fill(self, _var_name, _list_index, _operation):
        """Called when the user switch from filled structure to lines only or the opposite

        Update the structure with the new state
        the parameters are there only to swallow the events' params
        """
        self.command_stack.do(model.structure.SetFill(self._structure, bool(self._fill_var.get())))

    def _delete_point(self):
        """Called when the user delete a point

        Update the structure
        the parameters are there only to swallow the events' params
        """
        if self._point_index >= 0 and self._point_index < len(self._structure.points):
            self.command_stack.do(model.structure.DeletePoint(self._structure, self._point_index))

    def _add_point(self):
        """Called when the user delete a point

        Update the structure
        the parameters are there only to swallow the events' params
        """
        self.command_stack.do(model.structure.AddPoint(self._structure, self._point_index+1, 0, 0))

    def _apply_symmetry(self):
        self.command_stack.do(model.structure.ApplySymmetry(self._structure))

def is_float(possible_number):
    """Returns true if the passed string can be parsed to a float, false if not

    Args:
    possible_number (str):
    """
    try:
        float(possible_number)
        return True
    except ValueError:
        return False

"""Entry point for the whole program

Builds the main window menu bar and TODO: associated keyboard shortcuts
Manages root functions: load program config, load file, save file.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import sys
import logging
import pathlib
from window import topview, structeditor, funnelseditor, sideview
from window.framework import CommandStack
import model.shipdata as sd
import parameters_loader

_SIDEVIEW_ROW = 0
_TOPVIEW_ROW = _SIDEVIEW_ROW+1
_SIDEVIEW_COL = 1
_TOPVIEW_COL = _SIDEVIEW_COL

_FUNNELS_ROW = _TOPVIEW_ROW

_STRUCT_EDITORS_ROW = _TOPVIEW_ROW+1

class MainWindow(tk.Tk):
    """Base class for the whole UI

    Args:
        parameters (parameters_loader.Parameters): all the parameters for the app and the ship data
    """
    def __init__(self, parameters):
        super().__init__()
        self.iconbitmap('icon.ico')
        self.resizable(False, False)
        self.parameters = parameters
        self.command_stack = CommandStack()

        menubar = tk.Menu(self)
        self.config(menu=menubar)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Open File', command=self.do_load, accelerator="Ctrl+O")
        filemenu.add_separator()
        filemenu.add_command(label='Save as', command=self.do_save_as, accelerator="Ctrl+Shift+S")
        filemenu.add_command(label='Save', command=self.do_save, accelerator="Ctrl+S")

        editmenu = tk.Menu(menubar, tearoff=0)
        editmenu.add_command(label='Undo', command=self.do_undo, accelerator="Ctrl+Z")
        editmenu.add_command(label='Redo', command=self.do_redo, accelerator="Ctrl+Y")

        menubar.add_cascade(label='File', menu=filemenu)
        menubar.add_cascade(label='Edit', menu=editmenu)

        self.bind("<Control-s>", self.do_save)
        self.bind("<Control-o>", self.do_load)
        self.bind("<Control-S>", self.do_save_as_keyboard)
        self.bind("<Control-z>", self.do_undo)
        self.bind("<Control-y>", self.do_redo)

        self.center_frame = ttk.Button(self, text="Load ship file", command=self.do_load)
        self.center_frame.grid()

        try:
            with open(self.parameters.app_config["last_file_path"]) as file:
                self.load(file.name)
        except OSError:
            return

    def do_undo(self, *_args):
        """undo last command, or deeper in the undoing stack
        """
        self.command_stack.undo()

    def do_redo(self, *_args):
        """redo last command, or deeper in the redoing stack
        """
        self.command_stack.redo()

    def do_load(self, *_args):
        """React to keyboard shortcut"""
        logging.debug("Load file requested")
        path = filedialog.askopenfilename(filetypes=(("ship files", "*.?0d"),
                                                     ("all files", "*.*")))
        if path == "":
            logging.debug("Load canceled")
            return
        else:
            self.load(path)

    def do_save_as_keyboard(self, *_args):
        """React to keyboard shortcut"""
        self.do_save_as()

    def do_save(self, *_args):
        """Save the current file to the same path
        """
        self.do_save_as(self.parameters.app_config["last_file_path"])

    def load(self, path):
        """load a ship file and display it

        Args:
            path (str): ship file's path.
                If none is given, a dialog box is opened to choose it.
        """
        logging.debug("loading %s", path)
        try:
            with open(path) as file:
                self.current_ship_data = sd.ShipData(file, self.parameters)
        except sd.ShipFileInvalidException as error:
            logging.error(error)
            messagebox.showerror(f"Could not load file {pathlib.Path(path).name}", error)
            return

        self.parameters.app_config["last_file_path"] = path

        logging.debug("loading done")
        self.center_frame.destroy()
        #reset the command stack
        new_command_stack = CommandStack()
        #TODO: handle last loading failure
        self.center_frame = ShipEditor(self,
                                       self.current_ship_data,
                                       new_command_stack,
                                       self.parameters)
        self.center_frame.grid(row=0, column=0)
        #if load was OK, forget the old command stack
        self.command_stack = new_command_stack
        self.winfo_toplevel().title(pathlib.Path(path).name)

    def do_save_as(self, path=None):
        """Save the current file, path choosable

        Also saves the path as "last file" to open on the next start

        Args:
            path (str): path to the file
                If none given, a file picker dialog allows to choose a new or existing file
        """
        if path is None:
            file = filedialog.asksaveasfile(mode='w', filetypes=(("ship files", "*.*d"),
                                                                 ("all files", "*.*")))
            if file is not None:
                logging.debug("saving file to %s", file.name)
                self.current_ship_data.write_as_ini(file_object=file)
                self.parameters.app_config["last_file_path"] = file.name
                file.close()
                self.parameters.write_app_param()
        else:
            logging.debug("saving file to %s", path)
            try:
                with open(path, "w") as file:
                    self.current_ship_data.write_as_ini(file_object=file)
            except OSError as error:
                logging.error("Could not save file:\n%s", error)
            self.parameters.app_config["last_file_path"] = path
            self.parameters.write_app_param()

class ShipEditor(tk.Frame):
    """class for the display of the whole editor

        so everything except the menu bar

    Args:
        parent (tk.Frame): parent frame in which the editor willbe displayed
        ship_data (shipdata.ShipData):
        parameters (parameters_loader.Parameters): all the parameters for the app and the ship data
    """
    def __init__(self, parent, ship_data, command_stack, parameters):
        super().__init__(parent)

        funnels_frame = tk.Frame(self)
        funnels_editors = []
        for index, funnel in enumerate(ship_data.funnels.values()):
            funnel_editor = funnelseditor.FunnelEditor(funnels_frame, funnel, index, command_stack)
            funnel_editor.pack()
            funnels_editors.append(funnel_editor)
        funnels_frame.grid(row=_FUNNELS_ROW, column=0)
        struct_frame = tk.Frame(self)
        index_structure = 0
        st_editors = []
        for index_structure, structure in enumerate(ship_data.structures):
            new_st_display = structeditor.StructEditor(struct_frame, structure, command_stack)
            new_st_display.grid(row=0, column=index_structure)
            st_editors.append(new_st_display)
        struct_frame.grid(row=_STRUCT_EDITORS_ROW, column=0, columnspan=2)

        (topview.TopView(self, ship_data, st_editors, funnels_editors, command_stack, parameters)
         .grid(row=_TOPVIEW_ROW, column=_TOPVIEW_COL, sticky=tk.W))

        st_editors[0]._on_get_focus()

        (sideview.SideView(self, ship_data)
         .grid(row=_SIDEVIEW_ROW, column=_SIDEVIEW_COL, sticky=tk.W))

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,stream=sys.stdout )
    MainWindow(parameters_loader.Parameters()).mainloop()

"""Entry point for the whole program

Builds the main window menu bar and associated keyboard shortcuts
Manages root functions: load program config, load file, save file.
"""
import tkinter as tk
from tkinter import filedialog, Text
from tkinter import ttk
import logging
import logging.handlers
import pathlib
import appdirs
from window import topview, structeditor, funnelseditor, sideview
from window.framework import CommandStack
import model.shipdata as sd
import parameters_loader

summary = logging.getLogger("Summary")
summary.setLevel(logging.DEBUG)

log_filename = pathlib.Path(appdirs.user_data_dir("Drafnought")).joinpath("log.txt")
details = logging.getLogger("Details")
details.setLevel(logging.DEBUG)
file_handler = logging.handlers.RotatingFileHandler(
    log_filename, maxBytes=500*1000, backupCount=5)
details.addHandler(file_handler)


_MAIN_ROW = 0

_LOG_ROW = _MAIN_ROW +1

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
    def __init__(self):
        super().__init__()
        self.iconbitmap('icon.ico')
        self.resizable(False, False)
        self.command_stack = CommandStack()

        logging_frame = tk.Frame(self)
        log_scroll = tk.Scrollbar(logging_frame)
        log_scroll.grid(row=0, column=1, sticky=tk.N+tk.S)
        logging_text = Text(logging_frame, height=6, wrap=tk.WORD, yscrollcommand=log_scroll.set)
        logging_text.grid(row=0, column=0, sticky=tk.W+tk.E)
        logging_frame.grid_columnconfigure(0, weight=1)
        log_scroll.config(command=logging_text.yview)

        summary.addHandler(LogToWidget(logging_text))

        logging_frame.grid(row=_LOG_ROW, sticky=tk.W+tk.E)

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

        self.parameters = parameters_loader.Parameters("")

        self.center_frame = ttk.Button(self, text="Load ship file", command=self.do_load)
        self.center_frame.grid(row=_MAIN_ROW)

        try:
            with open(self.parameters.last_file_path) as file:
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
        path = filedialog.askopenfilename(filetypes=(("ship files", "*.?0d"),
                                                     ("all files", "*.*")))
        if path == "":
            return
        else:
            self.load(path)

    def do_save_as_keyboard(self, *_args):
        """React to keyboard shortcut"""
        self.do_save_as()

    def do_save(self, *_args):
        """Save the current file to the same path
        """
        self.do_save_as(self.parameters.current_file_path)

    def load(self, path):
        """load a ship file and display it

        Args:
            path (str): ship file's path.
                If none is given, a dialog box is opened to choose it.
        """
        summary.debug("loading %s", path)
        self.parameters = parameters_loader.Parameters(path)
        try:
            with open(path) as file:
                self.current_ship_data = sd.ShipData(file, self.parameters)
        except sd.ShipFileInvalidException as error:
            details.error("The file is not correctly formatted to be a ship file!\n%s\n%s",
                          path, error)
            summary.error("The file is not correctly formatted to be a ship file!")
            return

        summary.info("loading successful!")
        self.center_frame.destroy()
        #reset the command stack
        new_command_stack = CommandStack()
        #TODO: handle last loading failure
        self.center_frame = ShipEditor(self,
                                       self.current_ship_data,
                                       new_command_stack,
                                       self.parameters)
        self.center_frame.grid(row=_MAIN_ROW)
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
                summary.debug("saving file to %s", file.name)
                self.current_ship_data.write_as_ini(file_object=file)
                file.close()
                self.parameters.write_app_param(file.name)
        else:
            summary.debug("saving file to %s", path)
            try:
                with open(path, "w") as file:
                    self.current_ship_data.write_as_ini(file_object=file)
            except OSError as error:
                summary.error("Could not save file:\n%s", error)
                details.error("Could not save file:\n%s", error)
                return

            summary.info("save successful!")
            self.parameters.write_app_param(file.name)

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
        funnels_frame.grid(row=_FUNNELS_ROW, column=0, sticky=tk.S)
        struct_frame = tk.Frame(self)
        index_structure = 0
        st_editors = []
        for index_structure, structure in enumerate(ship_data.structures):
            new_st_display = structeditor.StructEditor(struct_frame, structure, command_stack)
            new_st_display.grid(row=0, column=index_structure)
            st_editors.append(new_st_display)
        struct_frame.grid(row=_STRUCT_EDITORS_ROW, column=0, columnspan=2)

        self._top_view = topview.TopView(self, ship_data, st_editors,
                                         funnels_editors, command_stack, parameters)
        self._top_view.grid(row=_TOPVIEW_ROW, column=_TOPVIEW_COL, sticky=tk.W)

        st_editors[0]._on_get_focus()

        self._side_view = sideview.SideView(self, ship_data, parameters)
        self._side_view.grid(row=_SIDEVIEW_ROW, column=_SIDEVIEW_COL, sticky=tk.W)

        self._grid_var = tk.IntVar()
        (ttk.Checkbutton(self, text="Grid", variable=self._grid_var, command=self._switch_grid).
         grid(row=_SIDEVIEW_ROW, column=0))

    def _switch_grid(self):
        self._side_view.switch_grid(bool(self._grid_var.get()))
        self._top_view.switch_grid(bool(self._grid_var.get()))


class LogToWidget(logging.Handler):
    """Redirect the logger's output to a ttk text Widget

    With colors according to debug/info/warning/critical
    """
    def __init__(self, text_widget):
        super().__init__()
        self._text_widget = text_widget
        self._text_widget.tag_config("Debug")
        self._text_widget.tag_config("Info", background="spring green")
        self._text_widget.tag_config("Warning", background="orange")
        self._text_widget.tag_config("Error", background="red")

    def emit(self, record):
        if record.levelno == logging.DEBUG:
            self._text_widget.insert(tk.END, record.getMessage() + "\n", "Debug")
        if record.levelno == logging.INFO:
            self._text_widget.insert(tk.END, record.getMessage() + "\n", "Info")
        if record.levelno == logging.WARNING:
            self._text_widget.insert(tk.END, record.getMessage() + "\n", "Warning")
        if record.levelno == logging.ERROR:
            self._text_widget.insert(tk.END, record.getMessage() + "\n", "Error")
        self._text_widget.see(tk.END)

if __name__ == "__main__":
    MainWindow().mainloop()

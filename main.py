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

log_filename = pathlib.Path(appdirs.user_data_dir("Draftnought")).joinpath("log.txt")
if not log_filename.exists():
    log_filename.parent.mkdir(parents=True, exist_ok=True)
details = logging.getLogger("Details")
details.setLevel(logging.WARNING)
file_handler = logging.handlers.RotatingFileHandler(
    log_filename, maxBytes=500*1000, backupCount=5)
details.addHandler(file_handler)

_MAIN_ROW = 0

_LOG_ROW = _MAIN_ROW +1

class MainWindow(tk.Tk):
    """Base class for the whole UI"""
    def __init__(self):
        super().__init__()
        self.winfo_toplevel().title("Draftnought")
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

        self.parameters = parameters_loader.Parameters("")

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

        viewmenu = tk.Menu(menubar, tearoff=0)
        self.grid_var = tk.IntVar()
        self.grid_var.set(int(self.parameters.grid))
        self.grid_var.trace_add("write", self._set_grid)
        viewmenu.add_checkbutton(label="Grid", variable=self.grid_var)

        menubar.add_cascade(label='File', menu=filemenu)
        menubar.add_cascade(label='Edit', menu=editmenu)
        menubar.add_cascade(label='View', menu=viewmenu)

        self.bind("<Control-s>", self.do_save)
        self.bind("<Control-o>", self.do_load)
        self.bind("<Control-S>", self.do_save_as_keyboard)
        self.bind("<Control-z>", self.do_undo)
        self.bind("<Control-y>", self.do_redo)

        self.center_frame = ttk.Button(self, text="Load ship file", command=self.do_load)
        self.center_frame.grid(row=_MAIN_ROW)

        try:
            with open(self.parameters.last_file_path) as file:
                self.load(file.name)
        except OSError:
            return

    def _set_grid(self, _var_name, _list_index, _operation):
        self.parameters.grid = bool(self.grid_var.get())
        if isinstance(self.center_frame, ShipEditor):
            self.center_frame.set_grid(bool(self.grid_var.get()))

    def do_undo(self, *_args):
        """undo last command, or deeper in the undoing stack"""
        self.command_stack.undo()

    def do_redo(self, *_args):
        """redo last command, or deeper in the redoing stack"""
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
        """Save the current file to the same path"""
        self.do_save_as(self.parameters.current_file_path)

    def load(self, path):
        """load a ship file and display it

        Args:
            path (str): ship file's path.
                If none is given, a dialog box is opened to choose it.
        """
        summary.debug("loading %s", path)
        #save old parameters in case something goes wrong
        old_parameters = self.parameters
        self.parameters = parameters_loader.Parameters(path)
        try:
            with open(path) as file:
                self.current_ship_data = sd.ShipData(file, self.parameters)
        except sd.ShipFileInvalidException as error:
            details.error("The file is not correctly formatted to be a ship file:\n%s\n%s",
                          path, error)
            summary.error("The file is not correctly formatted to be a ship file:"
                          "\n%s\nPlease load it in-game and save it again", path)
            self.parameters = old_parameters
            return

        summary.info("loading successful!")
        self.center_frame.destroy()
        #reset the command stack
        new_command_stack = CommandStack()
        self.center_frame = ShipEditor(self,
                                       self.current_ship_data,
                                       new_command_stack,
                                       self.parameters)
        self.center_frame.grid(row=_MAIN_ROW, column=0, sticky=tk.N+tk.E+tk.S+tk.W)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(_MAIN_ROW, weight=1)
        self.resizable(True, True)

        #if load was OK, forget the old command stack
        self.command_stack = new_command_stack
        self.grid_var.set(int(self.parameters.grid))
        self.winfo_toplevel().title(pathlib.Path(path).name)

    def do_save_as(self, path=None):
        """Save the current file, path choosable

        Also saves the path as "last file" to open on the next start

        Args:
            path (str): path to the file
                If none given, a file picker dialog allows to choose a new or existing file
        """
        if path is None:
            current_file_path = self.parameters.current_file_path
            if not current_file_path:
                return
            extension = pathlib.Path(current_file_path).suffix
            file = filedialog.asksaveasfile(defaultextension=extension,
                                            initialdir=pathlib.Path(current_file_path).parent,
                                            initialfile=pathlib.Path(current_file_path).name,
                                            filetypes=(("ship files", extension),
                                                       ("all files", "*.*")))
            if file is not None:
                summary.debug("saving file to %s", file.name)
                self.current_ship_data.write_as_ini(file_object=file)
                file.close()
                self.parameters.write_app_param(file.name)
        elif path:
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
        command_stack (CommandStack): the  redo/undo  command stack common to the whole program
        parameters (parameters_loader.Parameters): all the parameters for the app and the ship data
    """
    def __init__(self, parent, ship_data, command_stack, parameters):
        super().__init__(parent)
        funnels_editors = []
        for index, funnel in enumerate(ship_data.funnels.values()):
            funnel_editor = funnelseditor.FunnelEditor(self, funnel, index, command_stack)
            funnel_editor.grid(row=(index//2)+1, column=index%2, sticky=tk.W+tk.E)
            funnels_editors.append(funnel_editor)
        st_editors = []
        for index, structure in enumerate(ship_data.structures):
            new_st_display = structeditor.StructEditor(self, structure, command_stack)
            new_st_display.grid(row=(index//2)+3, column=index%2)
            st_editors.append(new_st_display)

        views = tk.Frame(self)
        self._top_view = topview.TopView(views, ship_data, st_editors,
                                         funnels_editors, command_stack, parameters)
        self._top_view.grid(row=1, column=0, sticky=tk.N+tk.E+tk.S+tk.W)

        self._side_view = sideview.SideView(views, ship_data, parameters, self._top_view)
        self._side_view.grid(row=0, column=0, sticky=tk.N+tk.E+tk.S+tk.W)
        views.columnconfigure(0, weight=1)
        views.rowconfigure(0, weight=1)
        views.rowconfigure(1, weight=1)

        views.grid(row=0, column=2, rowspan=5, sticky=tk.N+tk.W+tk.S+tk.E)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)

        st_editors[0].focus_set()

    def set_grid(self, grid_state):
        """set the grid for both top and side view according to grid_state"""
        self._side_view.refresh_grid(grid_state)
        self._top_view.switch_grid(grid_state)


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

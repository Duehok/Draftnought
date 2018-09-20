"""docstring"""
from window.framework import Observable, Command

class Funnel(Observable):
    """Container for the data needed to draw a funnel

    Contrary to the other ship parts, not generated from the file's data but from passed parameters
    Args:
        oval=False: round or oval funnel
        position=0: funnel position on the vertical axis. 0 is the center of the ship.
    Attrs:
        oval: if the funnel should be displayed as an oval, or not
        position: Position of the funnel along the length of the ship, in funnel coordinates
    """
    def __init__(self, oval=False, position=0):
        super().__init__()
        self._oval = oval
        self._position = position

    @property
    def oval(self):
        """if the funnel should be displayed as an oval, or not"""
        return self._oval

    @oval.setter
    def oval(self, value):
        if value != self._oval:
            self._oval = value
            self._notify("set_oval", {"oval":value})

    @property
    def position(self):
        """Position of the funnel along the length of the ship, in funnel coordinates"""
        return self._position

    @position.setter
    def position(self, value):
        if value != self._position:
            self._position = value
            self._notify("set_position", {"position":value})

class MoveFunnel(Command):
    """Moves a funnel to a given position

    Args:
        funnel: funnel tha moves
        position: new position in funnel coordinates
    """
    def __init__(self, funnel, position):
        super().__init__()
        self._funnel = funnel
        self._position = position
        self._old_position = funnel.position

    def execute(self):
        """Moves the funnel"""
        if self._position != self._funnel.position:
            self._funnel.position = self._position

    def undo(self):
        """Back to previous position
        """
        if self._old_position != self._funnel.position:
            self._funnel.position = self._old_position

class OvalFunnel(Command):
    """Change the funnel from oval to circular and the opposite

    Args:
        funnel (Funnel): the funnel to be changed
        oval (bool): true if oval
    """
    def __init__(self, funnel, oval):
        super().__init__()
        self._funnel = funnel
        self._oval = oval
        self._old_oval = funnel.oval

    def execute(self):
        """Change the funnel's status"""
        if self._oval != self._funnel.oval:
            self._funnel.oval = self._oval

    def undo(self):
        """Back to original state"""
        if self._old_oval != self._funnel.oval:
            self._funnel.oval = self._old_oval

def funnels_as_ini_section(funnels):
    """from a list of funnels, gives back a dict that can be exported to a
    file that RTW can understand
    """
    section_content = {}
    for name, funnel in funnels.items():
        section_content[name+ "Pos"] = round(funnel.position)
    for name, funnel in funnels.items():
        if funnel.oval:
            section_content[name+"Oval"] = 1
        else:
            section_content[name+"Oval"] = 0
    return section_content

def parse_funnels(funnels_section):
    """helper function to read the funnels data

    Args:
        funnels_section (dict): about the funnels straight from the parsed file
    returns:
        dict {"funnelname": {"Pos":number, "Oval":number}}
    """
    funnels = {}
    for k in funnels_section.keys():
        pos_string_index = k.find("Pos")
        if pos_string_index != -1:
            #if the current option is a funnel's position
            #grab its name (before "Pos")
            #add it to the funnels collection if it is new, update it if it is not
            #so hardening against duplicate funnels
            pos = funnels_section.getint(k)
            funnel_name = k[0: pos_string_index]
            if funnel_name in funnels:
                is_oval = funnels[funnel_name].oval
                funnels[funnel_name] = Funnel(is_oval, pos)
            else:
                funnels[funnel_name] = Funnel(position=pos)

        oval_string_index = k.find("Oval")
        if oval_string_index != -1:
            #same logic for the "Oval" info
            is_oval = funnels_section.getboolean(k)
            funnel_name = k[0: oval_string_index]
            if funnel_name in funnels:
                pos = funnels[funnel_name].position
                funnels[funnel_name] = Funnel(is_oval, pos)
            else:
                funnels[funnel_name] = Funnel(oval=is_oval)
    return funnels

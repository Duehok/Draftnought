"""Reads and write ship data from/to RTW's ship files
"""
import configparser
import pathlib
from math import pi
from PIL import Image
from model.structure import Structure
from model.turrets_torps import Turret, Torpedo
from model.funnel import funnels_as_ini_section, parse_funnels

#superstructures and funnels have different coordinates system
#I decide to use the funnel
#might be a bad idea
STRUCTURE_TO_FUNNEL = 1.0/45.0

#To convert the angle's value in superstructure's points to radiants
ANGLE_TO_RADS = pi/972000000.0

#to set up the display if starting without loading a file
DEFAULT_HALF_LENGTH = 200
DEFAULT_SHIP_TYPE = "BC"

MANDATORY_SECTIONS_OPTIONS = {"Data":["PictureName", "ShipType", "Displacement"],
                              "Guns":["TurretStyle"], "Funnels":[]}

class ShipData:
    """Main container for all data

    Also all the logic to read and write from/to ship data files.
    Args:
        file (str): path to the file to be read.
        parameters (parameters_loader.parameters): dict with the configurable parameters.
            Needs "ships_hlengths", see parameters_loaders or the default files for more info
    Attrs:
        structures (list): list of all model.Structure
        turrets (list): list of all Turret
        funnels (dict): dict of all funnels.
            {"funnelname": {"Pos":number, "Oval":number}}
        half_length (int): lengths from center to bow, in funnel coordinates
        ship_type (string): ship type, like "BC", "DD"...
        side_pict (PIL.Image or None): A PIL Image if a side picture path was set in the file,
            and this path can be found and read as a picture. Else None
    """
    def __init__(self, file, parameters):
        self.structures = []
        self.turrets_torps = []
        self.funnels = {}
        self.path = pathlib.Path(file.name)
        #parser as self to help write back the file
        self._parser = configparser.ConfigParser()
        #we preserve the case of the option names, instead of converting all to lower case
        self._parser.optionxform = str
        try:
            self._parser.read_file(file)
        except configparser.Error as error:
            raise ShipFileInvalidException(self.path.resolve(), error) from error

        for section in MANDATORY_SECTIONS_OPTIONS:
            if section not in self._parser.keys():
                raise ShipFileInvalidException(self.path.resolve(),
                                               message=f"Missing section: {section}")
            else:
                for option in MANDATORY_SECTIONS_OPTIONS[section]:
                    if option not in self._parser[section]:
                        message = f"Missing option: {option} in section {section}"
                        raise ShipFileInvalidException(self.path.resolve(), message=message)

        caliber = self._parser['Guns'].getint('Main')
        #No length data in the ship file, length is determined from tonnage and ship type
        #reverse-engineered from in game ships
        self.ship_type = self._parser['Data']['ShipType']
        displacement = self._parser['Data'].getint('Displacement')

        #grab the first length whose tonnage is above our tonnage for the correct ship type
        #assumes the length to tonnage are ordered
        #the lengths are in "funnel coordinates"
        self.half_length = [v for k, v in
                            parameters.ships_hlengths[self.ship_type].items()
                            if k > displacement][0]

        turret_data = {}
        torps = []
        for section, section_content in self._parser.items():
            if "Superstructure" in section:
                new_struct = Structure(section, section_content)
                self.structures.append(new_struct)
            elif "Turret" in section:
                turret_data[self._parser[section]["Pos"]] = self._parser[section].getint("Guns")
            elif "TorpedoMount" in section:
                if int(section_content["Tubes"]) >= 1:
                    new_torp = Torpedo(section_content, self.half_length, parameters)
                    torps.append(new_torp)


        self.turrets_torps = [Turret(caliber, k, v, self.half_length, turret_data, parameters)
                              for k, v in turret_data.items()] + torps


        self.funnels = parse_funnels(self._parser["Funnels"])

        if self._parser["Data"]["PictureName"] is not None:
            pict_path = self.path.parent.joinpath(self._parser["Data"]["PictureName"])
            try:
                self.side_pict = Image.open(pict_path)
            except OSError:
                self.side_pict = None
        else:
            self.side_pict = None

    def write_as_ini(self, file_object=None, file_path=None):
        """Write the ship data in a RTW-readable format to the given file path or file object
        Choose one or the other method!

        OSErrors should be handled by the caller

        Args:
            file_path (str): file path to save
            file_object (IOstram): writeable file-like object to save
        """
        for struct in self.structures:
            self._parser[struct.name] = struct.as_ini_section()

        self._parser["Funnels"] = funnels_as_ini_section(self.funnels)
        if  file_path is not None:
            with open(file_path, "w") as file:
                self._parser.write(file, space_around_delimiters=False)
        elif file_object is not None:
            self._parser.write(file_object, space_around_delimiters=False)
        else:
            with open(self.path.resolve(), "w") as file:
                self._parser.write(file, space_around_delimiters=False)

class ShipFileInvalidException(Exception):
    """Errors that can be raised while reading a ship data file"""
    def __init__(self, file_path, root_error=None, message=None):
        if isinstance(root_error, configparser.Error):
            super().__init__(f"Could not parse as INI the file {file_path}\n{root_error.message}")
        elif root_error is not None:
            super().__init__(f"Error trying to read the file {file_path}\n{root_error.message}")
        elif message is not None:
            super().__init__(f"Schema error in file {file_path}\n{message}")
        else:
            super().__init__(f"Unspecified error trying to read file {file_path}")

"""Centralize all the loading of data  from external files that are not in the ship file

Contains default path for those files
files in json format
"""
import json
import logging
from collections import OrderedDict
import pathlib
log = logging.getLogger()

#TODO: simplify list of files
DEFAULT_FILES = {
    "app_config" : "app_config.json",
    "hulls_shapes" : "hull_shapes.json",
    "ships_hlengths" : "lengths.json",
    "turrets_positions": "turrets_positions.json",
    "turrets_scale":"turrets_scale.json",
    "turrets_outlines":"turrets_outlines.json",
    }

SHIP_TYPES = ["BB", "BC", "B", "CA", "CL", "DD", "MS", "AMC"]
TURRETS = ["1", "2", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
           "Q", "R", "S", "T", "V", "W", "X", "Y", "3", "4"]
DEFAULT_TURRET_POSITION = {"positions": [(1000, 1000), (1000, 1000), (1000, 1000), (1000, 1000)],
                           "to_bow": True}

#gun caliber must be defined at least to this value
MIN_MAX_GUN_CALIBER = 18
MAX_GUNS_PER_TURRET = 4
DEFAULT_TURRETS_SCALE = [0.22, 0.26, 0.306, 0.347,
                         0.387, 0.422, 0.458, 0.536,
                         0.615, 0.657, 0.700, 0.746,
                         0.793, 0.867, 0.942, 0.971,
                         1.000, 1.091, 1.091
                        ]

DEFAULT_APP_CONFIG = {
    "last_file_path" : "",
    "max_points_in_structure":21
    }

DEFAULT_TURRET_OUTLINE = [[-7.4, 12.9], [-10, -0.1], [-6.5, -7.4], [-1.2, -9.6],
                          [-0.7, -30], [0.7, -30], [1.2, -9.6], [6.5, -7.4], [10, -0], [7.4, 12.9]]

def read_ships_hlengths():
    """build the half lengths data

    There should be one def for each ship type
    Default values will be used for missing ship types

    Returns:
        a dict of the format:
        {ship_type (str): { max_tonnage (int) : ship_half_length (int)}}
    """
    path = DEFAULT_FILES["ships_hlengths"]
    try:
        with open(path) as file:
            hlengths = json.load(file, object_hook=convert_str_key_to_int)
    except (OSError, json.JSONDecodeError) as error:
        log.error("Could not load or read file: %s\n%s", pathlib.Path(path).resolve(), error)
        hlengths = {ship_type:{200000:200} for ship_type in SHIP_TYPES}
        return hlengths

    for ship_type in SHIP_TYPES:
        if not ship_type in hlengths.keys():
            hlengths[ship_type] = {200000:200}
            log.error("Missing definition for ship type %s from file %s",
                      ship_type, pathlib.Path(path).resolve())
    return hlengths

def read_hulls_shapes():
    """build the hulls outlines data

    The outlines are made of several lines.
    Those lines are smoothed so if you want sharp angle,
    use several lines that start or end at the coordinates
    The coordinates are in the relative system

    Returns:
        a dict of the format:
        {ship_type (str) : [ [float,float] ] }
    """
    path = DEFAULT_FILES["hulls_shapes"]
    try:
        with open(path) as file:
            shapes = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        log.error("Could not load or read file: %s\n%s", pathlib.Path(path).resolve(), error)
        shapes = [[] for ship_type in SHIP_TYPES]
        return shapes

    for ship_type in SHIP_TYPES:
        if not ship_type in shapes.keys():
            shapes[ship_type] = []
            log.error("Missing hull outline shape for ship type %s from file %s",
                      ship_type, pathlib.Path(path).resolve())
    return shapes

def read_turrets_positions():
    """build the turrets position data

    TODO: explain
    """
    path = DEFAULT_FILES["turrets_positions"]
    try:
        with open(path) as file:
            turrets_positions = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        log.error("Could not load or read file: %s\n%s", pathlib.Path(path).resolve(), error)
        turrets_positions = {turret:DEFAULT_TURRET_POSITION for turret in TURRETS}
        return turrets_positions

    for turret in TURRETS:
        if not turret in turrets_positions:
            log.error("Missing turret position %s from file %s",
                      turret, pathlib.Path(path).resolve())
            turrets_positions[turret] = DEFAULT_TURRET_POSITION
    return turrets_positions

def read_turrets_scale():
    """build the turrets scale data

    This is used to scale the turret#s outlines according to the gun caliber

    Returns:
        a list. Index is caliber (so start at caliber = 0), value is scale (1 for 406mm by default)
    """
    path = DEFAULT_FILES["turrets_scale"]
    try:
        with open(path) as file:
            turrets_scale = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        log.error("Could not load or read file: %s\n%s", pathlib.Path(path).resolve(), error)
        return DEFAULT_TURRETS_SCALE

    if len(turrets_scale) <= MIN_MAX_GUN_CALIBER:
        log.error("Turret scale defined up to caliber %s instead of %s in file %s",
                  len(turrets_scale)-1,
                  MIN_MAX_GUN_CALIBER,
                  pathlib.Path(path).resolve())
        turrets_scale = (turrets_scale +
                         [DEFAULT_TURRETS_SCALE[i]
                          for i in range(len(turrets_scale, len(DEFAULT_TURRETS_SCALE)))])
        return turrets_scale
    return turrets_scale

def read_turrets_outlines():
    """Build the turrets outilnes

    The coordinates are in the funnel system
    They will be scaled according to caliber
    By default, scale = 1 for 406mm guns
    Returns
    A list. index is amount of guns-1 (starts at 0)
    then a list of coordinates
    coordinates are x, y
    [ [ (x, y)] ]
    """
    path = DEFAULT_FILES["turrets_outlines"]
    try:
        with open(path) as file:
            turrets_outlines = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        log.error("Could not load or read file: %s\n%s", pathlib.Path(path).resolve(), error)
        return [DEFAULT_TURRET_OUTLINE for i in range(0, MAX_GUNS_PER_TURRET)]

    if len(turrets_outlines)+1 < MAX_GUNS_PER_TURRET:
        log.error("Not all gun per turret defined in file: %s", pathlib.Path(path).resolve())
        turrets_outlines = (turrets_outlines
                            + [DEFAULT_TURRET_OUTLINE
                               for i in range(len(turrets_outlines), MAX_GUNS_PER_TURRET)])
    return turrets_outlines

def read_app_param():
    """build the data for the program config

    If the config file is not found, default values are used and an info-level message is logged

    Returns (dict):
        a dict with all the data
    """
    path = DEFAULT_FILES["app_config"]
    try:
        with open(path) as file:
            param = json.load(file)
    except OSError as error:
        log.info("Could not load file: %s\n%s", pathlib.Path(path).resolve(), error)
        return DEFAULT_APP_CONFIG
    except json.JSONDecodeError as error:
        log.error("Could not decode file: %s\n%s", pathlib.Path(path).resolve(), error)
        return DEFAULT_APP_CONFIG

    for config, value in DEFAULT_APP_CONFIG.items():
        if config not in param.keys():
            param[config] = value
            log.error("Missing definition %s from file %s", config, pathlib.Path(path).resolve())
    return param

class Parameters:
    """Main class that contains all the parameters

    Attributes:
        hulls_shapes (dict): for each ship type, a list of lines that define the hull outer line.
            each line is a list of tuples (x, y) in relative coordinates
        ships_hlengths (dict): for each ship type, a dict {int:int} used to get the length
            from origin to bow
            The key is the biggest tonnage for which the length is still valid
            the value is the distance from origin to bow in funnel coordinates.
        app_config (dict): program configuration
    """
    def __init__(self):

        self.hulls_shapes = read_hulls_shapes()
        self.ships_hlengths = read_ships_hlengths()
        self.turrets_positions = read_turrets_positions()
        self.app_config = read_app_param()
        self.turrets_scale = read_turrets_scale()
        self.turrets_outlines = read_turrets_outlines()

    def write_app_param(self, new_parameters=None, file_path=None):
        """write the application config to a file

        Args:
            new_parameters (dict): new set of parameters to write.
                If not given, the current parameters are written.
            file_path (str): path to the file that should be created or overwritten.
                If not given, the default file path is used.
        """
        if file_path is None:
            file_path = DEFAULT_FILES["app_config"]
        if new_parameters is None:
            new_parameters = self.app_config
        try:
            with open(file_path, "w") as file:
                json.dump(new_parameters, file)
        except OSError as err:
            log.error("Could not save app config file to: %s\n%s", file_path, err)

def convert_str_key_to_int(data):
    """in a dictionary, convert to int the keys (assumed to be an int) that can be parsed to int
    AND order the dict in increasing key value

    the keys that cant be parsed are kept intact, but sorting still happens

    Args:
        data: anything.
        If it is not a dict, nothing is done and the returned value is identical the parameter

    Returns.
        An ordered dict with int keys if the param was a dict and the keys could be parsed to int,
        the same as the parameter if not
    """
    if isinstance(data, dict):
        new_dict = {}
        could_be_parsed = True
        for key, value in data.items():
            try:
                newk = int(key)
            except ValueError:
                could_be_parsed = False
                break
            new_dict[newk] = value
        if could_be_parsed:
            return OrderedDict(sorted(new_dict.items()))
    return data

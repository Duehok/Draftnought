"""Centralize all the loading of data  from external files that are not in the ship file

Contains default path for those files
files in json format
#TODO:reduce copy pasta
"""
import json
import jsonschema
import logging
from collections import OrderedDict
import pathlib
import appdirs
import schemas


APP_CONFIG = pathlib.Path(appdirs.user_data_dir("Drafnought")).joinpath("app_config.json")
#TODO: simplify list of files
DEFAULT_FILES = {
    "hulls_shapes" : "hull_shapes.json",
    "ships_hlengths" : "lengths.json",
    "turrets_positions": "turrets_positions.json",
    "turrets_scale":"turrets_scale.json",
    "turrets_outlines":"turrets_outlines.json",
    }



DEFAULT_APP_CONFIG = {
    "last_file_path" : "",
    "max_points_in_structure":21
    }

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
            raw_hlengths = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        logging.error("Could not load or read file: %s\n%s", pathlib.Path(path).resolve(), error)
        return schemas.DEFAULT_HALF_LENGTHS

    try:
        jsonschema.validate(raw_hlengths, schemas.HALF_LENGTHS_SCHEMA)
    except jsonschema.ValidationError as error:
        logging.error("Valid JSON but invalid Schema in: %s, default values used instead", path)
        logging.warning("Valid JSON but invalid Schema in: %s\n, description:\n%s", path, error)
        return schemas.DEFAULT_HALF_LENGTHS

    #convert the keys of the lengths to allow comparison:

    hlengths = {}
    for ship_type, lengths_dicts in raw_hlengths.items():
        hlengths[ship_type] = convert_str_key_to_int(lengths_dicts)

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
        logging.error("Could not load or read file: %s\n%s", pathlib.Path(path).resolve(), error)
        return schemas.DEFAULT_HULLS_SHAPES
    try:
        jsonschema.validate(shapes, schemas.HULLS_SHAPES_SCHEMA)
    except jsonschema.ValidationError as error:
        logging.error("Valid JSON but invalid Schema in: %s, default values used instead", path)
        logging.warning("Valid JSON but invalid Schema in: %s\n, description:\n%s", path, error)
        return schemas.DEFAULT_HULLS_SHAPES

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
        logging.error("Could not load or read file: %s\n%s", path, error)
        return schemas.DEFAULT_TURRETS_POSITION

    try:
        jsonschema.validate(turrets_positions, schemas.TURRETS_POSITION_SCHEMA)
    except jsonschema.ValidationError as error:
        
        logging.error("Valid JSON but invalid Schema in: %s, default values used instead", path)
        logging.warning("Valid JSON but invalid Schema in: %s\n, description:\n%s", path, error)
        return schemas.DEFAULT_TURRETS_POSITION

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
        logging.error("Could not load or read file: %s\n%s", pathlib.Path(path).resolve(), error)
        return schemas.DEFAULT_TURRETS_SCALE

    try:
        jsonschema.validate(turrets_scale, schemas.TURRETS_SCALE_SCHEMA)
    except jsonschema.ValidationError as error:  
        logging.error("Valid JSON but invalid Schema in: %s, default values used instead", path)
        logging.warning("Valid JSON but invalid Schema in: %s\n, description:\n%s", path, error)
        return schemas.DEFAULT_TURRETS_SCALE

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
        logging.error("Could not load or read file: %s\n%s", pathlib.Path(path).resolve(), error)
        return schemas.DEFAULT_TURRETS_OUTLINE

    try:
        jsonschema.validate(turrets_outlines, schemas.TURRETS_OUTLINE_SCHEMA)
    except jsonschema.ValidationError as error:
        
        logging.error("Valid JSON but invalid Schema in: %s, default values used instead", path)
        logging.warning("Valid JSON but invalid Schema in: %s\n, description:\n%s", path, error)
        return schemas.DEFAULT_TURRETS_OUTLINE

    return turrets_outlines

def read_app_param():
    """build the data for the program config

    If the config file is not found, default values are used and an info-level message is logged

    Returns (dict):
        a dict with all the data
    """
    try:
        with open(APP_CONFIG) as file:
            param = json.load(file)
    except OSError as error:
        logging.info("Could not load file: %s\n%s", APP_CONFIG.resolve(), error)
        return DEFAULT_APP_CONFIG
    except json.JSONDecodeError as error:
        logging.error("Could not decode file: %s\n%s", APP_CONFIG.resolve(), error)
        return DEFAULT_APP_CONFIG

    for config, value in DEFAULT_APP_CONFIG.items():
        if config not in param.keys():
            param[config] = value
            logging.error("Missing definition %s from file %s", config, APP_CONFIG.resolve())
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
            file_path = APP_CONFIG.resolve()
        if new_parameters is None:
            new_parameters = self.app_config
        try:
            pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as file:
                json.dump(new_parameters, file)
                logging.info("Saved app parameters to %s", file_path)
        except OSError as err:
            logging.error("Could not save app config file to: %s\n%s", file_path, err)

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
            return new_dict
    return data

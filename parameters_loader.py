"""Centralize all the loading of data  from external files that are not in the ship file

Contains default path for those files
files in json format
"""
import json
import logging
import pathlib
import jsonschema
import schemas

summary = logging.getLogger("Summary")
details = logging.getLogger("Details")

MAX_RECENT_FILES = 21

def read_json(path, json_schema, default_data):
    """Read a json file and validate it against a schema

    If an exception occurs, the default data is returned
    Args:
        path (string): path to json file
        json_schema (dict) a dict with the json schema info
        default_data (dict): what should be returned in case of failure
    returns:
        a dict with the json data if everything works fine, default_data if not
    """
    try:
        details.debug("loading parameter file %s", pathlib.Path(path).name)
        with open(path) as file:
            json_data = json.load(file)
    except OSError as error:
        summary.warning("Could not load file: %s\nLoading default values instead",
                        pathlib.Path(path).resolve())
        details.warning("Could not load file: %s\n%s",
                        pathlib.Path(path).resolve(), error)
        return default_data
    except json.JSONDecodeError as error:
        summary.warning("This file is not valid json: %s\nLoading default values instead",
                        pathlib.Path(path).resolve())
        details.warning("This file is not valid json: %s\n%s\n\nLoading default values instead",
                        pathlib.Path(path).resolve(), error)
        return default_data

    try:
        jsonschema.validate(json_data, json_schema)
    except jsonschema.ValidationError as error:
        summary.warning("Valid JSON but invalid Schema in: %s\nLoading default values instead",
                        path)
        details.warning("Valid JSON but invalid Schema in: %s\n%s", path, error)
        return default_data

    return json_data

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
    def __init__(self, ship_file_path):
        self._recent_files = read_json(schemas.RECENT_FILES_PATH,
                                     schemas.RECENT_FILES_SCHEMA,
                                     schemas.DEFAULT_RECENT_FILES)
        self.hulls_shapes = read_json(schemas.HULLS_SHAPES_PATH,
                                      schemas.HULLS_SHAPES_SCHEMA,
                                      schemas.DEFAULT_HULLS_SHAPES)
        self.turrets_positions = read_json(schemas.TURRETS_POSITION_PATH,
                                           schemas.TURRETS_POSITION_SCHEMA,
                                           schemas.DEFAULT_TURRETS_POSITION)
        self.turrets_scale = read_json(schemas.TURRETS_SCALE_PATH,
                                       schemas.TURRETS_SCALE_SCHEMA,
                                       schemas.DEFAULT_TURRETS_SCALE)
        self.turrets_outlines = read_json(schemas.TURRETS_OUTLINES_PATH,
                                          schemas.TURRETS_OUTLINE_SCHEMA,
                                          schemas.DEFAULT_TURRETS_OUTLINE)
        raw_hlengths = read_json(schemas.HALF_LENGTHS_PATH,
                                 schemas.HALF_LENGTHS_SCHEMA,
                                 schemas.DEFAULT_HALF_LENGTHS)

        self.ships_hlengths = {}
        for ship_type, lengths_dicts in raw_hlengths.items():
            self.ships_hlengths[ship_type] = convert_str_key_to_int(lengths_dicts)

        #if the requested file is in the list of recent files, 
        #use its zoom and offset for the side pict
        #if not, use the moset recent file if it exists
        #if not, default values
        #Starting python 3.7, dicts are ordered by insert order
        self._current_file_path = ship_file_path
        self.zoom = self.file_param("zoom")
        self.offset = self.file_param("offset")
        self.grid = self.file_param("grid")

    def file_param(self, param):
        if self._current_file_path in self._recent_files.keys():
            return self._recent_files[self._current_file_path][param]
        if self._recent_files:
            last_file = list(self._recent_files.keys())[-1]
            return self._recent_files[last_file][param]
        return schemas.DEFAULT_PARAM[param]



    def write_app_param(self, path=None):
        """write the application config to a file

        Args:
            new_parameters (dict): new set of parameters to write.
                If not given, the current parameters are written.
            file_path (str): path to the file that should be created or overwritten.
                If not given, the default file path is used.
        """
        if path is not None:
            self._current_file_path = path
        if self._current_file_path in self._recent_files.keys():
            del self._recent_files[self._current_file_path]
        if pathlib.Path(self._current_file_path).exists():
            self._recent_files[self._current_file_path] = {}
            self._recent_files[self._current_file_path]["zoom"] = self.zoom
            self._recent_files[self._current_file_path]["offset"] = self.offset
            self._recent_files[self._current_file_path]["grid"] = self.grid
        if len(self._recent_files) > MAX_RECENT_FILES:
            self._recent_files = {f:self._recent_files[f] 
                                  for f in list(
                                                self._recent_files.keys())[len(self._recent_files)
                                                                           -MAX_RECENT_FILES:]}

        try:
            details.info("Saving app parameters to %s", schemas.RECENT_FILES_PATH)
            pathlib.Path(schemas.RECENT_FILES_PATH).parent.mkdir(parents=True, exist_ok=True)
            with open(schemas.RECENT_FILES_PATH, "w") as file:
                json.dump(self._recent_files, file)
                details.info("Saved app parameters to %s", schemas.RECENT_FILES_PATH)
        except OSError as error:
            summary.warning("Could not save app config file to: %s", schemas.RECENT_FILES_PATH)
            details.warning("Could not save app config file to: %s\n%s", schemas.RECENT_FILES_PATH, error)

    @property
    def last_file_path(self):
        if self._recent_files:
            return list(self._recent_files.keys())[-1]
        return ""

    @property
    def current_file_path(self):
        return self._current_file_path

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

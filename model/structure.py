"""Class for the superstructures data
And the commands that change it
"""
from math import atan2, sin, cos, pi, sqrt
from window.framework import Observable, Command
import model.shipdata as sd

STRUCTURE_POINTS_MAX = 21

class Structure(Observable):
    """Container for the data needed to draw a superstructure and their operations

        name (str): the name of the superstructure section in the ship file
        raw_data (dict): section about the superstructure straight from the parsed file
    """
    def __init__(self, name, raw_data):
        super().__init__()
        self.name = name
        self._points = []
        rtw_points = []
        self._fill = True
        for k in raw_data.keys():
            if "IsLine" in k:
                self._fill = not raw_data.getboolean(k)
            else:
                value = raw_data.getint(k)
                dist_string_index = k.find("Distance")
                angle_string_index = k.find("Angle")
                point_index = int(k[len("Point"):max(dist_string_index, angle_string_index)])

                if point_index <= len(rtw_points)-1:
                    #if the point has already been encountered, update it
                    if dist_string_index != -1 and value != 0:
                        rtw_points[point_index] = (rtw_points[point_index][0], value)
                    elif angle_string_index != -1:
                        rtw_points[point_index] = (value, rtw_points[point_index][1])
                else:
                    #if this is a new point, fill all the points between the last encountered point
                    #and the new point with (0,0)
                    #that's in case we go from point1 to point3 and then we have point2
                    while len(rtw_points) < point_index-1:
                        rtw_points.append((0, 0))
                    if dist_string_index != -1:
                        rtw_points.append((0, value))
                    elif angle_string_index != -1:
                        rtw_points.append((value, 0))

        #get rid of "empty" points
        #that's what the game seems to do
        rtw_points[:] = [point for point in rtw_points if (point[0] != 0 or point[1] != 0)]

        #all duplicates are deleted, and the circular coordinates are converted to cartesian
        temp_point = (0, 0)
        for point in rtw_points:
            if point != temp_point:
                #origin is more or less the middle of the ship
                #x to the right
                #y to the bow
                #the magic value for the angle is from estimations from the game
                x = (-point[1]*sin(point[0]*sd.ANGLE_TO_RADS)
                     *sd.STRUCTURE_TO_FUNNEL)
                y = (-point[1]*cos(point[0]*sd.ANGLE_TO_RADS)
                     *sd.STRUCTURE_TO_FUNNEL)
                self._points.append((x, y))
                temp_point = (point[0], point[1])

    @property
    def fill(self):
        """Fill state: the opposite of the ship file's IsLine option
        Seems to me to make more sense than just "line"
        """
        return self._fill

    @fill.setter
    def fill(self, value):
        if self._fill != value:
            self._fill = value
            self._notify("fill", {"fill": value})

    @property
    def points(self):
        """expose the structure's point list"""
        return self._points

    @points.setter
    def points(self, value):
        self._points = value
        self._notify("replace_poits", {"new_points":value})


    def as_ini_section(self):
        """returns a dict that looks like the raw data loaded from the ship file

                but with the edited points
            intended to be used to write a new ship file with the modifications
        """
        section_content = {}
        for index, point in enumerate(self._points):
            angle = int(pi/2.0 * 1.0/sd.ANGLE_TO_RADS)
            if point[1] != 0:
                angle = int(atan2(-point[0], -point[1]) * 1.0/sd.ANGLE_TO_RADS)
            distance = int(sqrt(pow(point[0], 2) + pow(point[1], 2))/sd.STRUCTURE_TO_FUNNEL)
            section_content[f"Point{index}Angle"] = angle
            section_content[f"Point{index}Distance"] = distance
            if len(section_content)//2 >= STRUCTURE_POINTS_MAX:
                break

        #pad the dict to the specified point amount with "empty" points
        if len(section_content)/2 < STRUCTURE_POINTS_MAX:
            for index in range(len(section_content)//2, STRUCTURE_POINTS_MAX):
                section_content[f"Point{index}Angle"] = 0
                section_content[f"Point{index}Distance"] = 0

        if self._fill:
            section_content["IsLine"] = 0
        else:
            section_content["IsLine"] = 1
        return section_content

    def update_point(self, point_index, new_x, new_y):
        """Call this when updating a point

        It assumes the arguments are correct
            PLEASE OH PLEASE do not change the point list directly but use this method
        Args:
            point_index (int): the index of the point to be changed in the points list
            new_x (number): new value for x coordinate, funnel coordinates
            new_y (number):  new value for y coordinate, funnel coordinates
        """
        self._points[point_index] = (new_x, new_y)
        self._notify("update", {"index":point_index, "x":new_x, "y":new_y})

    def add_point(self, point_index, new_x, new_y):
        """Call this when adding a point

        It assumes the arguments are correct
            PLEASE OH PLEASE do not change the point list directly but use this method
            or replace the whole list
        Args:
            point_index (int): the index of the point to be added in the points list
            new_x (number): new value for x coordinate, funnel coordinates
            new_y (number):  new value for y coordinate, funnel coordinates
        """
        self._points.insert(point_index, (new_x, new_y))
        self._notify("add_point", {"index":point_index, "x":new_x, "y":new_y})

    def delete_point(self, point_index):
        """Call this when updating a point

        It assumes the arguments are correct

        Args:
            point_index (int): the index of the point to be changed in the points list
        """
        self._points.pop(point_index)
        self._notify("delete_point", {"index": point_index})

class UpdatePoint(Command):
    """Command to update a point

    Args:
        structure (Structure): the structure to be updated
        point_index (int): the index of the point to be changed in the points list
        new_x (number): new value for x coordinate
        new_y (number):  new value for y coordinate
    """
    def __init__(self, structure, point_index, new_x, new_y):
        super().__init__()
        self.structure = structure
        self.point_index = point_index
        self.new_x = new_x
        self.new_y = new_y
        self.old_x = structure.points[point_index][0]
        self.old_y = structure.points[point_index][1]

    def execute(self):
        """update the point
        """
        if (round(self.new_x, 1) != round(self.old_x, 1) or
                round(self.new_y, 1) != round(self.old_y, 1)):
            self.structure.update_point(self.point_index, self.new_x, self.new_y)

    def undo(self):
        """restore the point to its previous value
        """
        self.structure.update_point(self.point_index, self.old_x, self.old_y)

class DeletePoint(Command):
    """Command to delete a point

    Args:
        structure (Structure): the structure to be updated
        point_index (int): the index of the point to be deleted in the points list
    """
    def __init__(self, structure, point_index):
        super().__init__()
        self._structure = structure
        self._point_index = point_index
        self._old_point = self._structure.points[point_index]

    def execute(self):
        """Delete the point
        """
        self._structure.delete_point(self._point_index)

    def undo(self):
        """restore the point
        """
        self._structure.add_point(self._point_index, *self._old_point)

class AddPoint(Command):
    """Command to add a point

    Args:
        structure (Structure): the structure to be updated
        point_index (int): the index of the new point in the points list
            all following points will move to their index+1
        new_x (number): new value for x coordinate
        new_y (number):  new value for y coordinate
    """
    def __init__(self, structure, point_index, new_x, new_y):
        super().__init__()
        self._structure = structure
        self._point_index = point_index
        self._new_point = (new_x, new_y)

    def execute(self):
        """Add point
        """
        self._structure.add_point(self._point_index, *self._new_point)

    def undo(self):
        """remove the new point
        """
        self._structure.delete_point(self._point_index)

class SetFill(Command):
    """Command to change the fill state of a structure

    Args:
        structure (Structure): the structure to be updated
        fill_state (bool): true for filled, false for only lines
    """
    def __init__(self, structure, fill_state):
        super().__init__()
        self._structure = structure
        self._fill_state = fill_state
        self._old_fill_state = structure.fill

    def execute(self):
        """Set the new fill state
        """
        if self._old_fill_state != self._fill_state:
            self._structure.fill = self._fill_state

    def undo(self):
        """Restore the old fill state
        """
        if self._old_fill_state != self._fill_state:
            self._structure.fill = self._old_fill_state

class ApplySymmetry(Command):
    """Make a structure symmetrical

    The side that will be mirrored is the side of the first point that is not on the centerline
    the points after the first point that on the other side of the centerline will be deleted
    """
    def __init__(self, structure):
        super().__init__()
        self._structure = structure
        #fun with pass by reference vs pass by value
        self._old_points = structure.points

        self._new_points = []
        port_side_first = True
        #find the first point that is not on the centerline of the ship
        for point in structure.points:
            if point[0] > 0:
                port_side_first = False
                break
            elif point[0] < 0:
                port_side_first = True
                break

        #add the points that are on the side to mirror
        #and build the list of points to add
        #the first point that is not on this side is the first point to delete
        #all following points will be deleted
        points_to_mirror = []
        for point in structure.points:
            if (point[0] == 0 or
                    (point[0] < 0 and port_side_first) or
                    (point[0] > 0 and not port_side_first)):
                self._new_points.append((point[0], point[1]))
                points_to_mirror.insert(0, (-point[0], point[1]))
            else:
                break
        #concatene the points to keep and points to add
        self._new_points = self._new_points + points_to_mirror

    def execute(self):
        self._structure.points = self._new_points

    def undo(self):
        self._structure.points = self._old_points

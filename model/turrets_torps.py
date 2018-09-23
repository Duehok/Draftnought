"""Turrets and torpedo mpunt data in a useable form"""

from schemas import TURRETS

class Turret:
    """Container for the data needed to draw a turret
    Args:
        caliber (int): caliber of the gun in inches (urgh)
        pos (string): the letter of the turret, like "A", "X", etc...
            positions 1 to 4 are also passed as strings
        guns (int): how many guns in the turret
        half_length (int): the length from middle to bow of the ship, in funnel coordinates
        all_turrs (list[string]): the list of all the turret position used on the ship
        parameters (Parameters): parameters for the whole program
    Attr:
        outline (list[(x,y)]): a list of vertexes for the turret's outline. In funnel coordinates
    """
    def __init__(self, caliber, pos, guns, half_length, all_turrs, parameters):
        to_bow = parameters.turrets_positions[pos]["to_bow"]
        scale = parameters.turrets_scale[caliber]

        rel_position = rel_tur_or_torp_position(pos, all_turrs, parameters)

        position = (rel_position[0]*half_length, rel_position[1]*half_length)
        raw_outline = parameters.turrets_outlines[guns]
        #mirror if the turret should be backward
        if not to_bow:
            mirrored_outline = [(vertex[0], -vertex[1]) for vertex in raw_outline]
        else:
            mirrored_outline = raw_outline
        #also mirror if the turret is to starboard
        if position[0] >0:
            mirrored_outline = [(-vertex[0], vertex[1]) for vertex in mirrored_outline]
        #scale according to gun caliber
        scaled_outline = [(vertex[0]*scale, vertex[1]*scale) for vertex in mirrored_outline]
        #move according to position
        self.outline = [(vertex[0]+position[0], vertex[1]+position[1]) for vertex in scaled_outline]

def rel_tur_or_torp_position(pos, all_turrs, parameters):
    """Apply the game's logic to get a turret or toorp mount position

    Args:
        pos (string): the letter of the turret, like "A", "X", etc...
            positions 1 to 4 are also passed as strings
        all_turrs (list[string]): the list of all the turret position used on the ship
        parameters (Parameters): parameters for the whole program
    """
    rel_position = parameters.turrets_positions[pos]["positions"][0]

    if pos == "X":
        if ("W" in all_turrs or "V" in all_turrs or
                "R" in all_turrs or "C" in all_turrs):
            rel_position = parameters.turrets_positions[pos]["positions"][1]

    elif pos == "W":
        if ("X" in all_turrs or "V" in all_turrs or "B" in all_turrs):
            rel_position = parameters.turrets_positions[pos]["positions"][1]

    elif pos == "A":
        if ("V" in all_turrs or
                {"W", "X", "Y"}.issubset(all_turrs) or
                "C" in all_turrs and "X" in all_turrs or
                "B" in all_turrs and "R" in all_turrs and (
                    ("W" in all_turrs or "X" in all_turrs or "Y" in all_turrs))):
            rel_position = parameters.turrets_positions[pos]["positions"][2]
        elif ("X" in all_turrs or  "W" in all_turrs or
              "B" in all_turrs and ("C" in all_turrs or "R" in all_turrs or "W" in all_turrs)):
            rel_position = parameters.turrets_positions[pos]["positions"][1]

    elif pos == "B":
        if ("V" in all_turrs or
                "W" in all_turrs or
                "C" in all_turrs and ("X" in all_turrs or "Y" in all_turrs) or
                "A" in all_turrs and "R" in all_turrs and ("X" in all_turrs or "Y" in all_turrs)):
            rel_position = parameters.turrets_positions[pos]["positions"][2]
        elif ("X" in all_turrs or "Y" in all_turrs or "C" in all_turrs or "R" in all_turrs):
            rel_position = parameters.turrets_positions[pos]["positions"][1]

    elif pos == "Y":
        if (("X" in all_turrs and "W" in all_turrs.keys()) or
                ("V" in all_turrs and "W"in all_turrs)):
            rel_position = parameters.turrets_positions[pos]["positions"][3]
        elif ("V" in all_turrs or "W" in all_turrs or
              ({"A", "B", "C"}.issubset(all_turrs)) or
              ({"A", "B", "R"}.issubset(all_turrs))):
            rel_position = parameters.turrets_positions[pos]["positions"][2]
        elif ("B" in all_turrs or "C" in all_turrs or "R" in all_turrs or "X" in all_turrs):
            rel_position = parameters.turrets_positions[pos]["positions"][1]
    return rel_position

class Torpedo:
    """Container for the data needed to draw a torpedo mount
    Args:
        section_content (dict): the a TorpedoMount<x> section from the parser
            that read the ship file
        half_length (int): the length from middle to bow of the ship, in funnel coordinates
        parameters (Parameters): parameters for the whole program
    Attr:
        outline (list[(x,y)]): a list of vertexes for the mount's outline. In funnel coordinates
    """
    def __init__(self, section_content, half_length, parameters):
        pos = section_content["Pos"]
        tubes_count = int(section_content["Tubes"])

        if pos in TURRETS:
            to_bow = parameters.turrets_positions[pos]["to_bow"]
            rel_position = parameters.turrets_positions[pos]["positions"][0]

        else:
            to_bow = True
            #draw the mount outside of the visible area, so hidden
            rel_position = [0, 1.5]

        position = (rel_position[0]*half_length, rel_position[1]*half_length)
        raw_outline = parameters.torpedo_outlines[tubes_count]
        #rotate if the turret should be backward
        if not to_bow:
            rotated_outline = [(point[0], -point[1]) for point in raw_outline]
        else:
            rotated_outline = raw_outline
        #move according to position
        self.outline = [(point[0]+position[0], point[1]+position[1]) for point in rotated_outline]

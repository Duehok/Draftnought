#Turret positions
TURRETS = ["1", "2", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
           "Q", "R", "S", "T", "V", "W", "X", "Y", "3", "4"]

TURRETS_POSITION_SCHEMA = (
{
  "$schema" : "http://json-schema.org/draft-04/schema#",
  "patternProperties":
  {
    ".*":
    {
      "turret":
      {
        "type":"object", 
        "properties":
        {
          "to_bow": {"type":"boolean"},
          "positions":
          {
            "type": "array",
            "items":
            {
              "items":[{ "type":"number"},{ "type":"number"}],
              "additionalItems":False
            },
            "maxItems":4,
            "minItems":1,
            "additionalItems":False
          }
        }
      }
    }
  },
  "required": TURRETS,
  "additionalProperties":False
})
_DEFAULT_TURRET_POSITION = {"positions": [(1000, 1000), (1000, 1000), (1000, 1000), (1000, 1000)],
                           "to_bow": True}
DEFAULT_TURRETS_POSITION = {turret:_DEFAULT_TURRET_POSITION for turret in TURRETS}

#turret outlines
MAX_GUNS_PER_TURRET = 4
TURRETS_OUTLINE_SCHEMA =(
{
  "$schema" : "http://json-schema.org/draft-04/schema#",
  "type":"array",
  "items":
  {
    "type":"array",
    "items":
    {
      "type":"array",
      "items":[{"type":"number"}],
      "maxItems":2,
      "minItems":2
    }
  },
  "maxItems":MAX_GUNS_PER_TURRET+1,
  "minItems":MAX_GUNS_PER_TURRET+1
})

_DEFAULT_TURRET_OUTLINE = [[-7.4, 12.9], [-10, -0.1], [-6.5, -7.4], [-1.2, -9.6],
                          [-0.7, -30], [0.7, -30], [1.2, -9.6], [6.5, -7.4], [10, -0], [7.4, 12.9]]

DEFAULT_TURRETS_OUTLINE = [_DEFAULT_TURRET_OUTLINE for i in range(MAX_GUNS_PER_TURRET+1)]

#turret scale
MIN_MAX_GUN_CALIBER = 18
TURRETS_SCALE_SCHEMA =(
{
  "$schema" : "http://json-schema.org/draft-04/schema#",
  "type":"array",
  "items":
  {
    "type":"number"
  },
  "maxItems":MIN_MAX_GUN_CALIBER+1,
  "minItems":MIN_MAX_GUN_CALIBER+1
}
)

DEFAULT_TURRETS_SCALE = [0.22, 0.26, 0.306, 0.347, 0.387, 0.422, 0.458, 0.536,
                         0.615, 0.657, 0.700, 0.746, 0.793, 0.867, 0.942, 0.971,
                         1.000, 1.091, 1.091]

#hull shapes
SHIP_TYPES = ["BB", "BC", "B", "CA", "CL", "DD", "MS", "AMC"]
HULLS_SHAPES_SCHEMA = (
{
  "$schema" : "http://json-schema.org/draft-04/schema#",
  "patternProperties":
  {
    ".*":
    { 
      "type":"array",
      "items":
      {
        "type":"array",
        "items":
        {
          "type":"array",
          "items":[{"type":"number"}],
          "maxItems":2,
          "minItems":2
        }
      }
    }
  },
  "required":SHIP_TYPES
})
DEFAULT_HULLS_SHAPES = {ship_type:[[[100, 100],[-100, 100],[-100, -100],[100, -100]]] for ship_type in SHIP_TYPES}


HALF_LENGTHS_SCHEMA = (
{
  "$schema" : "http://json-schema.org/draft-04/schema#",
  "patternProperties":
  {
    ".*":
    { 
      "patternProperties":
      {
        "^[0-9]+$":{"type":"number"}
      },
      "required":["2000000"]
    }
  },
  "required":SHIP_TYPES
})
DEFAULT_HALF_LENGTHS = {ship_type:{"2000000":200} for ship_type in SHIP_TYPES}

RECENT_FILES_SCHEMA = (
  {
    "$schema" : "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties":
    {
      "type": "object",
      "properties":
      {
        "zoom":{"type":"number"},
        "offset":
        {
          "type":"array",
          "items":
          [
            {"type":"number"}, {"type":"number"}
          ],
          "additionalItems": False
        }
      },
      "additionalProperties": False
    }
  }
)

DEFAULT_RECENT_FILES ={}
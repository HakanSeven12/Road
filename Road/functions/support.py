# SPDX-License-Identifier: LGPL-2.1-or-later

"""
Useful math functions and constants
"""
import math
import FreeCAD as App
from collections.abc import Iterable
from ..utils.tuple_math import TupleMath


class Constants:
    """
    Useful math constants
    """

    TWO_PI = math.pi * 2.0          # 2 * pi in radians
    HALF_PI = math.pi / 2.0         # 1/2 * pi in radians
    ONE_RADIAN = 180 / math.pi      # one radian in degrees
    TOLERANCE = 0.0001              # tolerance for differences in measurements
    UP = 0.0, 1.0, 0.0              # Up vector
    Z_DEPTH = [0.0, 0.05, 0.1]      # Z values to provide rendering layers

def get_doc_units():
    """
    Return the units (feet / meters) of active document

    format - string format (0 = abbreviated, 1 = singular, 2 = plural)
    """
    #need to add support for international spellings for metric units

    english = ['ft', 'foot', 'feet']
    metric = ['m', 'meter', 'meters']

    if App.ParamGet(
                'User parameter:BaseApp/Preferences/Units'
                ).GetInt('UserSchema', 0)  == 7:
        return english

    return metric

def scale_factor():
    """
    Return the scale factor to convert the document units to mm
    """

    if get_doc_units()[0] == 'ft':
        return 304.80

    return 1000.0

def to_float(value):
    """
    Return value as a float, if possible.
    If value is a list, non-float values are returned as None
    Float 'nan' values are converted to None
    """

    result = None

    if value is None:
        return None

    if isinstance(value, list):
        result = []

        for _v in value:
            result.append(to_float(_v))

    else:

        try:
            result = float(value)

        except ValueError:
            pass

        if result:
            if math.isnan(result):
                result = None

    return result

def to_int(value):
    """
    Return true if string is an integer
    """

    result = None

    if isinstance(value, list):

        result = []

        for _v in value:

            _f = to_int(_v)

            if not _f:
                return None

            result.append(_f)

        return result

    try:
        result = int(float(value))

    except ValueError:
        pass

    return result

def safe_sub(lhs, rhs, return_none=False):
    """
    Safely subtract two vectors.
    Returns an empty vector or None if either vector is None
    """

    if not lhs or not rhs:

        if return_none:
            return None

        return [0, 0, 0]

    return TupleMath.subtract(lhs,rhs)

def get_rotation(in_vector, out_vector=None):
    """
    Returns the rotation as a signed integer:
    1 = cw, -1 = ccw, 0 = fail

    if in_vector is an instance, out_vector is ignored.
    """
    if not all([in_vector, out_vector]):return 0

    _in = App.Vector(in_vector)
    _out = App.Vector(out_vector)


    if not all([_in, _out]):
        return 0

    if not (_in.Length and _out.Length):
        return 0

    return -1 * math.copysign(1, _in.cross(_out).z)

def get_quadrant(vector):
    """
    Returns the quadrant of the vector:
    0 = 0-90
    1 = 90-180
    2 = 180-270
    3 = 270-360

    zero values will read positive, defaulting to right / upper halves
    """

    _v = int(vector.y < 0.0)
    _h = int(vector.x < 0.0)

    return [[0, 1], [3, 2]][_h][_v]

def within_tolerance(lhs, rhs=None, tolerance=0.0001):
    """
    Determine if two values are within a pre-defined tolerance

    lhs / rhs - values to compare
    If rhs is none, lhs may be a list of values to compare
    or a single value to compare with tolerance

    List comparisons check every value against every other
    and errors if any checks fail
    """

    if not isinstance(lhs, Iterable):
        lhs = [lhs]

    if not isinstance(rhs, Iterable):
        rhs = [rhs]

    #item list eliminates none types
    item_list = [_v for _v in tuple(lhs) + tuple(rhs) if _v is not None]

    if not item_list:
        print('utils.within_tolerance() - empty item list')
        return False

    #abort if any of the data types are not valid
    if not all([
            isinstance(_i, (App.Vector, list, float, int)) for _i in item_list
        ]):
        print('utils.within_tolerance() - invalid type')
        return False

    items = []

    #convert all items of valid type to lists
    for item in item_list:

        result = item

        if isinstance(item, App.Vector):
            result = list(item)

        elif not isinstance(item, list):
            result = [item]

        items.append(result)

    #default to left-hand side value
    _delta = items[0]

    #at this point, either both items are defined or at least one is.
    if len(items) == 2:

        #abort if lists aren't the same length
        if len(items[0]) != len(items[1]):
            return False

        #perform element-wise difference and save truth list
        _delta = [
            abs(_i[0] - _i[1]) for _i in zip(items[0], items[1])
        ]

    _truth = [abs(_i) <= tolerance for _i in _delta]

    return all(_truth)

def vector_ortho(vector):
    """
    Returns the orthogonal of a 2D vector as (-y, x)
    """

    vec_list = vector

    if not isinstance(vector, list):
        vec_list = [vector]

    result = []

    for vec in vec_list:
        result.append(App.Vector(-vec.y, vec.x, 0.0))

    if len(result) == 1:
        return result[0]

    return result

def vector_from_angle(angle):
    """
    Returns a vector form a given angle in radians
    """

    _angle = to_float(angle)

    if not _angle:
        return None

    return [math.sin(_angle), math.cos(_angle), 0.0]

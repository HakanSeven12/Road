# SPDX-License-Identifier: LGPL-2.1-or-later

"""
Line generation tools
"""

import FreeCAD
import math

from ...functions import support
from ...utils.tuple_math import TupleMath


class Line():
    """
    Line class object
    """
    _keys = [
        'ID', 'Type', 'Start', 'End', 'Bearing', 'Length', 'StartStation',
        'InternalStation', 'PI', 'Center', 'Description', 'Status', 'ObjectID', 'Note'
    ]

    def __init__(self, line_dict=None):
        """
        Line class constructor
        """

        self.id = ''
        self.type = 'Line'
        self.start = None
        self.end = None
        self.bearing = math.nan
        self.length = 0.0
        self.start_station = 0.0
        self.internal_station = [0.0, 0.0]
        self.pi = None
        self.center = None
        self.description = ''
        self.status = ''
        self.object_id = ''
        self.note = ''

        # Build a list of key pairs for string-based lookup
        self._key_pairs = {}

        _keys = list(self.__dict__.keys())

        for _i, _k in enumerate(Line._keys):
            self._key_pairs[_k] = _keys[_i]

            self._key_pairs['BearingIn'] = 'bearing'
            self._key_pairs['BearingOut'] = 'bearing'


        if line_dict:
            for _k, _v in line_dict.items():
                self.set(_k, _v)

    def __str__(self):
        """
        String representation
        """

        return str(self.__dict__)

    def to_dict(self):
        """
        Return the object as a dictionary
        """

        _result = {}

        _result.update(
            [(_k, getattr(self, _v)) for _k, _v in self._key_pairs.items()])

        return _result

    def get_bearing(self):
        """
        Getter function for bearing_in / bearing_out aliasing
        """

        return self.bearing

    def set_bearing(self, value):
        """
        Setter function for bearing_in / bearing_out aliasing
        """

        self.bearing = value

    def get(self, key):
        """
        Generic getter for class attributes
        """

        if not key in self.__dict__:

            assert (key in self._key_pairs), """
                \nArc.get(): Bad key: ' + key + '\n')
                """

            key = self._key_pairs[key]

        _value = getattr(self, key)

        if _value and key in ('start', 'end', 'pi', 'center'):
            _value = tuple(_value)

        return _value

    def set(self, key, value):
        """
        Generic setter for class attributes
        """

        if not key in self._key_pairs:

            FreeCAD.Console.PrintError('\nLine.set(): Bad key' + key)
            return

        if value and key.lower() in ('start', 'end', 'pi', 'center'):
            value = tuple(value)

        setattr(self, self._key_pairs[key], value)

    # Alias bearing_in / bearing_out with the bearing attribute
    # provides compatibility with curve classes
    bearing_in = property(get_bearing, set_bearing)
    bearing_out = property(get_bearing, set_bearing)

def get_parameters(line, as_dict=True):
    """
    Return a fully-defined line
    """

    _result = line

    if isinstance(line, dict):
        _result = Line(line)

    _coord_truth = [_result.start, _result.end]
    _param_truth = [not math.isnan(_result.bearing), _result.length > 0.0]

    # Both coordinates defined
    _case_one = all(_coord_truth)

    # Only one coordinate defined, plus both length and bearing
    _case_two = any(_coord_truth) \
                and not all(_coord_truth) \
                and all(_param_truth)

    if _case_one:

        line_vec = TupleMath.subtract(_result.end, _result.start)

        _length = TupleMath.length(line_vec)

        if _result.length:
            if support.within_tolerance(_result.length, _length):
                _length = _result.length

        _result.length = _length

    elif _case_two:

        _vec = \
            support.vector_from_angle(_result.bearing).multiply(_result.length)

        if _result.start:
            _result.end = TupleMath.add(_result.start, _vec)
        else:
            _result.start = TupleMath.add(_result.end, _vec)

    else:
        print('Unable to calculate parameters for line', _result)

    if as_dict:
        return _result.to_dict()

    return _result

def get_coordinate(start, bearing, distance):
    """
    Return the x/y coordinate of the line at the specified distance along it
    """

    _vec = TupleMath.bearing_vector(bearing)

    return TupleMath.add(
        tuple(start), TupleMath.scale(tuple(_vec), distance)
    )

def get_tangent_vector(line, distance):
    """
    Return the directed tangent vector
    """

    _start = line.start
    _end = line.end

    if _start is None or _end is None:
        return None, None

    _slope = TupleMath.unit((-(_end[1] - _start[1]), _end[0] - _start[0]))

    _coord = TupleMath.add(get_coordinate(
        line.start, line.bearing, distance
        ), _slope)

    return _coord, _slope

def get_ortho_vector(line, distance, side=''):
    """
    Return the orthogonal vector pointing toward the indicated side at the
    provided position. Defaults to left-hand side
    """

    _dir = 1.0

    _side = side.lower()

    if _side in ['r', 'rt', 'right']:
        _dir = -1.0

    start = tuple(line.get('Start'))
    end = tuple(line.get('End'))
    bearing = line.get('BearingIn')

    if (start is None) or (end is None):
        return None, None

    _delta = TupleMath.subtract(end, start)
    _delta = TupleMath.unit(_delta)

    _left = tuple((-_delta[1], _delta[0], 0.0))

    _coord = get_coordinate(start, bearing, distance)

    return _coord, TupleMath.multiply(_left, _dir)

def get_orthogonal_point(start_pt, end_pt, coord):
    """
    Return the point on the line specified by the projection of coord
    """
    _x = (coord[0] - start_pt[0]) * (end_pt[0] - start_pt[0])
    _y = (coord[1] - start_pt[1]) * (end_pt[1] - start_pt[1])

    # Euclidean distance
    _d = (end_pt[0] - start_pt[0])**2 + (end_pt[1] - start_pt[1])**2

    _u = (_x + _y) / _d

    return (
        start_pt[0] + (_u * (end_pt[0] - start_pt[0])),
        start_pt[1] + (_u * (end_pt[1] - start_pt[1])),
        0.0
    )

def get_position_offset(line, coord):
    """
    Find the station (distance along line), point on line, offset distance,
    and boundary status for the given coordinate
    
    Returns:
        station - distance along line from start point
        point - coordinate of projection point on line
        offset - perpendicular distance from line (+ for left, - for right)
        bound - boundary status: -1 (before start), 0 (on line), 1 (after end)
    """

    line = Line(line)

    _start = line.start
    _end = line.end
    _length = line.length

    # Check if coordinate is at start or end point
    if support.within_tolerance(TupleMath.length(TupleMath.subtract(coord, _start))):
        return 0.0, _start, 0.0, 0

    if support.within_tolerance(TupleMath.length(TupleMath.subtract(coord, _end))):
        return _length, _end, 0.0, 0

    # Get the orthogonal projection point on the line
    _proj_point = get_orthogonal_point(_start, _end, coord)

    # Calculate station (distance from start to projection point)
    _station = TupleMath.length(TupleMath.subtract(_proj_point, _start))

    # Calculate offset (perpendicular distance from line)
    _offset_dist = TupleMath.length(TupleMath.subtract(coord, _proj_point))

    # Calculate direction vector of line
    _line_vec = TupleMath.unit(TupleMath.subtract(_end, _start))

    # Calculate vector from projection point to coordinate
    _offset_vec = TupleMath.subtract(coord, _proj_point)

    # Determine sign of offset using cross product
    # Positive = left side, Negative = right side
    _cross = TupleMath.cross(_line_vec, _offset_vec)
    _sign = 1.0 if _cross[2] > 0 else -1.0

    _offset = _offset_dist * _sign

    # Check boundary conditions
    if support.within_tolerance(_station, 0.0) or _station < 0:
        if _station < 0 and not support.within_tolerance(_station, 0.0):
            # Point is before line start
            _dist_to_start = TupleMath.length(TupleMath.subtract(coord, _start))
            return 0.0, _start, _dist_to_start, -1
        else:
            # Very close to start, consider it on line
            return 0.0, _proj_point, _offset, 0

    elif support.within_tolerance(_station, _length) or _station > _length:
        if _station > _length and not support.within_tolerance(_station, _length):
            # Point is after line end
            _dist_to_end = TupleMath.length(TupleMath.subtract(coord, _end))
            return _length, _end, _dist_to_end, 1
        else:
            # Very close to end, consider it on line
            return _length, _proj_point, _offset, 0

    else:
        # Point projection is within line bounds
        return _station, _proj_point, _offset, 0
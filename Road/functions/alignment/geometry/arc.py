# SPDX-License-Identifier: LGPL-2.1-or-later

"""
Arc generation tools
"""

import math
import numpy

from FreeCAD import Console

from ... import support
from ....utils.tuple_math import TupleMath

C = support.Constants

class Arc():
    """
    Arc class object
    """

    _keys = [
        'ID', 'Type', 'Start', 'End', 'PI', 'Center', 'BearingIn',
        'BearingOut', 'Length', 'StartStation', 'InternalStation', 'Delta',
        'Direction', 'Tangent', 'Radius', 'Chord', 'Middle', 'MiddleOrdinate',
        'External', 'CurveType', 'Hash', 'Description', 'Status', 'ObjectID',
        'Note', 'Bearings', 'Points'
    ]

    def __init__(self, source_arc=None):
        """
        Arc class constructor
        """

        self.id = ''
        self.type = 'Curve'
        self.start = None
        self.end = None
        self.pi = None
        self.center = None
        self.bearing_in = math.nan
        self.bearing_out = math.nan
        self.length = 0.0
        self.start_station = 0.0
        self.internal_station = (0.0, 0.0)
        self.delta = 0.0
        self.direction = 0.0
        self.tangent = 0.0
        self.radius = 0.0
        self.chord = 0.0
        self.middle = 0.0
        self.middle_ordinate = 0.0
        self.external = 0.0
        self.curve_type = 'Arc'
        self.hash = ''
        self.description = ''
        self.status = ''
        self.object_id = ''
        self.note = ''
        self.bearings = None
        self.points = []

        if isinstance(source_arc, Arc):
            self.__dict__ = source_arc.__dict__.copy()
            self._key_pairs = source_arc._key_pairs.copy()
            return

        # Build a list of key pairs for string-based lookup
        self._key_pairs = {}

        _keys = list(self.__dict__.keys())

        for _i, _k in enumerate(Arc._keys):
            self._key_pairs[_k] = _keys[_i]

        if not source_arc:
            return

        if isinstance(source_arc, dict):

            for _k, _v in source_arc.items():
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

        if not key in self.__dict__:

            assert (key in self._key_pairs), """
                \nArc.set(): Bad key: ' + key + '\n')
                """

            key = self._key_pairs[key]

            if value and key in ('start', 'end', 'pi', 'center'):
                value = tuple(value)

        setattr(self, key, value)

    def update(self, values):
        """
        Update the parameters of the arc with values in passed dictionary
        """

        for _k, _v in values.items():
            self.set(_k, _v)

def _create_geo_func():

    _fn = []

    # Create a square matrix of empty lambdas
    for _i in range(0, 6):
        _fn.append([lambda _x: 0.0]*7)

    _fn.append([lambda _x: _x]*7)

    # Vector order: Radius Start, Radius End, Tangent Start, Tangent End,
    # Middle, Chord, UP

    _fn[1][0] = lambda _x: _x
    _fn[3][2] = _fn[1][0]

    _fn[5][0] = lambda _x: _x*2 - math.pi
    _fn[4][3] = _fn[5][0]

    _fn[5][1] = lambda _x: math.pi - _x*2
    _fn[4][2] = _fn[5][1]

    _fn[3][0] = lambda _x: _x - C.HALF_PI
    _fn[2][1] = lambda _x: C.HALF_PI - _x

    _fn[4][0] = lambda _x: _x*2
    _fn[4][1] = _fn[4][0]
    _fn[5][2] = _fn[4][0]
    _fn[5][3] = _fn[4][0]

    # -------------------------------------------------------------------
    # Bearing lambdas for the curve's vector dot products:
    #   0 - Radius Start    (START - CENTER)
    #   1 - Radius End      (END - CENTER)
    #   2 - Tangent Start   (PI - START)
    #   3 - Tangent End     (END - PI)
    #   4 - Middle Ordinate (PI - CENTER)
    #   5 - Chord           (END - START)
    # -------------------------------------------------------------------
    _fn[6][0] = lambda _x, _delta, _rot: _x + _rot*C.HALF_PI
    _fn[6][1] = lambda _x, _delta, _rot: _x + _rot*(-_delta+C.HALF_PI)
    _fn[6][2] = lambda _x, _delta, _rot: _x
    _fn[6][3] = lambda _x, _delta, _rot: _x - _rot*_delta
    _fn[6][4] = lambda _x, _delta, _rot: _x + _rot*(C.HALF_PI - _delta/2.0)
    _fn[6][5] = lambda _x, _delta, _rot: _x - _rot*(_delta/2.0)

    return _fn


class _GEO:
    '''
    Create the geometry functions for arc processing
    '''
    FUNC = _create_geo_func()

    # List of vector pairs to calculate rotations
    ROT_PAIRS = [
        [1, 2, 4, 5],
        [3, 5],
        [1, 3, 5],
        [0],
        [1, 2, 3, 5],
        [3]
    ]

def get_scalar_matrix(vecs):
    """
    Calculate the square matrix of scalars
    for the provided vectors
    """

    # -------------------------------
    # Matrix format:
    #
    #   |  RST
    #   |        REND
    #   |                TST
    #   |                        TEND
    #   |                                MORD
    #   |                                       CHORD
    #   |                                                UP
    # --------------------------------

    # Ensure list is a list of lists (not vectors) and create the matrix
    mat_list = [list(_v) if _v else [0, 0, 0] for _v in vecs]
    rot_list = [0.0]*7

    # Get rotation direction for vector bearings
    for _i in range(0, 6):
        rot_list[_i] = support.get_rotation(C.UP, vecs[_i])

    mat_list.append(list(C.UP))

    mat = numpy.matrix(mat_list)
    _result = mat * mat.T

    # Abort for non-square matrices
    if (_result.shape[0] != _result.shape[1]) or (_result.shape[0] != 7):
        return None

    # Calculate the magnitudes first (minus the UP vector)
    for _i in range(0, 6):
        _result.A[_i][_i] = math.sqrt(_result.A[_i][_i])

    # Calculate the delta for the lower left side
    # This is a dot-product calculation to determine the angle between vectors
    for _i in range(0, 7):
        _d1 = _result.A[_i][_i]

        for _j in range(0, _i):

            _denom = _d1 * _result.A[_j][_j]
            _n = _result.A[_i][_j]

            _angle = None

            if not (any([math.isnan(_v) for _v in [_denom, _n]])
                    or _denom == 0.0):

                _ratio = _n / _denom

                if abs(_ratio) > 1.0:
                    _ratio = math.copysign(1, _ratio)

                _angle = math.acos(_ratio)

            # Compute the arc central angle for all but the last row
            if _angle:
                if _i < 6:
                    _angle = _GEO.FUNC[_i][_j](_angle)
                else:
                    _angle *= rot_list[_j]

                    if _angle < 0.0:
                        _angle += C.TWO_PI

            _result.A[_i][_j] = _angle

    # Lower left half contains angles, diagonal contains scalars
    return _result

def get_bearings(arc, mat, delta, rot):
    """
    Calculate the bearings from the matrix and delta value
    """
    if rot is None:
        rot = 0.0

    bearing_in = arc.get('BearingIn')
    bearing_out = arc.get('BearingOut')

    bearings = mat.A[6]

    if not any([math.isnan(_v) for _v in bearings]):

        # Calculate the delta angle from the radius and tangent bearings
        # as a cross check
        _deltas = [
            abs(bearings[0] - bearings[1]), abs(bearings[2] - bearings[3])
        ]

        # If delta exceeds PI, the wrong direction was calculated. Reverse.
        for _i, _v in enumerate(_deltas):
            if _v > math.pi:
                _deltas[_i] = math.pi*2 - _v

        assert(support.within_tolerance(_deltas)),\
        f"""
            Radius bearing/delta tolerance fail: {str(_deltas[0])} != {str(_deltas[1])}
        """

    # A negative rotation could push out bearing under pi
    # A positive rotation could push out bearing over 2pi
    _b_out = bearing_out

    # Restrict start bearing to [0, PI]
    _b_in = abs(bearing_in - int(bearing_in / math.pi) * math.pi)

    if not _b_out:
        _b_out = _b_in + (delta * rot)

    if _b_out < 0.0:
        _b_out += C.TWO_PI

    if _b_out >= C.TWO_PI:
        _b_out -= C.TWO_PI

    if not support.within_tolerance(_b_out, bearing_out):
        bearing_out = _b_out

    _row = mat.A[6]

    _rad = [_row[0], _row[1]]
    _tan = [bearing_in, bearing_out]
    _int = [_row[4], _row[5]]

    if not support.to_float(_rad[0]):
        _rad[0] = bearing_in - rot * (C.HALF_PI)

    if not support.to_float(_rad[1]):
        _rad[1] = _rad[0] + rot * delta

    if not support.to_float(_int[0]):
        _int[0] = _rad[0] + rot * (delta / 2.0)

    if not support.to_float(_int[1]):
        _int[1] = _rad[0] + rot * ((math.pi + delta) / 2.0)

    if _rad is None:
        _rad = arc.get('Radius')

    if _tan is None:
        _tan = arc.get('Tangent')

    if _int is None:
        _int = arc.get('Delta')

    mat_bearings = {
        'Radius': _rad,
        'Tangent': _tan,
        'Internal': _int
    }

    return {
        'BearingIn': bearing_in, 'BearingOut': bearing_out,
        'Bearings': mat_bearings
        }

def get_lengths(arc, mat):
    """
    Get needed parameters for arc calculation
    from the user-defined arc or the calculated vector matrix
    """

    # [0,1] = Radius; [2, 3] = Tangent, [4] = Middle, [5] = Chord
    lengths = mat.diagonal().A[0]

    params = [arc.get('Radius'), arc.get('Tangent'), arc.get('Middle'),
              arc.get('Chord'), arc.get('Delta')]

    for _i in range(0, 2):

        # Get two consecutive elements, saving only if they're valid
        _s = [_v for _v in lengths[_i*2:(_i+1)*2] if _v]

        # Skip the rest if not defined, we'll use the user values
        if not any(_s):
            continue

        # Duplicate the only calculated length
        if len(_s) == 1:
            _s.append(_s[0])

        # If both were calculated and they aren't the same, quit
        if all(_s) and not support.within_tolerance(_s[0], _s[1]):

            _attribs = ['radius', 'Start-Center-End']

            if _i == 1:
                _attribs = ['tangent', 'Start-PI-End']

            Console.PrintWarning("""
            \nArc {0} length and {1} distance mismatch by {2:f} mm. Using calculated value of {3:f} mm
            """\
                .format(_attribs[0], _attribs[1], abs(_s[1] - _s[0]), _s[0]))

        if _s[0]:
            if not support.within_tolerance(_s[0], params[_i]):
                params[_i] = _s[0]

    # Test middle and chord.
    # If no user-defined value or out-of-tolerance, use calculated
    for _i in range(4, 6):

        if lengths[_i]:
            if not support.within_tolerance(lengths[_i], params[_i - 2]):
                params[_i - 2] = lengths[_i]

    return {'Radius': params[0],
            'Tangent': params[1],
            'Middle': params[2],
            'Chord': params[3]}

def get_delta(arc, mat):
    """
    Get the delta value from the matrix, if possible,
    Default to the user-provided parameter if no calculated
    or values within tolerance
    """
    # Get the delta from the arc data as a default
    delta = arc.get('Delta')

    # Calculate the delta from the provided bearings, if they exist
    if not delta:
        if arc.get('BearingIn') and arc.get('BearingOut'):
            delta = abs(arc.get('BearingOut') - arc.get('BearingIn'))

    # Find the first occurrence of the delta value in the matrix
    if not delta:
        for _i in range(1, 6):
            for _j in range(0, _i):
                if support.to_float(mat.A[_i][_j]):
                    delta = mat.A[_i][_j]
                    break

    # If delta exceeds PI radians, swap it for lesser angle
    if delta:
        delta = abs((int(delta > math.pi) * C.TWO_PI) - delta)

    return {'Delta':delta}

def get_rotation(arc, vecs):
    """
    Determine the direction of rotation
    """

    # List all valid vector indices
    _idx = [_i for _i, _v in enumerate(vecs) if not TupleMath.is_zero(_v)]

    _v1 = None
    _v2 = None

    for _i in _idx:
        _l = _GEO.ROT_PAIRS[_i]
        _m = [_j for _j in _l if not TupleMath.is_zero(vecs[_j])]

        if _m:
            _v1 = vecs[_i]
            _v2 = vecs[_m[0]]
            break

    if not _v1:
        _v1 = support.vector_from_angle(arc.get('BearingIn'))

    if not _v2:
        _v2 = support.vector_from_angle(arc.get('BearingOut'))

    _rot = None

    if _v1 and _v2:
        _rot = support.get_rotation(_v1, _v2)

    else:
        _rot = arc.get('Direction')

    return {'Direction': _rot}

def get_missing_parameters(arc, new_arc, points):
    """
    Calculate any missing parameters from the original arc
    using the values from the new arc.

    These include:
     - Chord
     - Middle Ordinate
     - Tangent
     - Length
     - External distance
    """

    # By this point, missing radius / delta is a problem
    # Missing both? Stop now.
    if not new_arc.get('Radius') and not new_arc.get('Delta'):
        return None

    _half_delta = new_arc.delta / 2.0
    _cos_half_delta = math.cos(_half_delta)
    _tan_half_delta = math.tan(_half_delta)

    # Missing radius requires middle ordinate (or PI / Center coords)
    if not new_arc.get('Radius'):

        if new_arc.get('Tangent'):
            new_arc.set('Radius', new_arc.get('Tangent') / _tan_half_delta)

    if not new_arc.get('Radius'):

        # Attempt to assign middle length of curve
        if not new_arc.middle:

            if points[2] and points[3]:
                new_arc.middle = TupleMath.length(
                    TupleMath.subtract(points[3], points[2]))

        # Build radius from external, middle ordinate or middle length
        if new_arc.middle:
            new_arc.radius = new_arc.middle * _cos_half_delta

        elif new_arc.middle_ordinate:
            new_arc.radius = new_arc.middle_ordinate / (1 - _cos_half_delta)

        elif new_arc.external:
            new_arc.radius = new_arc.external / ((1/_cos_half_delta) - 1)

    # Abort if unable to determine radius
    if not new_arc.radius:
        return None

    if not new_arc.middle:
        new_arc.middle = \
            new_arc.radius * (_cos_half_delta + (1/_cos_half_delta))

    # Pre-calculate values and fill in remaining parameters
    if not new_arc.length:
        new_arc.length = new_arc.radius * new_arc.delta

    if not new_arc.external:
        new_arc.external = new_arc.radius * (1.0 / (_cos_half_delta - 1.0))

    if not new_arc.middle_ordinate:
        new_arc.middle_ordinate = new_arc.radius * (1.0 - _cos_half_delta)

    if not new_arc.tangent:
        new_arc.tangent = new_arc.radius * _tan_half_delta

    if not new_arc.chord:
        new_arc.chord = 2.0 * new_arc.radius * math.sin(_half_delta)

    # Quality-check - ensure everything is defined and default to
    # existing where within tolerance
    _keys = ['Chord', 'MiddleOrdinate', 'Tangent', 'Length', 'External']

    existing_vals = [arc.get(_k) for _k in _keys]
    new_vals = [new_arc.get(_k) for _k in _keys]

    vals = {}

    for _i, _v in enumerate(_keys):

        vals[_v] = existing_vals[_i]

        # If values are close enough, then keep existing
        if support.within_tolerance(vals[_v], new_vals[_i]):
            continue

        # Out of tolerance or existing is None - use the calculated value
        vals[_v] = new_vals[_i]

    return vals

def get_coordinates(arc, points):
    """
    Fill in any missing coordinates using arc parameters
    """

    vectors = {}

    for _k, _v in arc.get('Bearings').items():
        vectors[_k] = [support.vector_from_angle(_x) for _x in _v]

    _start = points[0]
    _end = points[1]
    _center = points[2]
    _pi = points[3]

    _vr = TupleMath.scale(vectors.get('Radius')[0], arc.get('Radius'))
    _vt0 = TupleMath.scale(vectors.get('Tangent')[0], arc.get('Tangent'))
    _vt1 = TupleMath.scale(vectors.get('Tangent')[1], arc.get('Tangent'))
    _vc = TupleMath.scale(vectors.get('Internal')[1], arc.get('Chord'))

    if not _start:

        if _pi:
            _start = TupleMath.subtract(_pi, _vt0)

        elif _center:
            _start = TupleMath.add(_center, _vr)

        elif _end:
            _start = TupleMath.subtract(_end, _vc)

    if not _start:
        return None

    if not _pi:
        _pi = TupleMath.add(_start, _vt0)

    if not _center:
        _center = TupleMath.subtract(_start, _vr)

    if not _end:
        _end = TupleMath.add(_pi, _vt1)

    return {'Start': _start, 'Center': _center, 'End': _end, 'PI': _pi}

def get_parameters(source_arc, as_dict=True):
    """
    Given a minimum of existing parameters, return a fully-described arc
    """

    _result = Arc(source_arc)

    # Vector order:
    # Radius in / out, Tangent in / out, Middle, and Chord

    points = [_result.start, _result.end, _result.center, _result.pi]
    point_count = len([_v for _v in points if _v])

    # Define the curve start at the origin if none is provided
    if point_count == 0:
        points[0] = (0.0, 0.0, 0.0)

    _vecs = [
        support.safe_sub(points[0], points[2], True),
        support.safe_sub(points[1], points[2], True),
        support.safe_sub(points[3], points[0], True),
        support.safe_sub(points[1], points[3], True),
        support.safe_sub(points[3], points[2], True),
        support.safe_sub(points[1], points[0], True)
    ]

    mat = get_scalar_matrix(_vecs)
    _p = get_lengths(_result, mat)
    assert(_p), """
        Invalid curve: cannot determine radius / tangent lengths.\nArc:\n{}
        """.format(str(_result))

    _result.update(_p)
    _p = get_delta(_result, mat)

    assert(_p), """
        Invalid curve: cannot determine central angle.\nArc:\n{}
        """.format(str(_result))

    _result.update(_p)
    _p = get_rotation(_result, _vecs)

    assert(_p), """
        Invalid curve: cannot determine curve direction.\nArc:\n{}
        """.format(str(_result))

    _result.update(_p)
    _p = get_bearings(_result, mat, _result.get('Delta'), _result.get('Direction'))

    assert(_p), """
            Invalid curve: cannot determine curve bearings.\nArc:\n{}
        """.format(str(_result))

    _result.update(_p)
    _p = get_missing_parameters(_result, _result, points)

    assert(_p), """
            Invalid curve: cannot calculate all parameters.\nArc:\n{}
        """.format(str(_result))

    _result.update(_p)
    _p = get_coordinates(_result, points)

    assert(_p), """
        Invalid curve: cannot calculate coordinates\nArc:\n{}
        """.format(str(_result))

    _result.update(_p)

    if as_dict:
        return _result.to_dict()

    return _result

def convert_units(arc, to_document=False):
    """
    Convert the units of the arc parameters to or from document units

    to_document = True - convert to document units
                  False - convert to system units (mm / radians)
    """

    angle_keys = ['Delta', 'BearingIn', 'BearingOut']

    _result = {}

    angle_fn = math.radians
    scale_factor = support.scale_factor()

    if to_document:
        angle_fn = math.degrees
        scale_factor = 1.0 / scale_factor

    for _k, _v in arc.items():

        _result[_k] = _v

        if _v is None:
            continue

        if _k in angle_keys:
            _result[_k] = angle_fn(_v)
            continue

        if _k != 'Direction':
            _result[_k] = _v * scale_factor

    return _result

def get_coord_on_arc(start, radius, direction, distance):
    """
    Get the coordinate at the specified distance on the arc with
    defined start, radius, and direction.
    """

    delta = distance / radius

    _offset = (
        math.sin(delta) * radius,
        (1 - math.cos(delta)) * radius,
        0.0
    )

    return TupleMath.add(start, _offset)

def get_ortho_vector(arc_dict, distance, side=''):
    """
    Given a distance from the start of a curve,
    and optional direction, return the orthogonal vector
    If no side is specified, directed vector to centerpoint is returned

    arc_dict - arc dictionary
    distance - distance along arc from start point
    side - any of 'l', 'lt', 'left', 'r', 'rt', 'right',
                regardless of case
    """

    direction = arc_dict.get('Direction')
    bearing = arc_dict.get('BearingIn')
    radius = arc_dict.get('Radius')
    start = arc_dict.get('Start')
    _side = side.lower()
    _x = 1.0

    if (direction < 0.0 and _side in ['r', 'rt', 'right']) or \
       (direction > 0.0 and _side in ['l', 'lt', 'left']):

        _x = -1.0

    delta = distance / radius
    coord = get_segments(bearing, [delta], direction, start, radius)[1]

    if not coord:
        return None, None

    ortho = TupleMath.subtract(arc_dict.get('Center'), coord)
    ortho = TupleMath.scale(TupleMath.unit(ortho), _x)

    return coord, ortho

def get_tangent_vector(arc_dict, distance):
    """
    Given an arc and a distance, return the tangent at the point along
    the curve from its start
    """

    side = 'r'
    multiplier = 1.0

    if arc_dict.get('Direction') < 0.0:
        side = 'l'
        multiplier = -1.0

    coord, ortho = get_ortho_vector(arc_dict, distance, side)

    # Rotate orthogonal vector 90 degrees to get tangent
    ortho = (-ortho[1], ortho[0], ortho[2])
    ortho = TupleMath.scale(ortho, multiplier)

    return coord, ortho

def get_segments(bearing, deltas, direction, start, radius, _dtype=tuple):
    """
    Calculate the coordinates of the curve segments

    bearing - beginning bearing
    deltas - list of angles to calculate
    direction - curve direction: -1.0 = ccw, 1.0 = cw
    start - starting coordinate
    radius - arc radius
    """

    _forward = (math.cos(bearing), math.sin(bearing), 0.0)
    _right = (_forward[1], -_forward[0], 0.0)

    _points = [_dtype(start)]
    _start = tuple(start)

    for delta in deltas:

        _dfw = TupleMath.scale(_forward, math.sin(delta))
        _drt = TupleMath.scale(_right, direction * (1.0 - math.cos(delta)))

        _vec = TupleMath.add(_start, TupleMath.scale(
            TupleMath.add(_dfw, _drt), radius))

        if _dtype is not tuple:
            _vec = _dtype(_vec)

        _points.append(_vec)

    return _points

def get_position_offset(arc, coord):
    """
    Find the station (distance along arc), point on arc, offset distance,
    and boundary status for the given coordinate
    
    Returns:
        station - distance along arc from start point
        point - coordinate of projection point on arc
        offset - perpendicular distance from arc (+ for outside, - for inside)
        bound - boundary status: -1 (before start), 0 (on arc), 1 (after end)
    """

    _center = arc.get('Center')
    _start = arc.get('Start')
    _end = arc.get('End')
    _radius = arc.get('Radius')
    _direction = arc.get('Direction')
    _delta = arc.get('Delta')
    
    # Check if coordinate is at start or end point
    if support.within_tolerance(TupleMath.length(TupleMath.subtract(coord, _start))):
        return 0.0, _start, 0.0, 0
    
    if support.within_tolerance(TupleMath.length(TupleMath.subtract(coord, _end))):
        _arc_length = arc.get('Length')
        return _arc_length, _end, 0.0, 0
    
    # Vector from center to coordinate
    _center_to_coord = TupleMath.subtract(coord, _center)
    
    # Vector from center to start
    _center_to_start = TupleMath.subtract(_start, _center)
    
    # Vector from center to end
    _center_to_end = TupleMath.subtract(_end, _center)
    
    # Calculate the angle of coordinate from center
    _coord_angle = math.atan2(_center_to_coord[1], _center_to_coord[0])
    _start_angle = math.atan2(_center_to_start[1], _center_to_start[0])
    _end_angle = math.atan2(_center_to_end[1], _center_to_end[0])
    
    # Calculate swept angle from start to coord
    _swept = _coord_angle - _start_angle
    
    # Normalize based on arc direction
    if _direction > 0:  # Clockwise
        while _swept > 0:
            _swept -= C.TWO_PI
        _swept = abs(_swept)
    else:  # Counter-clockwise
        while _swept < 0:
            _swept += C.TWO_PI
    
    # Calculate station along arc
    _station = _swept * _radius
    
    # Calculate actual distance from center to coordinate
    _dist_from_center = TupleMath.length(_center_to_coord)
    
    # Calculate radial offset (positive = outside arc, negative = inside arc)
    _offset = _dist_from_center - _radius
    
    # Project coordinate onto arc (point on arc at same angle)
    _unit_vec = TupleMath.unit(_center_to_coord)
    _point_on_arc = TupleMath.add(_center, TupleMath.scale(_unit_vec, _radius))
    
    # Check boundary conditions
    _arc_length = arc.get('Length')
    
    # Check if station is within arc bounds using tolerance
    if support.within_tolerance(_station, 0.0) or _station < 0:
        if _station < 0 and not support.within_tolerance(_station, 0.0):
            # Point is before arc start
            _dist_to_start = TupleMath.length(TupleMath.subtract(coord, _start))
            return 0.0, _start, _dist_to_start, -1
        else:
            # Very close to start, consider it on arc
            return 0.0, _point_on_arc, _offset, 0
    
    elif support.within_tolerance(_station, _arc_length) or _station > _arc_length:
        if _station > _arc_length and not support.within_tolerance(_station, _arc_length):
            # Point is after arc end
            _dist_to_end = TupleMath.length(TupleMath.subtract(coord, _end))
            return _arc_length, _end, _dist_to_end, 1
        else:
            # Very close to end, consider it on arc
            return _arc_length, _point_on_arc, _offset, 0
    
    else:
        # Point projection is within arc bounds
        return _station, _point_on_arc, _offset, 0

def get_points(
        arc, size=10.0, method='Segment', interval=None, _dtype=tuple):
    """
    Discretize an arc into the specified segments.
    Resulting list of coordinates omits provided starting point and
    concludes with end point

    arc         - A dictionary containing key elements:
        Direction   - non-zero.  <0 = ccw, >0 = cw
        Radius      - in document units (non-zero, positive)
        Delta       - in radians (non-zero, positive)
        BearingIn   - true north starting bearing in radians (0 to 2*pi)
        BearingOut  - true north ending bearing in radians (0 to 2*pi)

    size        - size of discrete elements (non-zero, positive)

    method      (Method of discretization)
        'Segment'   - subdivide into n equal segments (default)
        'Interval'  - subdivide into fixed length segments
        'Tolerance' - limit error between segment and curve

    interval    - Start and distance along arc to discretize
    _dtype      - data type for returned points (tuple or Vector)

    Points are returned referenced to start_coord
    """

    _arc = arc

    if isinstance(arc, dict):
        _arc = Arc(arc)

    angle = _arc.delta
    direction = _arc.direction
    bearing_in = _arc.bearing_in
    radius = _arc.radius
    start = _arc.start
    end = _arc.end

    if not radius:
        return [_arc.pi]

    if not interval:
        interval = [0.0, 0.0]

    _delta_angle = interval[0] / radius
    _start_angle = bearing_in + (_delta_angle * direction)

    # Get the start coordinate at the actual starting point on the curve
    if interval[0] > 0.0:

        start = get_segments(
            bearing_in, [_delta_angle], direction, start, radius
        )[1]

    # If the distance is specified, calculate the central angle from that
    # otherwise, the new central angle is the old central angle less the delta
    if interval[1] > 0.0:
        angle = interval[1] / radius
    else:
        angle = angle - _delta_angle

    # Define the incremental angle for segment calculations,
    # defaulting to 'Segment'
    _delta = angle / size

    _ratio = (size * support.scale_factor()) / radius

    if method == 'Interval':
        _delta = _ratio

    elif method == 'Tolerance':
        _delta = 2.0 * math.acos(1 - _ratio)

    # Pre-calculate the segment deltas,
    # increasing from zero to the central angle
    if _delta == 0.0:
        return None, None

    segment_deltas = [
        float(_i + 1) * _delta for _i in range(0, int(angle / _delta))
    ]

    _arc.points = get_segments(
        _start_angle, segment_deltas, direction, start, radius, _dtype
    )

    _arc.points.append(_dtype(end))

    return _arc.points
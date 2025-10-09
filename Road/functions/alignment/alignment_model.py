# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""
Class for managing 2D Horizontal Alignment data
"""

from FreeCAD import Vector
import Part

import math

from .. import support
from .geometry import arc, line, spiral
from ...utils.tuple_math import TupleMath

class AlignmentModel:
    """
    Alignment model for the alignment FeaturePython class
    """
    def __init__(self, meta, station, geometry):
        """
        Default Constructor
        """
        self.errors = []
        self.meta = meta
        self.station = station
        self.geometry = geometry

        if geometry: self.construct_geometry()

    def get_datum(self):
        """
        Return the alignment datum
        """

        return self.meta.get('Start')

    def get_pi_coords(self):
        """
        Return the coordinates of the alignment Points of Intersection(PIs)
        as a list of vectors
        """

        result = [Vector()]
        result += [
            _v.get('PI') for _v in self.geometry if _v.get('PI')]

        result.append(self.meta.get('End'))

        return result

    def construct_geometry(self):
        """
        Assign geometry to the alignment object
        """
        _geometry = []
        for _geo in self.geometry:
            if _geo.get('Type') == 'Line':
                _geo = line.get_parameters(_geo)

            elif _geo.get('Type') == 'Curve':
                _geo = arc.get_parameters(_geo)

            elif _geo.get('Type') == 'Spiral':
                _geo = spiral.get_parameters(_geo)

            else:
                self.errors.append('Undefined geometry: ' + str(_geo))
                continue

            _geometry.append(_geo)

        self.geometry = _geometry
        self.validate_datum()
        self.validate_stationing()

    def validate_datum(self):
        """
        Ensure the datum is valid, assuming 0+00 / (0,0,0)
        for station and coordinate where none is suplpied and it
        cannot be inferred fromt the starting geometry
        """
        _datum = self.meta
        _geo = self.geometry[0]

        if not _geo or not _datum:
            return

        _datum_truth = [not _datum.get('StartStation') is None,
                        not _datum.get('Start') is None]

        _geo_truth = [not _geo.get('StartStation') is None,
                      not _geo.get('Start') is None]

        #----------------------------
        #CASE 0
        #----------------------------
        #both defined?  nothing to do
        if all(_datum_truth):
            return

        #----------------------------
        #Parameter Initialization
        #----------------------------
        _geo_station = 0
        _geo_start = Vector()

        if _geo_truth[0]:
            _geo_station = _geo.get('StartStation')

        if _geo_truth[1]:
            _geo_start = _geo.get('Start')

        #---------------------
        #CASE 1
        #---------------------
        #no datum defined?  use initial geometry or zero defaults
        if not any(_datum_truth):

            _datum['StartStation'] = _geo_station
            _datum['Start'] = _geo_start
            return

        #--------------------
        #CASE 2
        #--------------------
        #station defined?
        #if the geometry has a station and coordinate,
        #project the start coordinate

        if _datum_truth[0]:

            _datum['Start'] = _geo_start

            #assume geometry start if no geometry station
            if not _geo_truth[0]:
                return

            #scale the distance to the system units
            delta = _geo_station - _datum['StartStation']

            #cutoff if error is below tolerance
            if not support.within_tolerance(delta):
                delta *= support.scale_factor()
            else:
                delta = 0.0

            #assume geometry start if station delta is zero
            if delta:

                #calculate the start based on station delta
                _datum['Start'] =\
                    TupleMath.subtract(_datum.get('Start'),
                    TupleMath.scale(
                        TupleMath.bearing_vector(_geo.get('BearingIn')),
                        delta)
                        #_geo.get('BearingIn')).multiply(delta)
                    )

            return

        #---------------------
        #CASE 3
        #---------------------
        #datum start coordinate is defined
        #if the geometry has station and coordinate,
        #project the start station
        _datum['StartStation'] = _geo_station

        #assume geometry station if no geometry start
        if _geo_truth[1]:

            #scale the length to the document units
            delta = TupleMath.length(
                TupleMath.subtract(_geo_start, _datum.get('Start'))
            ) / support.scale_factor()

            _datum['StartStation'] -= delta

    def validate_stationing(self):
        """
        Iterate the geometry, calculating the internal start station
        based on the actual station and storing it in an
        'InternalStation' parameter tuple for the start
        and end of the curve
        """

        prev_station = self.meta.get('StartStation')
        prev_coord = self.meta.get('Start')

        if (prev_coord is None) or (prev_station is None):
            return

        for _geo in self.geometry:

            if not _geo:
                continue

            _geo['InternalStation'] = None

            geo_station = _geo.get('StartStation')
            geo_coord = _geo.get('Start')

            #if no station is provided, try to infer it from the start
            #coordinate and the previous station
            if geo_station is None:

                geo_station = prev_station

                if not geo_coord:
                    geo_coord = prev_coord

                delta = TupleMath.length(
                    TupleMath.subtract(tuple(geo_coord), tuple(prev_coord)))

                if not support.within_tolerance(delta):
                    geo_station += delta / support.scale_factor()

                _geo['StartStation'] = geo_station

            prev_coord = _geo.get('End')
            prev_station = _geo.get('StartStation') \
                + _geo.get('Length')/support.scale_factor()

            int_sta = self.get_internal_station(geo_station)

            _geo['InternalStation'] = (int_sta, int_sta + _geo.get('Length'))

        last_curve_stations = self.geometry[-1].get('InternalStation')
        self.meta["EndStation"] = last_curve_stations[1] / 1000

    def get_internal_station(self, station):
        """
        Using the station equations, determine the internal station
        (position) along the alignment, scaled to the document units
        """
        start_sta = self.meta.get('StartStation')

        if not start_sta:
            start_sta = 0.0

        if not self.station:
            return station * support.scale_factor()

        eqs = self.station

        #default to distance from starting station
        position = 0.0

        for _eq in eqs[1:]:

            #if station falls within equation, quit
            if start_sta < station < _eq['Back']:
                break

            #increment the position by the equaion length and
            #set the starting station to the next equation
            position += _eq['Back'] - start_sta
            start_sta = _eq['Ahead']

        #add final distance to position
        position += station - start_sta

        if support.within_tolerance(position):
            position = 0.0

        return position * support.scale_factor()

    def get_alignment_station(self, internal_station=None, coordinate=None):
        """
        Return the alignment station given an internal station or coordinate
        Coordinate overrides internal station
        """

        if coordinate is not None:
            internal_station = self.get_station_offset(coordinate)[0]

        if internal_station is None:
            return None

        _start_sta = self.meta.get('StartStation')
        _dist = internal_station

        for _eq in self.station:

            #station equation adjustments should be limited to equations
            #on the same alignment
            if _eq['Description'] != _eq['Alignment']:
                continue

            #if the raw station exceeds the end of the first station
            #deduct the length of the first equation
            if _eq['Back'] >= _start_sta + _dist:
                break

            _dist -= _eq['Back'] - _start_sta
            _start_sta = _eq['Ahead']

        #start station represents beginning of enclosing equation
        #and raw station represents distance within equation to point
        return _start_sta + (_dist / support.scale_factor())

    def get_station_offset(self, coordinate):
        """
        Locate the provided coordinate along the alignment, returning
        the internal station or None if not within tolerance.
        """

        _matches = []
        _classes = {'Line': line, 'Curve': arc, 'Spiral': spiral}

        #iterate the geometry, creating a list of potential matches
        for _i, _v in enumerate(self.geometry):

            _class = _classes[_v.get('Type')]

            _pos, _dist, _b = _class.get_position_offset(_v, coordinate)

            #if position is before geometry, quit
            if _b < 0:
                break

            #if position is after geometry, skip to next
            if _b > 0:
                continue

            #save result
            _matches.append((_pos, _dist, _i))

        if not _matches:
            return None, None

        #get the distances
        _dists = [_v[1] for _v in _matches]

        #return the closest match
        return _matches[_dists.index(min(_dists))]

    def locate_curve(self, station):
        """
        Retrieve the curve at the specified station
        """

        int_station = self.get_internal_station(station)

        if int_station is None:
            return None

        prev_geo = None

        for _geo in self.geometry:

            if _geo.get('InternalStation')[0] > int_station:
                break

            prev_geo = _geo

        return prev_geo

    def get_orthogonal(self, station, side, verbose=False):
        """
        Return the orthogonal vector to a station along the alignment
        """

        curve = self.locate_curve(station)
        int_sta = self.get_internal_station(station)

        if verbose:
            print (f'\ncurve = {str(curve)}\nsta={str(int_sta)}')

        if (curve is None) or (int_sta is None):

            print('unable to locate station ', station, 'on curve ', curve)
            return None

        distance = int_sta - curve.get('InternalStation')[0]

        _fn = {
            'Line': line,
            'Curve': arc,
            'Spiral': spiral,
        }

        #return orthogonal for valid curve types
        if curve.get('Type') in _fn:

            return _fn[curve.get('Type')].get_ortho_vector(
                curve, distance, side)

        return None

    def get_stations(self, increment, terminal):
        last = None
        stations = []
        inc = {"Line": increment[0]*1000, "Curve": increment[1]*1000, "Spiral": increment[2]*1000}
        for geo in self.geometry:
            # Get starting and ending stations based on alignment
            geo_start = geo.get('StartStation')*1000
            length = geo.get('Length')
            geo_end = geo_start + length
            last = geo_end

            if terminal: stations.append(geo_start)
            incre = int(inc[geo.get('Type')])
            stations.extend(range(int(math.ceil(geo_start / incre) * incre), int(geo_end + 1), incre))

        # Add the end station
        if terminal: stations.append(last)

        return stations

    def get_tangent(self, station):
        """
        Return the tangent vector to a station along the alignment,
        directed in the direction of the curve
        """

        curve = self.locate_curve(station)
        int_sta = self.get_internal_station(station)

        if (curve is None) or (int_sta is None):
            return None

        distance = int_sta - curve.get('InternalStation')[0]

        _fn = {
            'Line': line,
            'Curve': arc,
            'Spiral': spiral,
        }

        if curve.get('Type') in _fn:
            return _fn[curve.get('Type')].get_tangent_vector(curve, distance)

        return None

    def discretize_geometry(self, interval=None, method='Segment', delta=10.0, types=False):
        """
        Discretizes the alignment geometry to a series of vector points
        interval - the starting internal station and length of curve
        method - method of discretization
        delta - discretization interval parameter
        """

        geometry = self.geometry

        points = []
        curves = []
        spirals = []
        lines = []
        last_curve = None

        #undefined = entire length
        if not interval:
            interval = [0.0, self.meta.get('Length')]

        #only one element = starting position
        if len(interval) == 1:
            interval.append(self.meta.get('Length'))

        #discretize each arc in the geometry list,
        #store each point set as a sublist in the main points list
        for curve in geometry:

            if not curve:
                continue

            _sta = curve.get('InternalStation')

            #skip if curve end precedes start of interval
            if _sta[1] < interval[0]:
                continue

            #skip if curve start exceeds end of interval
            if _sta[0] > interval[1]:
                continue

            _start = _sta[0]

            #if curve starts before interval, use start of interval
            if _sta[0] < interval[0]:
                _start = interval[0]

            _end = _sta[1]

            #if curve ends past the interval, stop at end of interval
            if _sta[1] > interval[1]:
                _end = interval[1]

            #calculate start position on arc and length to discretize
            _arc_int = [_start - _sta[0], _end - _start]

            #just in case, skip for zero or negative lengths
            if _arc_int[1] <= 0.0:
                continue

            if curve.get('Type') == 'Curve':

                _pts = arc.get_points(
                    curve, size=delta, method=method, interval=_arc_int)

                if _pts:
                    points.append(_pts)
                    curves.append([(i.x, i.y, i.z) for i in _pts])

            elif curve.get('Type') == 'Spiral':

                _pts = spiral.get_points(curve, size=delta, method=method)

                if _pts:
                    points.append(_pts)
                    spirals.append([(i.x, i.y, i.z) for i in _pts])

            else:

                _start_coord = line.get_coordinate(
                    curve.get('Start'), curve.get('BearingIn'), _arc_int[0])

                _end_coord = line.get_coordinate(
                    _start_coord, curve.get('BearingIn'), _arc_int[1])

                points.append([_start_coord, _end_coord])
                lines.append([_start_coord, _end_coord])

            last_curve = curve

        #store the last point of the first geometry for the next iteration
        _prev = points[0][-1]
        result = points[0]

        if not (_prev and result):
            return None

        #iterate the point sets, adding them to the result set
        #and eliminating any duplicate points
        for item in points[1:]:

            _v = item

            #duplicate points are within a hundredth of a foot of each other
            if TupleMath.length(
                TupleMath.subtract(tuple(_prev), tuple(item[0]))) < 0.01:

                _v = item[1:]

            result.extend(_v)
            _prev = item[-1]

        #add a line segment for the last tangent if it exists
        last_tangent = abs(
            self.meta.get('Length') \
                - last_curve.get('InternalStation')[1]
        )

        if not support.within_tolerance(last_tangent):
            _vec = TupleMath.bearing_vector(
                last_curve.get('BearingOut') * last_tangent)

#            _vec = support.vector_from_angle(last_curve.get('BearingOut'))\
#                .multiply(last_tangent)

            last_point = tuple(result[-1])

            result.append(TupleMath.add(last_point, _vec))

        #set the end point
        if not self.meta.get('End'):
            self.meta['End'] = result[-1]

        if types: return curves, spirals, lines, result
        return result
    
    def get_shape(self):
        """
        Get the shape of the alignment geometry
        """
        shapes = []
        for curve in self.geometry:
            if not curve: continue

            if curve.get('Type') == 'Curve':
                center = Vector(curve.get('Center'))
                radius = curve.get('Radius')
                start = Vector(curve.get('Start'))
                end = Vector(curve.get('End'))

                chord_middle = (start + end) / 2
                middle = chord_middle.sub(center).normalize().multiply(radius).add(center)
                shapes.append(Part.Arc(start, middle, end).toShape())

            elif curve.get('Type') == 'Spiral':

                _pts = spiral.get_points(curve, size=1, method="Interval")
                if not _pts: continue
                try:
                    bspline = Part.BSplineCurve()
                    bspline.interpolate(_pts)
                    shapes.append(bspline.toShape())
                
                except: 
                    continue
                    shp = Part.makePolygon(_pts)
                    shp.Placement.move(Vector(_pts[0]).negative())

            else:
                start = Vector(curve.get('Start'))
                end = Vector(curve.get('End'))
                shapes.append(Part.LineSegment(start, end).toShape())

        return Part.Compound(shapes)
        return Part.Wire(shapes)

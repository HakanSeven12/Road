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

"""Provides functions to object and viewprovider classes of Alignment."""

import FreeCAD
import Part

import math

from ..geoutils.tangent import makeTangent
from ..geoutils.curve import makeCurve
from ..geoutils.spiral import makeSpiral

import math
import FreeCAD


def angle_direction(v1, v2=None, v3=None):
    """
    Calculate the angle difference and turn direction between three vectors.

    v1: Start vector
    v2: Middle vector (if not provided, v1 is the direction vector)
    v3: Optional end vector (if not provided, assumes a default vector of X axis)

    Returns: Tuple (angle, direction)
    - angle: The angle between the vectors
    - direction: 1 for counter-clockwise, -1 for clockwise
    """
    # If v3 is not provided, assume it to X axis
    x_axis = FreeCAD.Vector(1, 0, 0)
    if v3 is None:
        v3 = x_axis

    # Calculate direction vectors
    direction_in = v2.sub(v1) if v2 else v1
    direction_out = v3.sub(v2) if v2 and v3 != x_axis else v3

    # Calculate the angle and cross product
    angle = direction_in.getAngle(direction_out)
    cross = direction_in.cross(direction_out)

    # Determine the direction of rotation
    direction = 1 if cross.z > 0 else -1

    # Adjust the angle for default vector case
    if v3 == x_axis:
        angle = 2 * math.pi - angle if cross.z > 0 else angle

    return angle, direction

def spiral_bspline(start, end, radius, length, direction, delta, type = "in"):
    angle, _ = angle_direction(start, end)
    spiral = makeSpiral(length, radius, direction, delta)
    placement = start.sub(end).normalize().multiply(abs(spiral.tangent)).add(end)
    return spiral.toShape(placement, angle, type)

def get_geometry(alignment_data):
    if not alignment_data:
        return Part.Shape(), []
 
    # Extract points and parameters from dictionary
    PI_points = []
    for key in alignment_data:
        PI_points.append({
            'point': FreeCAD.Vector(float(alignment_data[key]['X']), float(alignment_data[key]['Y']), 0).multiply(1000),
            'spiral_in_length': float(alignment_data[key].get('Spiral Length In', 0)) * 1000,
            'spiral_out_length': float(alignment_data[key].get('Spiral Length Out', 0)) * 1000,
            'radius': float(alignment_data[key].get('Radius', 0)) * 1000,
            'curve_type': alignment_data[key].get('Curve Type', 'None')})
    
    # Get PI points
    all_points = [pi['point'] for pi in PI_points]
    
    # Variable to store previous ST point
    shapes = []
    previous = all_points[0]

    for i in range(1, len(all_points)-1):
        curve_type = PI_points[i]['curve_type']
        if curve_type == 'None':
            # If there is no curve, create a line between points
            tangent = makeTangent(previous, all_points[i])
            shapes.append(tangent)
            previous = all_points[i]

        elif curve_type == 'Curve':
            # If it's a curve, create a simple circular arc
            start_point = all_points[i-1]
            middle_point = all_points[i]
            end_point = all_points[i+1]

            radius = PI_points[i]['radius']

            # Rotation and direction of the curve
            delta, direction = angle_direction(start_point, middle_point, end_point)

            length = radius * math.tan(delta / 2)
            start = start_point.sub(middle_point).normalize().multiply(abs(length)).add(middle_point)
            end = end_point.sub(middle_point).normalize().multiply(abs(length)).add(middle_point)
            
            tangent = makeTangent(previous, start)
            curve = makeCurve(start, end, radius, direction)
            shapes.extend([tangent, curve])

            # Save the end point for the next group
            previous = end

        elif curve_type == 'Spiral-Curve-Spiral':
            start_point = all_points[i-1]
            middle_point = all_points[i]
            end_point = all_points[i+1]

            # Get spiral parameters for the current PI point
            radius = PI_points[i]['radius']
            length_in = PI_points[i]['spiral_in_length']
            length_out = PI_points[i]['spiral_out_length']

            # Rotation and direction of the curve
            delta, direction = angle_direction(start_point, middle_point, end_point)

            spiral_in = spiral_bspline(start_point, middle_point, radius, length_in, direction, delta)
            spiral_out = spiral_bspline(end_point, middle_point, radius, length_out, -direction, delta, type = "out")

            tangent = makeTangent(previous, spiral_in.Curve.StartPoint)

            SC = spiral_in.Curve.EndPoint
            CS = spiral_out.Curve.StartPoint
            
            curve = makeCurve(SC, CS, radius, direction)

            shapes.extend([tangent, spiral_in, curve, spiral_out])

            # Save the end point for the next group
            previous = spiral_out.Curve.EndPoint

    # For the last group, connect to the last PI
    end_tangent = makeTangent(previous, all_points[-1])
    shapes.append(end_tangent)

    shape = Part.makeCompound(shapes)
    return all_points, shape

def transformation(shape, stations, last=False):
    points = []
    rotations = []
    total_length = 0

    for i, sub in enumerate(shape.SubShapes):
        sta_list = [sta for sta in stations if total_length <= sta <= total_length + sub.Length]
        if i == len(shape.SubShapes) - 1 and last:
            sta_list.append(total_length + sub.Length)

        for station in sta_list:
            length = station - total_length
            parameter = sub.getParameterByLength(length)

            point = sub.valueAt(parameter)
            points.append(point)

            tangent = sub.tangentAt(parameter)
            normal = FreeCAD.Vector(-tangent.y, tangent.x, tangent.z)

            angle = FreeCAD.Vector(1, 0, 0).getAngle(normal)
            angle = 2*math.pi - angle if normal.y < 0 else angle
            rotations.append(angle)

        total_length += sub.Length
    return points, rotations
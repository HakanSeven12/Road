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

"""Provides functions to object and viewprovider classes of Profile."""

import FreeCAD
import MeshPart, Part

import math

from ..geoutils.tangent import makeTangent
from ..geoutils.curve import makeCurve

def flatten_profile(points, horizon):
    flatten =[]
    flatten.append(FreeCAD.Vector(0, points[0].z - horizon, 0))
    for i in range(len(points)-1):
        if points[i] == points[i+1]: continue
        vector = points[i+1].sub(points[i])
        angle = vector.getAngle(FreeCAD.Vector(0, 0, 1))
        length = vector.Length
        rotation = FreeCAD.Rotation(FreeCAD.Vector(0,0,1), Radian=-angle)
        projected = rotation.multVec(FreeCAD.Vector(0, length, 0))

        flatten.append(flatten[-1].add(projected))

    return flatten

def from_mesh(wire, mesh):
    num = 1
    model = {}
    prev = None
    total_length = 0
    for edge in wire.Edges:
        parameters = [edge.getParameterByLength(0)]
        parameters.extend(MeshPart.findSectionParameters(
            edge, mesh, FreeCAD.Vector(0, 0, 1)))
        parameters.append(edge.getParameterByLength(edge.Length))

        for param in parameters:
            point = edge.valueAt(param)
            if point == prev: continue
            projection = MeshPart.projectPointsOnMesh(
                [point], mesh, FreeCAD.Vector(0, 0, 1))

            model[num] = {"Station": total_length + param, "Elevation": projection[0].z if projection else None}
            prev = point
            num += 1

        total_length += edge.Length
    return model

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

def get_geometry(model):
    if not model:
        return [], Part.makeCompound([])
 
    # Extract points and parameters from dictionary
    whole = []
    current = []
    for key, value in model.items():
        station = value['Station']
        elevation = value['Elevation']

        if elevation is None:
            if current:
                whole.append(current)
                current = []

        else:
            current.append({
                "point": FreeCAD.Vector(float(station), float(elevation)),
                "radius": float(value.get("Radius", 0)) * 1000,
                "curve_type": value.get("Curve Type", "None")})

    if current: whole.append(current)

    # Create Part Wire for every seperated segment in the profile
    compound = []
    for segment in whole:
        all_points = [pvi["point"] for pvi in segment]

        edges = []
        previous = all_points[0]
        for i in range(1, len(all_points)-1):
            curve_type = segment[i]["curve_type"]

            if curve_type == "None":
                tangent = makeTangent(previous, all_points[i])
                edges.append(tangent)
                previous = tangent.lastVertex().Point

            elif curve_type == "Curve":
                start_point = all_points[i-1]
                middle_point = all_points[i]
                end_point = all_points[i+1]

                radius = segment[i]["radius"]
                delta, direction = angle_direction(start_point, middle_point, end_point)

                length = radius * math.tan(delta / 2)
                start = start_point.sub(middle_point).normalize().multiply(abs(length)).add(middle_point)
                end = end_point.sub(middle_point).normalize().multiply(abs(length)).add(middle_point)
                
                tangent = makeTangent(previous, start)
                curve = makeCurve(start, end, radius, direction)
                edges.extend([tangent, curve])

                previous = curve.lastVertex().Point

            elif curve_type == "Parabola":
                start_point = all_points[i-1]
                middle_point = all_points[i]
                end_point = all_points[i+1]

                radius = segment[i]["radius"]
                delta, direction = angle_direction(start_point, middle_point, end_point)

                #TODO
                print("Parabola not defined")

        # Connect to the last PVI
        if previous != all_points[-1]:
            end_tangent = makeTangent(previous, all_points[-1])
            edges.append(end_tangent)

        sort = Part.sortEdges(edges)
        if not sort: continue
        wire = Part.Wire(sort[0])
        compound.append(wire)

    return all_points, Part.makeCompound(compound)

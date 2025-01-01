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

def from_mesh(shape, mesh, horizon):
    points = []
    for shp in shape.SubShapes:
        for edge in shp.Edges:
            parameters = [edge.getParameterByLength(0)]
            parameters.extend(MeshPart.findSectionParameters(
                edge, mesh, FreeCAD.Vector(0, 0, 1)))
            parameters.append(edge.getParameterByLength(edge.Length))

            points.extend([edge.valueAt(param) for param in parameters])

    projection = MeshPart.projectPointsOnMesh(
        points, mesh, FreeCAD.Vector(0, 0, 1))

    vertexes =  flatten_profile(projection, horizon)
    return Part.makePolygon(vertexes)
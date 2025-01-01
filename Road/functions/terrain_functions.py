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

"""Provides functions to object and viewprovider classes of Terrain."""

import FreeCAD
import Part

import numpy, math, colorsys


def test_triangulation(tri, lmax, amax):
    """Test triangulation for max length and max angle."""
    index = []
    for i in tri.simplices:
        points = [tri.points[i[j]] for j in range(3)]
        p1, p2, p3 = [FreeCAD.Vector(point[0], point[1], 0) for point in points]

        #Test triangle
        if max_length(lmax, p1, p2, p3)\
            and max_angle(amax,  p1, p2, p3):
            index.extend([i[j] for j in range(3)])
    return index

def max_length(lmax, p1, p2, p3):
    """Calculation of the 2D length between triangle edges"""
    for i, j in [(p1, p2), (p2, p3), (p3, p1)]:
        if i.sub(j).Length > lmax:
            return False
    return True

def max_angle(amax, p1, p2, p3):
    """Calculation of the 2D angle between triangle edges"""
    for j, k, l in [(p1, p2, p3), (p2, p3, p1), (p3, p1, p2)]:
        angle = math.degrees(j.sub(k).getAngle(l.sub(k)))
        if angle > amax:
            return False
    return True

def get_contours(mesh, major, minor):
    """Create triangulation contour lines"""
    zmax, zmin = mesh.BoundBox.ZMax, mesh.BoundBox.ZMin
    minor_contours, major_contours = [], []
    delta = minor
    while delta < zmax:
        if minor == 0: break
        cross_sections = mesh.crossSections([((0, 0, delta), (0, 0, 1))], 0.000001)
        for point_list in cross_sections[0]:
            if len(point_list) > 3:
                wire = Part.makePolygon(point_list)
                if delta % major == 0:
                    major_contours.append(wire)
                else:
                    minor_contours.append(wire)
        delta += minor
    return Part.makeCompound(
        [Part.makeCompound(major_contours), 
        Part.makeCompound(minor_contours)])

def get_boundary(mesh):
    """Find boundary of triangulation"""
    edges = []
    facets = mesh.Facets
    for facet in facets:
        for i in range(3):
            if facet.NeighbourIndices[i] != -1: continue
            line = Part.makeLine(
                facet.Points[i], 
                facet.Points[(i + 1) % 3])
            edges.append(line)

    wires = []
    for opening in Part.sortEdges(edges):
        wires.append(Part.Wire(opening))
    return Part.makeCompound(wires)

def wire_view(shape):
    points = []
    vertices = []
    for i in shape.Wires:
        vectors = []
        for vertex in i.OrderedVertexes:
            vectors.append(vertex.Point)
        if i.isClosed():
            vectors.append(i.OrderedVertexes[0].Point)
        points.extend(vectors)
        vertices.append(len(vectors))
    return points, vertices

def elevation_analysis(mesh, ranges):
    max = mesh.BoundBox.ZMax
    min = mesh.BoundBox.ZMin
    colorlist = []
    for facet in mesh.Facets:
        z = facet.Points[0][2] + facet.Points[1][2] + facet.Points[2][2]
        hue = 1
        elevations = numpy.arange(min, max, (max-min)/ranges)
        for i in elevations:
            if z/3 < i: 
                hue = i/(max-min)
                break
        colorlist.append(colorsys.hls_to_rgb(hue, 0.5, 0.5))
    return colorlist

def slope_analysis(mesh, ranges):
    colorlist = []
    for facet in mesh.Facets:
        normal = facet.Normal
        angle = math.degrees(normal.getAngle(FreeCAD.Vector(0, 0, 1))*2)
        hue = 1
        slopes = numpy.arange(0.0, 90.0, 90.0/ranges)
        for i in slopes:
            if angle < i: 
                hue = i/90.0
                break
        colorlist.append(colorsys.hls_to_rgb(hue, 0.5, 0.5))
    return colorlist

def direction_analysis(mesh, ranges):
    colorlist = []
    for facet in mesh.Facets:
        normal = copy.deepcopy(facet.Normal)
        normal.z = 0
        anglex = math.degrees(normal.getAngle(FreeCAD.Vector(1, 0, 0)))
        angley = math.degrees(normal.getAngle(FreeCAD.Vector(0, 1, 0)))
        if angley >= 90:
            anglex = 360.0 - anglex
        hue = 0.0
        directions = numpy.arange(0.0, 360.0, 360.0/ranges)
        for i in directions:
            if anglex < i + directions[1]/2: 
                hue = i/360.0
                break
        colorlist.append(colorsys.hls_to_rgb(hue, 0.5, 0.5))
    return colorlist
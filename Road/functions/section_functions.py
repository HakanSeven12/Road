# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to object and viewprovider classes of Section."""

import FreeCAD
import Part, MeshPart
import copy, math


class SectionFunctions:
    """
    This class is contain Section object functions.
    """
    def __init__(self):
        pass

    @staticmethod
    def section_converter(section_3d, origin):
        section_2d = []
        section_2d.append(FreeCAD.Vector(0, 0, 0))

        prev_vector = origin
        for i in section_3d:
            reduced_vector = copy.deepcopy(i)
            reduced_vector.z = prev_vector.z

            vector = prev_vector.sub(i)
            x_vector = prev_vector.sub(reduced_vector)
            length = vector.Length
            angle = x_vector.getAngle(vector)

            dx = length * math.cos(angle)
            dy = length * math.sin(angle)

            if x_vector.z < vector.z: dy = -dy
            vector_2d = section_2d[-1].add(FreeCAD.Vector(dx, dy, 0))
            section_2d.append(vector_2d)
            prev_vector = i

        section_2d.pop(0)
        return section_2d

    def minimum_elevations(self, gl, surface):
        minel = []
        mesh = surface.Mesh.copy()
        for wire in gl.Shape.Wires:

            points = []
            for edge in wire.Edges:
                cs = mesh.crossSections(
                    [(edge.Vertexes[0].Point, edge.Vertexes[-1].Point)], 0.000001)

                minz = math.inf
                for l in cs[0]:
                    for i in l:
                        if  i.z < minz:
                            minz = i.z

            minel.append(minz)

        return minel

    def draw_2d_sections(self, position, gl, surface, geometry, gaps, horizons):
        counter = 0
        buffer = 50000
        pos = position

        multi_views_nor = math.ceil(len(gl.Shape.Wires)**0.5)

        section_list = []
        for i, wire in enumerate(gl.Shape.Wires):

            points = []
            origin = wire.Vertexes[0].Point
            for edge in wire.Edges:
                params = MeshPart.findSectionParameters(
                    edge, surface.Mesh, FreeCAD.Vector(0, 0, 1))
                params.insert(0, edge.FirstParameter+1)
                params.append(edge.LastParameter-1)

                values = [edge.valueAt(glp) for glp in params]
                points.extend(values)

            section_3d = MeshPart.projectPointsOnMesh(
                points, surface.Mesh, FreeCAD.Vector(0, 0, 1))

            section_2d = self.section_converter(section_3d, origin)
            if not section_2d:
                section_2d = [FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,1,0)]

            draw_sec = []
            for idx in range(0, len(section_2d)-1):
                if section_2d[idx] == section_2d[idx+1]: continue
                draw_sec.append(section_2d[idx].add(position))

            if len(draw_sec) > 2:
                sec = Part.makePolygon(draw_sec)
            else:
                sec = Part.makePolygon([position, position.add(FreeCAD.Vector(0, 1, 0))])

            if horizons:
                reduce_vector = FreeCAD.Vector(0, horizons[i]-1000, 0)
                sec.Placement.move(reduce_vector.negative())

            section_list.append(sec)

            if counter == multi_views_nor:
                shifting = position.x - pos.x + gaps[1]
                reposition = FreeCAD.Vector(geometry[1] + shifting, 0, 0)
                position = pos.add(reposition)
                counter = 0

            else:
                reposition = FreeCAD.Vector(0, -(geometry[0] + gaps[0]), 0)
                position = position.add(reposition)
                counter += 1

        section_draws = Part.makeCompound(section_list)
        return section_draws

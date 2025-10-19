# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Section objects."""

import FreeCAD, Part, MeshPart
from ..utils.get_group import georigin


class Section:
    """This class is about Section object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = 'Road::Section'

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            'App::PropertyLinkList', "Terrains", "Base",
            "Projection terrains").Terrains = []

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Object shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyFloat", "Height", "Geometry",
            "Height of section view").Height = 50

        obj.addProperty(
            "App::PropertyFloat", "Width", "Geometry",
            "Width of section view").Width = 100

        obj.addProperty(
            "App::PropertyFloat", "Vertical", "Distances",
            "Vertical distance between section frame placements").Vertical = 200

        obj.addProperty(
            "App::PropertyFloat", "Horizontal", "Distances",
            "Horizontal distance between section frame placements").Horizontal = 200

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""

        sections = obj.getParentGroup()
        region = sections.getParentGroup()
        regions = region.getParentGroup()
        alignment = regions.getParentGroup()

        for terrain in obj.Terrains:
            shape = region.Shape.copy()
            shape.Placement.move(terrain.Placement.Base.negative())
            for wire in shape.Wires:
                points_2d = []
                for edge in wire.Edges:
                    params = MeshPart.findSectionParameters(
                        edge, terrain.Mesh, FreeCAD.Vector(0, 0, 1))
                    params.insert(0, edge.FirstParameter+1)
                    params.append(edge.LastParameter-1)

                    values = [edge.valueAt(glp) for glp in params]
                    points_2d.extend(values)

                points_3d = MeshPart.projectPointsOnMesh(
                    points_2d, terrain.Mesh, FreeCAD.Vector(0, 0, 1))
                
                verts = []
                for point in points_3d:
                    verts.append(Part.Vertex(point))
                    point = point.add(terrain.Placement.Base)
                    sta = alignment.Proxy.model.get_alignment_station(coordinate=[*point])
                
                Part.show(Part.makeCompound(verts))

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        pass
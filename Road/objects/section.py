# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Section objects."""

import FreeCAD, Part, MeshPart


class Section:
    """This class is about Section object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = 'Road::Section'

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "App::PropertyPythonObject", "Stations", "Base",
            "List of stations").Stations = {}
        
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
        if not hasattr(alignment.Proxy, "model"): return

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
                
                for point in points_3d:
                    point = point.add(terrain.Placement.Base)
                    station, position, offset, index = alignment.Proxy.model.get_station_offset([*point])
                    obj.Stations[station] = {'Offset': offset, 'Elevation': point.z}

        print(obj.Stations)
                

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        pass
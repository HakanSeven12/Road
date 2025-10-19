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
            "App::PropertyPythonObject", "Model", "Base",
            "List of stations").Model = {}
        
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

        for idx, sta in enumerate(region.Stations):
            obj.Model[sta] = {}
            for terrain in obj.Terrains:
                shape = region.Shape.copy()
                shape.Placement.move(terrain.Placement.Base.negative())

                flat_points = []
                for edge in shape.Wires[idx].Edges:
                    params = MeshPart.findSectionParameters(
                        edge, terrain.Mesh, FreeCAD.Vector(0, 0, 1))
                    params.insert(0, edge.FirstParameter+1)
                    params.append(edge.LastParameter-1)

                    values = [edge.valueAt(glp) for glp in params]
                    flat_points.extend(values)

                projected_points = MeshPart.projectPointsOnMesh(
                    flat_points, terrain.Mesh, FreeCAD.Vector(0, 0, 1))
                
                offset_elevation = []
                for point in projected_points:
                    point = point.add(terrain.Placement.Base)
                    station, position, offset, index = alignment.Proxy.model.get_station_offset([*point])
                    offset_elevation.extend([offset, point.z])
                obj.Model[sta][terrain.Label] = offset_elevation

        from pprint import pprint
        pprint(obj.Model, indent=2, width=40)
        print(obj.Model.keys())
                

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        pass
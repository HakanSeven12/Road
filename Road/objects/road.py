# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Road objects."""

import FreeCAD
import Part
import math


class Road:
    """This class is about Road object data features."""

    def __init__(self, obj):
        """Set data properties."""
        self.Type = "Road::Road"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Object shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyLink", "Alignment", "Model",
            "Base line Alignment").Alignment = None

        obj.addProperty(
            "App::PropertyLink", "Profile", "Model",
            "Elevation profile").Profile = None

        obj.addProperty(
            "App::PropertyLink", "Structure", "Model",
            "Road structure").Structure = None

        obj.Proxy = self
            
    def execute(self, obj):
        """Do something when doing a recomputation."""
        com_list = []
        for component in obj.Structure.Group:
            for part in component.Group:
                if part.Proxy.Type == "Road::ComponentPoint": continue
                part_copy = part.Shape.copy()
                part_copy.Placement.move(obj.Structure.Placement.Base.negative())
                com_list.append(part_copy)

        sec_list = []
        base_shp = Part.makeCompound(com_list)
        stations = obj.Alignment.Model.generate_stations()
        pos = obj.Profile.Placement.Base
        dy=FreeCAD.Vector(0, obj.Profile.Shape.BoundBox.YLength)

        for station, transform in stations.items():
            length = station
            point = transform["Location"]
            angle = transform["Rotation"]

            start = pos.add(FreeCAD.Vector(length,0))
            end = start.add(dy)
            line_edge = Part.LineSegment(start, end)
            line_shape = line_edge.toShape()

            result = obj.Profile.Shape.distToShape(line_shape.SubShapes[0])
            elevation = result[1][0][0].y - start.y + 3000

            global_matrix = FreeCAD.Matrix()
            global_matrix.rotateX(math.pi/2)
            global_matrix.rotateZ(angle)

            new_placement = FreeCAD.Placement(global_matrix)
            new_placement.Base = point.add(FreeCAD.Vector(0, 0, elevation))

            section = base_shp.copy()
            section.Placement = new_placement
            sec_list.append(section)
        
        shp_list = []
        for i in range(len(base_shp.Edges)):
            l = [sec.Edges[i] for sec in sec_list]
            shp = Part.makeLoft(l)
            shp_list.append(shp)
        
        obj.Shape = Part.makeCompound(shp_list)

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        if prop == "Alignment":
            alignment = obj.getPropertyByName(prop)
            obj.Placement = alignment.Placement if alignment else FreeCAD.Placement()
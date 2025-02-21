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

"""Provides the object code for Road objects."""

import FreeCAD

import Part

import math

from ..functions.alignment import transformation


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
        stations = transformation(obj.Alignment, 10000)
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
            print(result)
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
        
        Part.show(Part.makeCompound(sec_list))
        obj.Shape = Part.makeCompound(shp_list)
        Part.show(obj.Shape)

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        pass
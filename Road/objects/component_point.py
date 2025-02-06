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

"""Provides the object code for Component Point objects."""
import FreeCAD
import Part

import math


class ComponentPoint:
    """This class is about Component Point Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::ComponentPoint"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Vertex(FreeCAD.Vector())

        obj.addProperty(
            "App::PropertyEnumeration", "Type", "Geometry",
            "Type of transformation that will be applied to the point").Type = [
                "Delta X and Delta Y",
                "Delta X and Angle",
                "Delta Y and Angle",
                "Delta X and Slope",
                "Delta Y and Slope",
                "Delta X on Terrain",
                "Slope to Terrain",
                "Distance and Angle"]

        obj.addProperty(
            "App::PropertyLink", "Start", "Geometry",
            "Target Terrain.")

        obj.addProperty(
            "App::PropertyBool", "Reverse", "Geometry",
            "Reverse vector direction.")

        obj.addProperty(
            "App::PropertyFloat", "DeltaX", "Geometry",
            "Displacement along the X axis.").DeltaX = 0

        obj.addProperty(
            "App::PropertyFloat", "DeltaY", "Geometry",
            "Displacement along the Y axis.").DeltaY = 0

        obj.addProperty(
            "App::PropertyAngle", "Angle", "Geometry",
            "The angle with the X axis.").Angle = 0

        obj.addProperty(
            "App::PropertyPercent", "Slope", "Geometry",
            "The slope with the X axis.").Slope = 0

        obj.addProperty(
            "App::PropertyLink", "Terrain", "Geometry",
            "Target Terrain.")

        obj.addProperty(
            "App::PropertyLink", "Alignment", "Geometry",
            "Target Alignment.")

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        component = obj.getParentGroup()
        structure = component.getParentGroup()
        origin = structure.Placement.Base

        shp = Part.Vertex(FreeCAD.Vector())
        shp.Placement.move(origin.add(obj.Placement.Base))
        obj.Shape = shp

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        if prop == "Type":
            type = obj.getPropertyByName(prop)
            if type == "Delta X and Delta Y":
                displacement = FreeCAD.Vector(obj.DeltaX, obj.DeltaY)

            elif type == "Delta X and Angle":
                dy =obj.DeltaX * math.tan(math.radians(obj.Angle))
                displacement = FreeCAD.Vector(obj.DeltaX, dy)

            elif type == "Delta Y and Angle":
                dx = obj.DeltaY / math.tan(math.radians(obj.Angle))
                displacement = FreeCAD.Vector(dx, obj.DeltaY)

            elif type == "Delta X and Slope":
                dy = obj.DeltaX * obj.Slope
                displacement = FreeCAD.Vector(obj.DeltaX, dy)

            elif type == "Delta Y and Slope":
                dx = obj.DeltaY / obj.Slope
                displacement = FreeCAD.Vector(dx, obj.DeltaY)

            elif type == "Delta X on Terrain":pass
            elif type == "Slope to Terrain":pass

            elif type == "Distance and Angle":
                rad = math.radians(obj.Angle)
                dx = obj.Distance * math.cos(rad)
                dy = obj.Distance * math.sin(rad)
                displacement = FreeCAD.Vector(dx, dy)

            if obj.Reverse: displacement = displacement.negative()

            placement = FreeCAD.Placement()
            placement.move(displacement)
            obj.Placement = placement

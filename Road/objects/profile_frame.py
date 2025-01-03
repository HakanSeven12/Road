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

"""Provides the object code for Profile Frame objects."""

import FreeCAD
import Part


class ProfileFrame:
    """This class is about Profile Frame Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::ProfileFrame"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "App::PropertyFloat", "Horizon", "Base",
            "Minimum elevation").Horizon = 0

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyFloat", "Length", "Geometry",
            "Offset length").Length = 1000

        obj.addProperty(
            "App::PropertyFloat", "Height", "Geometry",
            "Offset length").Height = 1000

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        profiles = obj.getParentGroup()
        alignment = profiles.getParentGroup()

        length = alignment.Length.Value
        obj.Length = 1000 if length == 0 else length
        l = obj.Length
        h = obj.Height

        p1 = obj.Placement.Base
        p2 = FreeCAD.Vector(p1.x+l,p1.y,p1.z)
        p3 = FreeCAD.Vector(p1.x+l,p1.y+h,p1.z)
        p4 = FreeCAD.Vector(p1.x,p1.y+h,p1.z)

        obj.Shape = Part.makePolygon([p1,p2,p3,p4,p1])

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        if prop == "Group":
            group = obj.getPropertyByName(prop)
            if group:
                z_values = []
                for profile in group:
                    bb =profile.Terrain.Mesh.BoundBox
                    z_values.extend([bb.ZMin, bb.ZMax])

                height = max(z_values) - min(z_values)
                obj.Height = 1000 if height == 0 else height
                obj.Horizon = min(z_values)
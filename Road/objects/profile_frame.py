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
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyFloat", "Horizon", "Base",
            "Minimum elevation").Horizon = 0

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

        z_values = []
        for profile in obj.Group:
            elevations = [item['Elevation'] for item in profile.Model.values()]
            z_values.extend([float(el) for el in elevations if el is not None])

        obj.Height = max(z_values) - min(z_values) if z_values else 1000
        obj.Horizon = min(z_values) if z_values else 0

        length = alignment.Length.Value
        obj.Length = length if length else 1000

        p1 = FreeCAD.Vector()
        p2 = FreeCAD.Vector(obj.Length, 0)
        p3 = FreeCAD.Vector(obj.Length, obj.Height)
        p4 = FreeCAD.Vector(0, obj.Height)

        shp = Part.makePolygon([p1,p2,p3,p4,p1])
        shp.Placement = obj.Placement
        obj.Shape = shp

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        pass
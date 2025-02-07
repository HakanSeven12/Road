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

"""Provides the object code for Component Line objects."""
import FreeCAD
import Part


class ComponentLine:
    """This class is about Component Line Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::ComponentLine"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyLink", "Start", "Geometry",
            "Start point of line.")

        obj.addProperty(
            "App::PropertyLink", "End", "Geometry",
            "End point of line.")

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        if obj.Start and obj.End:
            placement = FreeCAD.Placement()
            placement.move(obj.Start.Placement.Base)
            obj.Placement = placement

            start = obj.Placement.Base
            end = obj.End.Placement.Base
            obj.Shape = Part.makeLine(start, end)
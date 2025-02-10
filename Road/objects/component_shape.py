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

"""Provides the object code for Component Shape objects."""
import FreeCAD
import Part


class ComponentShape:
    """This class is about Component Shape Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::ComponentShape"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyLinkList", "Lines", "Geometry",
            "Lines of Shape.")

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        component = obj.getParentGroup()
        structure = component.getParentGroup()
        obj.Placement = structure.Placement
        
        edges = [line.Shape for line in obj.Lines]
        sorted = Part.sortEdges(edges)
        if not sorted: return
        wire = Part.Wire(sorted[0])
        if wire.isClosed():
            obj.Shape = Part.Face(wire)
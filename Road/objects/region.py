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

"""Provides the object code for Region objects."""
import FreeCAD

import Part

from ..functions.region import get_lines
from ..geoutils.alignment_old import transformation


class Region:
    """This class is about Region object data features."""

    def __init__(self, obj):
        """Set data properties."""
        self.Type = "Road::Region"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Object shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyBool", "AtHorizontalAlignmentPoints", "Base",
            "Show/hide labels").AtHorizontalAlignmentPoints = True

        obj.addProperty(
            "App::PropertyPythonObject", "Stations", "Base",
            "List of stations").Stations = {}

        obj.addProperty(
            "App::PropertyBool", "FromAlignmentStart", "Region",
            "Show/hide labels").FromAlignmentStart = True

        obj.addProperty(
            "App::PropertyBool", "ToAlignmentEnd", "Region",
            "Show/hide labels").ToAlignmentEnd = True

        obj.addProperty(
            "App::PropertyLength", "StartStation", "Station",
            "Guide lines start station").StartStation = 0

        obj.addProperty(
            "App::PropertyLength", "EndStation", "Station",
            "Guide lines end station").EndStation = 0

        obj.addProperty(
            "App::PropertyFloat", "IncrementAlongTangents", "Increment",
            "Distance between guide lines along tangents").IncrementAlongTangents = 10

        obj.addProperty(
            "App::PropertyFloat", "IncrementAlongCurves", "Increment",
            "Distance between guide lines along curves").IncrementAlongCurves = 10

        obj.addProperty(
            "App::PropertyFloat", "IncrementAlongSpirals", "Increment",
            "Distance between guide lines along spirals").IncrementAlongSpirals = 10

        obj.addProperty(
            "App::PropertyFloat", "RightOffset", "Offset",
            "Length of right offset").RightOffset = 20

        obj.addProperty(
            "App::PropertyFloat", "LeftOffset", "Offset",
            "Length of left offset").LeftOffset = 20

        obj.setEditorMode('StartStation', 1)
        obj.setEditorMode('EndStation', 1)

        self.onChanged(obj,'FromAlignmentStart')
        self.onChanged(obj,'ToAlignmentEnd')

        obj.Proxy = self

    def execute(self, obj):
        """
        Do something when doing a recomputation.
        """

        """
        start = obj.getPropertyByName("StartStation")
        end = obj.getPropertyByName("EndStation")
        """

        regions = obj.getParentGroup()
        alignment = regions.getParentGroup()

        tangent = obj.getPropertyByName("IncrementAlongTangents")
        curve = obj.getPropertyByName("IncrementAlongCurves")
        spiral = obj.getPropertyByName("IncrementAlongSpirals")
        horizontal = obj.getPropertyByName("AtHorizontalAlignmentPoints")

        stations = transformation(alignment, tangent, curve, spiral, horizontal)

        offset_left = obj.getPropertyByName("LeftOffset")*1000
        offset_right = obj.getPropertyByName("RightOffset")*1000

        obj.Shape = get_lines(stations, offset_left, offset_right)

    def onChanged(self, obj, prop):
        """
        Do something when a data property has changed.
        """
        regions = obj.getParentGroup()
        if not regions: return
        alignment = regions.getParentGroup()

        if prop == "Stations":
            obj.Placement = alignment.Placement if alignment else FreeCAD.Placement()

        if prop == "FromAlignmentStart":
            if obj.getPropertyByName(prop):
                obj.setEditorMode('StartStation', 1)
                obj.StartStation = alignment.StartStation
            else:
                obj.setEditorMode('StartStation', 0)

        if prop == "ToAlignmentEnd":
            if obj.getPropertyByName(prop):
                obj.setEditorMode('EndStation', 1)
                obj.EndStation = alignment.EndStation
            else:
                obj.setEditorMode('EndStation', 0)

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

import Part

from ..functions.region_functions import RegionFunctions
from ..utils.get_group import georigin


class Region(RegionFunctions):
    """
    This class is about Region object data features.
    """

    def __init__(self, obj):
        '''
        Set data properties.
        '''
        self.Type = 'Road::Region'

        obj.addProperty(
            "App::PropertyBool", "AtHorizontalAlignmentPoints", "Base",
            "Show/hide labels").AtHorizontalAlignmentPoints = True

        obj.addProperty(
            "App::PropertyFloatList", "StationList", "Base",
            "List of stations").StationList = []

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Object shape").Shape = Part.Shape()

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
            "App::PropertyLength", "IncrementAlongTangents", "Increment",
            "Distance between guide lines along tangents").IncrementAlongTangents = 10000

        obj.addProperty(
            "App::PropertyLength", "IncrementAlongCurves", "Increment",
            "Distance between guide lines along curves").IncrementAlongCurves = 5000

        obj.addProperty(
            "App::PropertyLength", "IncrementAlongSpirals", "Increment",
            "Distance between guide lines along spirals").IncrementAlongSpirals = 5000

        obj.addProperty(
            "App::PropertyLength", "RightOffset", "Offset",
            "Length of right offset").RightOffset = 20000

        obj.addProperty(
            "App::PropertyLength", "LeftOffset", "Offset",
            "Length of left offset").LeftOffset = 20000

        obj.setEditorMode('StartStation', 1)
        obj.setEditorMode('EndStation', 1)

        self.onChanged(obj,'FromAlignmentStart')
        self.onChanged(obj,'ToAlignmentEnd')

        obj.Proxy = self

    def onChanged(self, obj, prop):
        '''
        Do something when a data property has changed.
        '''
        alignment = obj.InList[0].InList[0]
        start, end = self.get_alignment_infos(alignment)

        if prop == "FromAlignmentStart":
            from_start = obj.getPropertyByName("FromAlignmentStart")
            if from_start:
                obj.setEditorMode('StartStation', 1)
                obj.StartStation = start
            else:
                obj.setEditorMode('StartStation', 0)

        if prop == "ToAlignmentEnd":
            to_end = obj.getPropertyByName("ToAlignmentEnd")
            if to_end:
                obj.setEditorMode('EndStation', 1)
                obj.EndStation = end
            else:
                obj.setEditorMode('EndStation', 0)

    def execute(self, obj):
        '''
        Do something when doing a recomputation.
        '''
        alignment = obj.InList[0].InList[0]

        tangent = obj.getPropertyByName("IncrementAlongTangents")
        curve = obj.getPropertyByName("IncrementAlongCurves")
        spiral = obj.getPropertyByName("IncrementAlongSpirals")
        increments = [tangent, curve, spiral]

        start = obj.getPropertyByName("StartStation")
        end = obj.getPropertyByName("EndStation")
        region = [start, end]

        horiz_pnts = obj.getPropertyByName("AtHorizontalAlignmentPoints")

        obj.StationList = self.generate(alignment,increments, region, horiz_pnts)

        left_offset = obj.getPropertyByName("LeftOffset")
        right_offset = obj.getPropertyByName("RightOffset")
        offsets = [left_offset, right_offset]
        origin = georigin()

        obj.Shape = self.get_lines(origin.Origin, alignment, offsets, obj.StationList)
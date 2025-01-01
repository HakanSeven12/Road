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

"""Provides the object code for Section objects."""

import Part

from ..functions.section_functions import SectionFunctions


class Section(SectionFunctions):
    """
    This class is about Section object data features.
    """

    def __init__(self, obj):
        '''
        Set data properties.
        '''

        self.Type = 'Road::Section'

        obj.addProperty(
            'App::PropertyLink', "Surface", "Base",
            "Projection surface").Surface = None

        obj.addProperty(
            'App::PropertyFloatList', "MinZ", "Base",
            "Minimum elevations").MinZ = []

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Object shape").Shape = Part.Shape()

        obj.Proxy = self

    def onChanged(self, obj, prop):
        '''
        Do something when a data property has changed.
        '''
        if prop == "Surface":
            surface = obj.getPropertyByName("Surface")

            if surface:
                cs = obj.getParentGroup()
                region = cs.getParentGroup()

                obj.MinZ = self.minimum_elevations(region, surface)

    def execute(self, obj):
        '''
        Do something when doing a recomputation. 
        '''
        surface = obj.getPropertyByName("Surface")

        if surface and obj.InList:
            cs = obj.getParentGroup()
            region = cs.getParentGroup()

            horizons = cs.Horizons
            if not horizons: return

            pos = cs.Position
            h = cs.Height.Value
            w = cs.Width.Value
            ver = cs.Vertical.Value
            hor = cs.Horizontal.Value
            geometry = [h, w]
            gaps = [ver, hor]

            obj.Shape = self.draw_2d_sections(pos, region, surface, geometry, gaps, horizons)
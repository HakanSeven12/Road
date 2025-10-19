# SPDX-License-Identifier: LGPL-2.1-or-later

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
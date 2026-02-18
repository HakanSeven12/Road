# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Table objects."""

import Part

from ..functions.volume_functions import VolumeFunctions


class Volume(VolumeFunctions):
    """
    This class is about Volume Object data features.
    """

    def __init__(self, obj):
        '''
        Set data properties.
        '''
        self.Type = 'Road::Volume'

        obj.addProperty(
            'App::PropertyLinkList', "TopSections", "Base",
            "Top section list").TopSections = []

        obj.addProperty(
            'App::PropertyLinkList', "BottomSections", "Base",
            "Bottom section list").BottomSections = []

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Volume areas shape").Shape = Part.Shape()

        obj.Proxy = self

    def onChanged(self, obj, prop):
        '''
        Do something when a data property has changed.
        '''
        return

    def execute(self, obj):
        '''
        Do something when doing a recomputation. 
        '''
        volumes = obj.getParentGroup()
        region = volumes.getParentGroup()
        tops = obj.getPropertyByName("TopSections")
        bottoms = obj.getPropertyByName("BottomSections")

        if tops and bottoms:
            obj.Shape = self.get_areas(region, tops, bottoms)
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Sections objects."""

import FreeCAD

class Sections:
    """
    This class is about Section object data features.
    """

    def __init__(self, obj):
        '''
        Set data properties.
        '''
        self.Type = 'Road::Sections'

        obj.addProperty(
            'App::PropertyVector', "Position", "Base",
            "Section creation origin").Position = FreeCAD.Vector()

        obj.addProperty(
            'App::PropertyFloatList', "Horizons", "Base",
            "Horizons").Horizons = []

        obj.addProperty(
            "App::PropertyLength", "Height", "Geometry",
            "Height of section view").Height = 50000

        obj.addProperty(
            "App::PropertyLength", "Width", "Geometry",
            "Width of section view").Width = 100000

        obj.addProperty(
            "App::PropertyLength", "Vertical", "Gaps",
            "Vertical gap between section view").Vertical = 50000

        obj.addProperty(
            "App::PropertyLength", "Horizontal", "Gaps",
            "Horizontal gap between section view").Horizontal = 50000

        obj.Proxy = self

    def execute(self, obj):
        '''
        Do something when doing a recomputation. 
        '''
        minz_lists = []
        for sec in obj.Group:
            minz_lists.append(sec.MinZ)

        horizons = []
        for i in zip(*minz_lists):
            horizons.append(min(i))

        obj.Horizons = horizons


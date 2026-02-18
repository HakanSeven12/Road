# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Table objects."""

import FreeCAD


class Table:
    """
    This class is about Table Object data features.
    """

    def __init__(self, obj):
        '''
        Set data properties.
        '''

        self.Type = 'Road::Table'

        obj.addProperty(
            'App::PropertyString', "TableTitle", "Base",
            "Table title").TableTitle = "Volume Table"

        obj.addProperty(
            'App::PropertyVector', "Position", "Base",
            "Section creation origin").Position = FreeCAD.Vector()

        obj.addProperty(
            'App::PropertyLink', "VolumeAreas", "Base",
            "Volume Areas").VolumeAreas = None

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
        return
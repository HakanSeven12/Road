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
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
        self.Type = 'Trails::Sections'

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


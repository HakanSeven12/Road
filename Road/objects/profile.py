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

"""Provides the object code for Profile objects."""

import FreeCAD

import Part

from ..utils.get_group import georigin
from ..functions import profile


class Profile:
    """This class is about Profile object data features."""

    def __init__(self, obj):
        """Set data properties."""
        self.Type = "Road::Profile"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "App::PropertyLink", "Terrain", "Base",
            "Projection surface").Terrain = None

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Object shape").Shape = Part.Shape()

        obj.Proxy = self


    def execute(self, obj):
        '''
        Do something when doing a recomputation. 
        '''
        terrain = obj.getPropertyByName("Terrain")

        if terrain and obj.InList:
            profile_frame = obj.getParentGroup()
            profiles = profile_frame.getParentGroup()
            alignment = profiles.getParentGroup()

            origin = georigin().Base
            shape = alignment.Shape.copy()
            shape.Placement.move(origin.negative())

            shp = profile.from_mesh(
                shape, terrain.Mesh, profile_frame.Horizon)
            
            shp.Placement = profile_frame.Placement

            obj.Shape = shp
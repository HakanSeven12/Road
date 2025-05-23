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

"""Provides functions to create GeoPoint objects."""

import FreeCAD

from ..objects.geopoint import GeoPoint
from ..viewproviders.view_geopoint import ViewProviderGeoPoint

def create(name="GeoPoint", easting=0, northing=0, elevation=0, description=""):
    obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "GeoPoint")

    GeoPoint(obj)
    ViewProviderGeoPoint(obj.ViewObject)

    obj.Label = name
    obj.Number = int(obj.Name[8:]) + 1 if obj.Name != "GeoPoint" else 1
    obj.Placement.Base = FreeCAD.Vector(easting, northing, elevation).multiply(1000)
    obj.Description = description

    return obj
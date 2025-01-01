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

"""Provides the object code for Cluster objects."""
import FreeCAD
import Part


class GeoPoint:
    """This class is about Cluster Object data features."""

    def __init__(self, obj, number=1, easting=0, northing=0, elevation=0, description=""):
        """Set data properties."""

        self.Type = "Road::GeoPoint"

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Vertex(FreeCAD.Vector(easting, northing, elevation).multiply(1000))

        obj.addProperty(
            "App::PropertyInteger", "Number", "Base",
            "Show point name labels").Number = number

        obj.addProperty(
            "App::PropertyString", "Description", "Base",
            "Show description labels").Description = description

        obj.addProperty(
            "App::PropertyFloat", "Easting", "Geometry",
            "Show easting labels").Easting = easting

        obj.addProperty(
            "App::PropertyFloat", "Northing", "Geometry",
            "Show norting labels").Northing = northing

        obj.addProperty(
            "App::PropertyFloat", "PointElevation", "Geometry",
            "Point elevation").PointElevation = elevation

        obj.Proxy = self

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        if prop in ["Easting", "Northing", "PointElevation"]:
            coordinate = FreeCAD.Vector(obj.Easting, obj.Northing, obj.PointElevation)
            obj.Shape = Part.Vertex(coordinate.multiply(1000))
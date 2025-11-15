# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Cluster objects."""
import FreeCAD, Points
from.geo_object import GeoObject


class GeoPoints(GeoObject):
    """This class is about Cluster Object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = "Road::GeoPoints"

        obj.addProperty(
            "App::PropertyInteger", "Number", "Base",
            "Show point name labels").Number = 1

        obj.addProperty(
            "App::PropertyString", "Description", "Base",
            "Show description labels").Description = ""

        obj.addProperty(
            "App::PropertyPythonObject", "Model", "Base",
            "Geo Points meta data").Model = {}

        obj.addProperty(
            "App::PropertyFloat", "Easting", "Location",
            "Show easting labels").Easting = 0

        obj.addProperty(
            "App::PropertyFloat", "Northing", "Location",
            "Show norting labels").Northing = 0

        obj.addProperty(
            "App::PropertyFloat", "PointElevation", "Location",
            "Point elevation").PointElevation = 0

        obj.Proxy = self

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        super().onChanged(obj, prop)
        if prop == "Model":
            points = []
            origin = None
            for point in obj.Model.values():
                easting = point.get("Easting", 0.0)
                northing = point.get("Northing", 0.0)
                elevation = point.get("Elevation", 0.0)
                pt = FreeCAD.Vector(easting, northing, elevation).multiply(1000)
                if origin is None: origin = pt
                points.append(pt.sub(origin))
            
            if points:
                obj.Points = Points.Points(points)
                obj.Geolocation.Base = origin
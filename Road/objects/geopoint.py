# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Cluster objects."""
import FreeCAD
import Part


class GeoPoint:
    """This class is about Cluster Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::GeoPoint"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Vertex(FreeCAD.Vector())

        obj.addProperty(
            "App::PropertyInteger", "Number", "Base",
            "Show point name labels").Number = 1

        obj.addProperty(
            "App::PropertyString", "Description", "Base",
            "Show description labels").Description = ""

        obj.addProperty(
            "App::PropertyFloat", "Easting", "Geometry",
            "Show easting labels").Easting = 0

        obj.addProperty(
            "App::PropertyFloat", "Northing", "Geometry",
            "Show norting labels").Northing = 0

        obj.addProperty(
            "App::PropertyFloat", "PointElevation", "Geometry",
            "Point elevation").PointElevation = 0

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        shp = Part.Vertex(FreeCAD.Vector())
        shp.Placement = obj.Placement
        obj.Shape = shp

    def onChanged(self, obj, prop):
        """Do something when a data property has changed."""
        if prop in ["Easting", "Northing", "PointElevation"]:
            coordinate = FreeCAD.Vector(obj.Easting, obj.Northing, obj.PointElevation)
            location = coordinate.multiply(1000)

            if obj.Placement.Base != location:
                obj.Placement.Base = location

        if prop == "Placement":
            placement = obj.getPropertyByName(prop)
            coordinate = FreeCAD.Vector(obj.Easting, obj.Northing, obj.PointElevation)
            location = coordinate.multiply(1000)

            if placement.Base != location:
                obj.Easting = placement.Base.x / 1000
                obj.Northing = placement.Base.y / 1000
                obj.PointElevation = placement.Base.z / 1000
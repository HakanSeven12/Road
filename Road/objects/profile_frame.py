# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Profile Frame objects."""

import FreeCAD, Part, MeshPart
from .geo_object import GeoObject
import math


class ProfileFrame(GeoObject):
    """This class is about Profile Frame object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = 'Road::ProfileFrame'

        obj.addProperty(
            "App::PropertyPythonObject", "Model", "Base",
            "List of stations").Model = {}
        
        obj.addProperty(
            "App::PropertyFloat", "Horizon", "Base",
            "Minimum elevation").Horizon = 0

        obj.addProperty(
            'App::PropertyLinkList', "Terrains", "Base",
            "Projection terrains").Terrains = []

        obj.addProperty(
            "App::PropertyFloat", "Height", "Geometry",
            "Height of section view").Height = 15

        obj.addProperty(
            "App::PropertyFloat", "Length", "Geometry",
            "Width of section view").Length = 1

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""

        profiles = obj.getParentGroup()
        alignment = profiles.getParentGroup()

        length = alignment.Length
        obj.Length = length if length else 1000
        
        obj.Model = {'surface': {}, 'design': {}}
        horizon = math.inf
        for terrain in obj.Terrains:
            flat_points = []
            for edge in alignment.Shape.Edges:
                params = MeshPart.findSectionParameters(
                    edge, terrain.Mesh, FreeCAD.Vector(0, 0, 1))
                params.insert(0, edge.FirstParameter+1)
                params.append(edge.LastParameter-1)

                values = [edge.valueAt(glp) for glp in params]
                flat_points.extend(values)

            projected_points = MeshPart.projectPointsOnMesh(
                flat_points, terrain.Mesh, FreeCAD.Vector(0, 0, 1))
            
            station_elevation = []
            for point in projected_points:
                point = point.sub(alignment.Placement.Base).multiply(0.001)
                station, offset = alignment.Model.get_station_offset([*point])
                if station: station_elevation.append([station, point.z])
                if point.z < horizon: horizon = point.z

            # Sort by offset
            station_elevation.sort(key=lambda x: x[0])
            obj.Model['surface'][terrain.Label] = station_elevation

        # Set horizon
        obj.Horizon = math.floor(horizon / 5) * 5 if horizon != math.inf else 0

        # Calculate grid position for this item
        p1 = FreeCAD.Vector()
        p2 = FreeCAD.Vector(0, obj.Height * 1000)
        p3 = FreeCAD.Vector(obj.Length * 1000, obj.Height * 1000)
        p4 = FreeCAD.Vector(obj.Length * 1000, 0, 0)
        frame = Part.makePolygon([p1, p2, p3, p4, p1])
            
        profiles = []
        for terrain, values in obj.Model['surface'].items():
            point_list = []
            for station, elevation in values:
                if station is None or elevation is None: continue
                point_list.append(FreeCAD.Vector(station, elevation - obj.Horizon).multiply(1000))
            
            if len(point_list) > 1:
                profile = Part.makePolygon(point_list)
                profiles.append(profile)
            
        shp_profile = Part.Compound(profiles)
        obj.Shape = Part.Compound([frame, shp_profile])

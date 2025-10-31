# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Section objects."""

import FreeCAD, Part, MeshPart
from .geo_object import GeoObject
import math


class Section(GeoObject):
    """This class is about Section object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = 'Road::Section'

        obj.addProperty(
            "App::PropertyPythonObject", "Model", "Base",
            "List of stations").Model = {}
        
        obj.addProperty(
            'App::PropertyLinkList', "Terrains", "Base",
            "Projection terrains").Terrains = []

        obj.addProperty(
            "App::PropertyFloat", "Height", "Geometry",
            "Height of section view").Height = 15

        obj.addProperty(
            "App::PropertyFloat", "Width", "Geometry",
            "Width of section view").Width = 40

        obj.addProperty(
            "App::PropertyFloat", "Vertical", "Distances",
            "Vertical distance between section frame placements").Vertical = 20

        obj.addProperty(
            "App::PropertyFloat", "Horizontal", "Distances",
            "Horizontal distance between section frame placements").Horizontal = 50

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""

        sections = obj.getParentGroup()
        region = sections.getParentGroup()
        regions = region.getParentGroup()
        alignment = regions.getParentGroup()
        if not hasattr(alignment.Proxy, "model"): return

        for idx, sta in enumerate(region.Stations):
            obj.Model[sta] = {'horizon': 0, 'sections': {}}
            horizon = 0
            for terrain in obj.Terrains:
                flat_points = []
                for edge in region.Shape.Wires[idx].Edges:
                    params = MeshPart.findSectionParameters(
                        edge, terrain.Mesh, FreeCAD.Vector(0, 0, 1))
                    params.insert(0, edge.FirstParameter+1)
                    params.append(edge.LastParameter-1)

                    values = [edge.valueAt(glp) for glp in params]
                    flat_points.extend(values)

                projected_points = MeshPart.projectPointsOnMesh(
                    flat_points, terrain.Mesh, FreeCAD.Vector(0, 0, 1))
                
                offset_elevation = []
                for point in projected_points:
                    point = point.add(terrain.Geolocation.Base).sub(terrain.Placement.Base)
                    station, position, offset, index = alignment.Proxy.model.get_station_offset([*point])
                    if offset: offset_elevation.append([offset, point.z])
                    if horizon==0 or point.z < horizon: horizon = point.z

                # Sort by offset
                offset_elevation.sort(key=lambda x: x[0])
                obj.Model[sta]['sections'][terrain.Label] = offset_elevation

            # Set horizon
            obj.Model[sta]["horizon"] = math.floor(horizon / 5000) * 5000

        # Calculate grid dimensions (equal rows and columns)
        total_items = len(obj.Model)
        grid_size = math.ceil(math.sqrt(total_items))  # This ensures rows = columns

        current_col = 0
        current_row = 0

        frames = []
        crosssections = []
        for sta, data in obj.Model.items():
            # Calculate grid position for this item
            origin = FreeCAD.Vector(current_col * obj.Horizontal, current_row * obj.Vertical, 0).multiply(1000)
            obj.Model[sta]["origin"] = [*origin]
            
            p2 = origin.add(FreeCAD.Vector(-obj.Width * 1000 / 2, 0, 0))
            p3 = origin.add(FreeCAD.Vector(-obj.Width * 1000 / 2, obj.Height * 1000, 0))
            p4 = origin.add(FreeCAD.Vector(obj.Width * 1000 / 2, obj.Height * 1000, 0))
            p5 = origin.add(FreeCAD.Vector(obj.Width * 1000 / 2, 0, 0))
            frame = Part.makePolygon([origin, p2, p3, p4, p5, origin])
            frames.append(frame)
            
            for terrain, values in data['sections'].items():
                point_list = []
                for offset, elevation in values:
                    if offset is None or elevation is None: continue
                    pt = FreeCAD.Vector(offset, elevation - data.get("horizon"), 0)
                    point_list.append(origin.add(pt))
                
                if len(point_list) > 1:
                    section = Part.makePolygon(point_list)
                    crosssections.append(section)
            
            # Update grid position
            current_row += 1
            if current_row >= grid_size:
                current_row = 0
                current_col += 1
            
        shp_frame = Part.Compound(frames)
        shp_section = Part.Compound(crosssections)
        obj.Shape = Part.Compound([shp_frame, shp_section])

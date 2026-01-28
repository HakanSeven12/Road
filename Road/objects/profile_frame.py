# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Profile Frame objects."""

import FreeCAD, Part
from .geo_object import GeoObject
from..functions.project_shape_to_mesh import project_shape_to_mesh
from ..geometry.profile.profile import Profile
from ..geometry.profile.tangent import Tangent
from ..geometry.profile.parabola import Parabola
from ..geometry.profile.arc import Arc
import math


class ProfileFrame(GeoObject):
    """This class is about Profile Frame object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = 'Road::ProfileFrame'

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

        profiles_obj = obj.getParentGroup()
        alignment = profiles_obj.getParentGroup()
        
        profiles = alignment.Model.get_profiles()
        if profiles is None:
            return
            
        length = alignment.Model.get_length()
        obj.Length = length if length else 1000

        surface_profiles = {}
        horizon = math.inf
        
        for terrain in obj.Terrains:
            points = project_shape_to_mesh(alignment, terrain)

            # Convert projected points to station-elevation pairs
            pvi_points = []
            for p in points:
                # Convert to alignment coordinate system
                point = p.sub(alignment.Placement.Base).multiply(0.001)
                
                # Get station and offset from alignment
                station, offset = alignment.Model.get_station_offset(
                    (point.x, point.y), 
                    input_system='current'
                )
                
                if station is not None: 
                    pvi_points.append({'station': station, 'elevation': point.z})
                    if point.z < horizon: 
                        horizon = point.z

            # Sort by station
            pvi_points.sort(key=lambda x: x['station'])

            if terrain.Label in profiles.get_surface_names():
                pr = profiles.get_surface_by_name(terrain.Label)
                pr.update(pvi_points)

            else:
                # Create new surface profile
                pr = Profile(
                    name=terrain.Label,
                    description="Surface profile",
                    geometry=pvi_points
                )
                profiles.surface_profiles.append(pr)

    
            # Get design profile elevations for horizon calculation
            for dp in profiles.design_profiles:
                for elem in dp.get_elements():
                    sta_start, sta_end = elem.get_station_range()
                    try:
                        elev_start = elem.get_elevation_at_station(sta_start)
                        elev_end = elem.get_elevation_at_station(sta_end)
                        if elev_start < horizon:
                            horizon = elev_start
                        if elev_end < horizon:
                            horizon = elev_end
                    except:
                        pass

        # Set horizon
        obj.Horizon = math.floor(horizon / 5) * 5 if horizon != math.inf else 0

        # Build Shape structure
        # Shape contains 3 compounds:
        # 1. Frame border
        # 2. Surface profiles compound
        # 3. Design profiles compound
        
        # 1. Frame border
        p1 = FreeCAD.Vector()
        p2 = FreeCAD.Vector(0, obj.Height * 1000)
        p3 = FreeCAD.Vector(obj.Length * 1000, obj.Height * 1000)
        p4 = FreeCAD.Vector(obj.Length * 1000, 0, 0)
        frame_border = Part.makePolygon([p1, p2, p3, p4, p1])
        
        # 2. Surface profiles compound
        surface_shapes = []
        for sp in profiles.surface_profiles:
            for elem in sp.get_elements():
                try:
                    shape = self._generate_profile_shape_from_element(
                        elem, obj.Horizon)
                    if shape:
                        surface_shapes.append(shape)
                        
                except Exception as e:
                    FreeCAD.Console.PrintWarning(
                        f"Failed to generate surface profile shape: {str(e)}\n"
                    )
        
        surface_compound = Part.Compound(surface_shapes) if surface_shapes else Part.Shape()
        
        # 3. Design profiles compound
        design_shapes = []

        for dp in profiles.design_profiles:
            geometry_elements = dp.get_elements()
            
            for elem in geometry_elements:
                try:
                    shape = self._generate_profile_shape_from_element(
                        elem, obj.Horizon)
                    if shape:
                        design_shapes.append(shape)

                except Exception as e:
                    FreeCAD.Console.PrintWarning(
                        f"Failed to generate design profile shape: {str(e)}\n"
                    )
        
        design_compound = Part.Compound(design_shapes) if design_shapes else Part.Shape()
        
        # Final compound: [frame_border, surface_compound, design_compound]
        obj.Shape = Part.Compound([frame_border, surface_compound, design_compound])

    def _generate_profile_shape_from_element(self, element, horizon):
        """
        Generate FreeCAD shape from profile geometry element.
        
        Args:
            element: Profile geometry element (Tangent, Parabola, or Arc)
            horizon: Base elevation to subtract from elevations
            
        Returns:
            Part.Shape representing the profile element
        """
        try:
            sta_start, sta_end = element.get_station_range()
            
            if isinstance(element, Tangent):
                # Tangent is a straight line
                elev_start = element.get_elevation_at_station(sta_start)
                elev_end = element.get_elevation_at_station(sta_end)
                
                p1 = FreeCAD.Vector(sta_start, elev_start - horizon).multiply(1000)
                p2 = FreeCAD.Vector(sta_end, elev_end - horizon).multiply(1000)
                
                return Part.LineSegment(p1, p2).toShape()
                
            elif isinstance(element, Parabola):
                # Parabola - use BSpline for smooth curve
                points = []
                step = 1.0  # 1 meter intervals for smooth curves
                current_sta = sta_start
                
                while current_sta <= sta_end:
                    elevation = element.get_elevation_at_station(current_sta)
                    points.append(
                        FreeCAD.Vector(
                            current_sta, 
                            elevation - horizon
                        ).multiply(1000)
                    )
                    current_sta += step
                
                # Add last point
                elevation = element.get_elevation_at_station(sta_end)
                points.append(
                    FreeCAD.Vector(
                        sta_end, 
                        elevation - horizon
                    ).multiply(1000)
                )
                
                if len(points) > 1:
                    # Use BSpline for smooth parabolic curve
                    bspline = Part.BSplineCurve()
                    bspline.interpolate(points)
                    return bspline.toShape()
                    
            elif isinstance(element, Arc):
                # Arc - use Part.Arc for circular curve
                # Calculate three points: start, middle, end
                elev_start = element.get_elevation_at_station(sta_start)
                elev_end = element.get_elevation_at_station(sta_end)
                
                # Middle point
                sta_mid = (sta_start + sta_end) / 2
                elev_mid = element.get_elevation_at_station(sta_mid)
                
                p1 = FreeCAD.Vector(sta_start, elev_start - horizon).multiply(1000)
                p2 = FreeCAD.Vector(sta_mid, elev_mid - horizon).multiply(1000)
                p3 = FreeCAD.Vector(sta_end, elev_end - horizon).multiply(1000)
                
                # Create arc from three points
                return Part.Arc(p1, p2, p3).toShape()
            
            return None
            
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"Failed to generate profile shape from element: {str(e)}\n"
            )
            return None
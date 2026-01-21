# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Profile Frame objects."""

import FreeCAD, Part, MeshPart
from .geo_object import GeoObject
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

        profiles = obj.getParentGroup()
        if profiles is None:
            return
            
        alignment = profiles.getParentGroup()
        if alignment is None:
            return

        # Get alignment model
        alignment_model = alignment.Model
        
        if alignment_model is None:
            return
        
        try:
            if not alignment_model.elements:
                return
        except (AttributeError, TypeError):
            return
        
        length = alignment_model.get_length()
        obj.Length = length if length else 1000
        
        # Dictionary to store surface profile data temporarily
        surface_profiles = {}
        horizon = math.inf
        
        # Process each terrain to get surface profiles
        for terrain in obj.Terrains:
            flat_points = []
            
            # Get intersection points between alignment and terrain
            for edge in alignment.Shape.Edges:
                params = MeshPart.findSectionParameters(
                    edge, terrain.Mesh, FreeCAD.Vector(0, 0, 1))
                params.insert(0, edge.FirstParameter+1)
                params.append(edge.LastParameter-1)

                values = [edge.valueAt(glp) for glp in params]
                flat_points.extend(values)

            # Project points onto terrain mesh
            projected_points = MeshPart.projectPointsOnMesh(
                flat_points, terrain.Mesh, FreeCAD.Vector(0, 0, 1))
            
            # Convert projected points to station-elevation pairs
            station_elevation = []
            for point in projected_points:
                # Convert to alignment coordinate system
                point = point.sub(alignment.Placement.Base).multiply(0.001)
                
                # Get station and offset from alignment
                station, offset = alignment_model.get_station_offset(
                    (point.x, point.y), 
                    input_system='current'
                )
                
                if station is not None: 
                    station_elevation.append([station, point.z])
                    if point.z < horizon: 
                        horizon = point.z

            # Sort by station
            station_elevation.sort(key=lambda x: x[0])
            
            # Store surface profile data
            surface_profiles[terrain.Label] = station_elevation
        
        # Add surface profiles to alignment's profile model
        if alignment_model.has_profile():
            profile = alignment_model.get_profile()
            
            # Add surface profiles as ProfSurf to the profile
            for terrain_name, station_elevation in surface_profiles.items():
                # Check if this surface already exists in profile
                existing_surfaces = profile.get_surface_names()
                
                if terrain_name not in existing_surfaces:
                    # Create new ProfSurf data
                    profsurf_data = {
                        'name': terrain_name,
                        'surfType': 'Terrain',
                        'geometry': []
                    }
                    
                    # Create Tangent segments from points
                    for i in range(len(station_elevation) - 1):
                        sta1, elev1 = station_elevation[i]
                        sta2, elev2 = station_elevation[i + 1]
                        
                        tangent = Tangent(
                            sta_start=sta1,
                            elev_start=elev1,
                            sta_end=sta2,
                            elev_end=elev2,
                            desc=f"{terrain_name} segment {i+1}"
                        )
                        profsurf_data['geometry'].append(tangent)
                    
                    # Add to profile's profsurf_list
                    profile.profsurf_list.append(profsurf_data)
                else:
                    # Update existing surface
                    for profsurf in profile.profsurf_list:
                        if profsurf['name'] == terrain_name:
                            # Recreate geometry from points
                            profsurf['geometry'] = []
                            
                            for i in range(len(station_elevation) - 1):
                                sta1, elev1 = station_elevation[i]
                                sta2, elev2 = station_elevation[i + 1]
                                
                                tangent = Tangent(
                                    sta_start=sta1,
                                    elev_start=elev1,
                                    sta_end=sta2,
                                    elev_end=elev2,
                                    desc=f"{terrain_name} segment {i+1}"
                                )
                                profsurf['geometry'].append(tangent)
                            break
            
            # Get design profile elevations for horizon calculation
            profalign_names = profile.get_profalign_names()
            for profalign_name in profalign_names:
                # Get profile geometry elements to find elevation range
                geometry_elements = profile.get_geometry_elements(profalign_name)
                for elem in geometry_elements:
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
        if alignment_model.has_profile():
            profile = alignment_model.get_profile()
            surface_names = profile.get_surface_names()
            
            for surface_name in surface_names:
                surface_geometry = profile.get_surface_geometry_elements(surface_name)
                
                for tangent in surface_geometry:
                    try:
                        shape = self._generate_profile_shape_from_element(
                            tangent, obj.Horizon
                        )
                        if shape:
                            surface_shapes.append(shape)
                    except Exception as e:
                        FreeCAD.Console.PrintWarning(
                            f"Failed to generate surface profile shape: {str(e)}\n"
                        )
        
        surface_compound = Part.Compound(surface_shapes) if surface_shapes else Part.Shape()
        
        # 3. Design profiles compound
        design_shapes = []
        if alignment_model.has_profile():
            profile = alignment_model.get_profile()
            profalign_names = profile.get_profalign_names()
            
            for profalign_name in profalign_names:
                geometry_elements = profile.get_geometry_elements(profalign_name)
                
                for elem in geometry_elements:
                    try:
                        shape = self._generate_profile_shape_from_element(
                            elem, obj.Horizon
                        )
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
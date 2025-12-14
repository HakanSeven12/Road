# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Dict, List, Tuple, Optional
from .arc import Arc
from .tangent import Tangent
from .parabola import Parabola


class Profile:
    """
    LandXML 1.2 vertical profile reader & geometry generator.
    Manages vertical alignment (ProfAlign) and surface profiles (ProfSurf).
    Works in conjunction with a horizontal Alignment.
    """

    def __init__(self, data: Dict, parent_alignment=None):
        """
        Initialize profile from LandXML data dictionary.
        
        Args:
            data: Dictionary containing profile data
            parent_alignment: Reference to parent Alignment object (optional)
        """
        # Profile metadata
        self.name = data.get('name', None)
        self.description = data.get('desc', None)
        self.sta_start = float(data['staStart']) if 'staStart' in data else None
        self.sta_end = float(data['staEnd']) if 'staEnd' in data else None
        self.alignment_name = data.get('alignmentName', None)
        
        # Reference to parent alignment (for station/offset calculations)
        self.parent_alignment = parent_alignment
        
        # PVI points (Profile Vertical Intersection points) - NOT geometry objects
        self.pvi_points = []  # List of dicts with station, elevation, description
        
        # Geometry elements (Tangent, Parabola, Arc)
        self.geometry_elements = []
        
        # Surface profiles (existing ground, etc.)
        self.profsurf_list = []
        
        # Parse ProfAlign (vertical alignment)
        if 'ProfAlign' in data and data['ProfAlign']:
            self._parse_profalign(data['ProfAlign'])
        
        # Parse ProfSurf elements (surface profiles)
        if 'ProfSurf' in data and data['ProfSurf']:
            self._parse_profsurf_list(data['ProfSurf'])
        
        # Compute profile properties
        self._compute_profile_properties()
    
    def _parse_profalign(self, profalign_data: Dict):
        """Parse vertical alignment (ProfAlign) data and create geometry"""
        
        # Temporary storage for parsed data
        raw_geometry = profalign_data.get('geometry', [])
        
        # First pass: Extract PVI points and curve data
        curves_data = []
        
        for geom_data in raw_geometry:
            geom_type = geom_data.get('Type', None)
            
            if geom_type == 'PVI':
                # Store PVI point (not a geometry object)
                pvi = {
                    'station': float(geom_data['station']),
                    'elevation': float(geom_data['elevation']),
                    'description': geom_data.get('desc', None)
                }
                self.pvi_points.append(pvi)
            
            elif geom_type in ['ParaCurve', 'UnsymParaCurve', 'CircCurve']:
                # Store curve data for second pass
                curves_data.append(geom_data)
        
        # Sort PVI points by station
        self.pvi_points.sort(key=lambda p: p['station'])
        
        if not self.pvi_points:
            return
        
        # Second pass: Create geometry elements (tangents and curves)
        self._create_geometry_elements(curves_data)
    
    def _create_geometry_elements(self, curves_data: List[Dict]):
        """
        Create geometry elements from PVI points and curve data.
        Automatically inserts tangents between curves.
        """
        if len(self.pvi_points) < 2:
            return
        
        # Track which PVI pairs have curves
        curve_map = {}  # {pvi_index: curve_data}
        
        # Map curves to their PVI positions
        for curve_data in curves_data:
            pvi_data = curve_data.get('pvi', {})
            if pvi_data:
                pvi_station = float(pvi_data['station'])
                
                # Find which PVI this curve belongs to
                for i, pvi in enumerate(self.pvi_points):
                    if abs(pvi['station'] - pvi_station) < 1e-6:
                        curve_map[i] = curve_data
                        break
        
        # Build geometry elements (tangents and curves) between consecutive PVIs
        for i in range(len(self.pvi_points) - 1):
            pvi_curr = self.pvi_points[i]
            pvi_next = self.pvi_points[i + 1]
            
            # Calculate grade between these two PVIs
            sta_diff = pvi_next['station'] - pvi_curr['station']
            elev_diff = pvi_next['elevation'] - pvi_curr['elevation']
            grade = elev_diff / sta_diff if sta_diff != 0 else 0.0
            
            # Check if there's a curve at the current PVI
            if i in curve_map:
                curve_data = curve_map[i]
                
                # Get previous grade (from previous element or assume same)
                if self.geometry_elements:
                    prev_elem = self.geometry_elements[-1]
                    if isinstance(prev_elem, Tangent):
                        prev_grade = prev_elem.grade
                    else:
                        prev_grade = prev_elem.grade_out
                else:
                    # First element - use current grade
                    prev_grade = grade
                
                # Create curve
                curve = self._create_curve(curve_data, prev_grade, grade)
                
                if curve:
                    # Add tangent before curve (if there's space)
                    if self.geometry_elements:
                        last_elem = self.geometry_elements[-1]
                        last_sta_end = last_elem.get_station_range()[1]
                        curve_sta_start = curve.get_station_range()[0]
                        
                        if curve_sta_start > last_sta_end + 1e-6:
                            # Create tangent from end of last element to start of curve
                            tangent = Tangent(
                                sta_start=last_sta_end,
                                elev_start=last_elem.get_elevation_at_station(last_sta_end),
                                sta_end=curve_sta_start,
                                elev_end=curve.elev_bvc
                            )
                            self.geometry_elements.append(tangent)
                    else:
                        # First element is a curve - add tangent from first PVI to curve start
                        curve_sta_start = curve.get_station_range()[0]
                        if pvi_curr['station'] < curve_sta_start - 1e-6:
                            tangent = Tangent(
                                sta_start=pvi_curr['station'],
                                elev_start=pvi_curr['elevation'],
                                sta_end=curve_sta_start,
                                elev_end=curve.elev_bvc
                            )
                            self.geometry_elements.append(tangent)
                    
                    self.geometry_elements.append(curve)
                    
                    # Add tangent after curve to next element (if space)
                    curve_sta_end = curve.get_station_range()[1]
                    if i + 1 < len(self.pvi_points) - 1:
                        # Not the last segment - add tangent to next curve or PVI
                        next_curve_data = curve_map.get(i + 1)
                        if next_curve_data:
                            next_curve_pvi = next_curve_data.get('pvi', {})
                            next_curve_sta = float(next_curve_pvi['station'])
                            next_curve_len = float(next_curve_data['length'])
                            next_curve_start = next_curve_sta - next_curve_len / 2
                            
                            if next_curve_start > curve_sta_end + 1e-6:
                                tangent = Tangent(
                                    sta_start=curve_sta_end,
                                    elev_start=curve.elev_evc,
                                    sta_end=next_curve_start,
                                    elev_end=curve.elev_evc + grade * (next_curve_start - curve_sta_end)
                                )
                                self.geometry_elements.append(tangent)
                    else:
                        # Last segment - add tangent to final PVI
                        if pvi_next['station'] > curve_sta_end + 1e-6:
                            tangent = Tangent(
                                sta_start=curve_sta_end,
                                elev_start=curve.elev_evc,
                                sta_end=pvi_next['station'],
                                elev_end=pvi_next['elevation']
                            )
                            self.geometry_elements.append(tangent)
            
            else:
                # No curve at this PVI - create simple tangent
                if not self.geometry_elements:
                    # First tangent
                    tangent = Tangent(
                        sta_start=pvi_curr['station'],
                        elev_start=pvi_curr['elevation'],
                        sta_end=pvi_next['station'],
                        elev_end=pvi_next['elevation']
                    )
                    self.geometry_elements.append(tangent)
                else:
                    # Continue from last element
                    last_elem = self.geometry_elements[-1]
                    last_sta_end = last_elem.get_station_range()[1]
                    
                    if last_sta_end < pvi_next['station'] - 1e-6:
                        tangent = Tangent(
                            sta_start=last_sta_end,
                            elev_start=last_elem.get_elevation_at_station(last_sta_end),
                            sta_end=pvi_next['station'],
                            elev_end=pvi_next['elevation']
                        )
                        self.geometry_elements.append(tangent)
    
    def _create_curve(self, curve_data: Dict, prev_grade: float, next_grade: float):
        """Create appropriate curve object from data"""
        
        geom_type = curve_data.get('Type')
        
        try:
            if geom_type in ['ParaCurve', 'UnsymParaCurve']:
                return Parabola(curve_data, prev_grade, next_grade)
            elif geom_type == 'CircCurve':
                return Arc(curve_data, prev_grade, next_grade)
        except Exception as e:
            print(f"Warning: Failed to create curve: {str(e)}")
            return None
    
    def _parse_profsurf_list(self, profsurf_list: List[Dict]):
        """Parse surface profile (ProfSurf) list"""
        
        for profsurf_data in profsurf_list:
            profsurf = {
                'name': profsurf_data.get('name', 'Surface Profile'),
                'description': profsurf_data.get('desc', None),
                'surfType': profsurf_data.get('surfType', None),
                'points': []  # List of (station, elevation) tuples
            }
            
            # Parse points
            points = profsurf_data.get('points', [])
            for point in points:
                if isinstance(point, (tuple, list)) and len(point) >= 2:
                    profsurf['points'].append((float(point[0]), float(point[1])))
            
            # Sort points by station
            profsurf['points'].sort(key=lambda p: p[0])
            
            self.profsurf_list.append(profsurf)
    
    def _compute_profile_properties(self):
        """Compute profile properties"""
        
        # Determine profile station range from geometry
        if self.geometry_elements:
            self.sta_start = self.geometry_elements[0].get_station_range()[0]
            self.sta_end = self.geometry_elements[-1].get_station_range()[1]
        elif self.pvi_points:
            self.sta_start = self.pvi_points[0]['station']
            self.sta_end = self.pvi_points[-1]['station']
    
    def get_elevation_at_station(self, station: float) -> Optional[float]:
        """
        Get elevation at given station from design profile.
        
        Args:
            station: Station value to query
            
        Returns:
            Elevation at station, or None if outside profile range
        """
        if not self.geometry_elements:
            return None
        
        # Find geometry element containing this station
        for elem in self.geometry_elements:
            sta_start, sta_end = elem.get_station_range()
            if sta_start <= station <= sta_end:
                return elem.get_elevation_at_station(station)
        
        return None
    
    def get_grade_at_station(self, station: float) -> Optional[float]:
        """
        Calculate grade (slope) at given station from design profile.
        
        Args:
            station: Station value to query
            
        Returns:
            Grade as decimal (e.g., 0.05 = 5%), or None if outside profile range
        """
        if not self.geometry_elements:
            return None
        
        # Find geometry element containing this station
        for elem in self.geometry_elements:
            sta_start, sta_end = elem.get_station_range()
            if sta_start <= station <= sta_end:
                return elem.get_grade_at_station(station)
        
        return None
    
    def get_surface_elevation_at_station(self, station: float, 
                                        surface_name: Optional[str] = None) -> Optional[float]:
        """
        Get elevation at given station from surface profile (ProfSurf).
        Uses linear interpolation between surface points.
        
        Args:
            station: Station value to query
            surface_name: Name of surface profile (uses first if None)
            
        Returns:
            Elevation at station, or None if outside profile range
        """
        if not self.profsurf_list:
            return None
        
        # Select surface profile
        if surface_name:
            profsurf = next((ps for ps in self.profsurf_list if ps['name'] == surface_name), None)
            if not profsurf:
                return None
        else:
            profsurf = self.profsurf_list[0]
        
        points = profsurf['points']
        if not points:
            return None
        
        # Check if station is within surface range
        if station < points[0][0] or station > points[-1][0]:
            return None
        
        # Find points bracketing this station
        for i in range(len(points) - 1):
            sta1, elev1 = points[i]
            sta2, elev2 = points[i + 1]
            
            if sta1 <= station <= sta2:
                # Linear interpolation
                if sta2 == sta1:
                    return elev1
                
                t = (station - sta1) / (sta2 - sta1)
                elevation = elev1 + t * (elev2 - elev1)
                
                return elevation
        
        return None
    
    def get_cut_fill_at_station(self, station: float, 
                                surface_name: Optional[str] = None) -> Optional[float]:
        """
        Calculate cut/fill at given station (design elevation - surface elevation).
        Positive value = fill, negative value = cut.
        
        Args:
            station: Station value to query
            surface_name: Name of surface profile (uses first if None)
            
        Returns:
            Cut/fill value, or None if data not available
        """
        design_elev = self.get_elevation_at_station(station)
        surface_elev = self.get_surface_elevation_at_station(station, surface_name)
        
        if design_elev is None or surface_elev is None:
            return None
        
        return design_elev - surface_elev
    
    def generate_profile_points(self, step: float, 
                               include_surface: bool = False,
                               surface_name: Optional[str] = None) -> List[Tuple]:
        """
        Generate profile points at regular station intervals.
        
        Args:
            step: Station interval between points
            include_surface: Include surface elevation in output
            surface_name: Name of surface profile (uses first if None and include_surface=True)
            
        Returns:
            List of tuples:
            - If include_surface=False: (station, design_elevation)
            - If include_surface=True: (station, design_elevation, surface_elevation)
        """
        if not self.geometry_elements:
            return []
        
        points = []
        current_station = self.sta_start
        
        while current_station <= self.sta_end:
            design_elev = self.get_elevation_at_station(current_station)
            
            if design_elev is not None:
                if include_surface:
                    surface_elev = self.get_surface_elevation_at_station(current_station, surface_name)
                    points.append((current_station, design_elev, surface_elev))
                else:
                    points.append((current_station, design_elev))
            
            current_station += step
        
        return points
    
    def get_pvi_points(self) -> List[Dict]:
        """Return list of all PVI points"""
        return self.pvi_points.copy()
    
    def get_geometry_elements(self) -> List:
        """Return list of all geometry elements"""
        return self.geometry_elements.copy()
    
    def get_surface_names(self) -> List[str]:
        """Return list of all surface profile names"""
        return [ps['name'] for ps in self.profsurf_list]
    
    def get_sta_start(self) -> Optional[float]:
        """Return profile start station"""
        return self.sta_start
    
    def get_sta_end(self) -> Optional[float]:
        """Return profile end station"""
        return self.sta_end
    
    def to_dict(self) -> Dict:
        """Export profile properties as dictionary"""
        return {
            'name': self.name,
            'desc': self.description,
            'staStart': self.sta_start,
            'staEnd': self.sta_end,
            'alignmentName': self.alignment_name,
            'pviCount': len(self.pvi_points),
            'geometryCount': len(self.geometry_elements),
            'surfaceProfileCount': len(self.profsurf_list),
            'pviPoints': self.pvi_points,
            'geometry': [elem.to_dict() for elem in self.geometry_elements],
            'surfaces': self.profsurf_list
        }
    
    def __repr__(self) -> str:
        """String representation of profile"""
        return (
            f"Profile(name='{self.name}', "
            f"PVIs={len(self.pvi_points)}, "
            f"geometry={len(self.geometry_elements)}, "
            f"surfaces={len(self.profsurf_list)})"
        )
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        sta_range = ""
        if self.sta_start is not None and self.sta_end is not None:
            sta_range = f", Sta {self.sta_start:.2f} to {self.sta_end:.2f}"
        
        return (
            f"Profile '{self.name}': "
            f"{len(self.pvi_points)} PVIs, "
            f"{len(self.geometry_elements)} geometry elements, "
            f"{len(self.profsurf_list)} surface profiles"
            f"{sta_range}"
        )
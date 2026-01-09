# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Dict, List, Tuple, Optional
from .arc import Arc
from .tangent import Tangent
from .parabola import Parabola


class Profile:
    """
    LandXML 1.2 vertical profile reader & geometry generator.
    Manages multiple vertical alignments (ProfAlign) and surface profiles (ProfSurf).
    Each uses geometry elements (Tangent, Parabola, Arc).
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
        
        # Reference to parent alignment
        self.parent_alignment = parent_alignment
        
        # Multiple design profiles (ProfAlign) - each has name, PVIs, and geometry
        self.profalign_list = []
        
        # Multiple surface profiles (ProfSurf) - each has name and geometry
        self.profsurf_list = []
        
        # Parse ProfAlign (can be single dict or list)
        if 'ProfAlign' in data:
            profalign_data = data['ProfAlign']
            if isinstance(profalign_data, dict):
                # Single ProfAlign
                self._parse_profalign(profalign_data)
            elif isinstance(profalign_data, list):
                # Multiple ProfAlign
                for pa_data in profalign_data:
                    self._parse_profalign(pa_data)
        
        # Parse ProfSurf (usually a list)
        if 'ProfSurf' in data and data['ProfSurf']:
            if isinstance(data['ProfSurf'], list):
                self._parse_profsurf_list(data['ProfSurf'])
            else:
                # Single ProfSurf as dict
                self._parse_profsurf_list([data['ProfSurf']])
        
        # Compute profile properties
        self._compute_profile_properties()
    
    def _parse_profalign(self, profalign_data: Dict):
        """Parse a single vertical alignment (ProfAlign) and create geometry"""
        
        profalign = {
            'name': profalign_data.get('name', 'Design Profile'),
            'description': profalign_data.get('desc', None),
            'staStart': float(profalign_data['staStart']) if 'staStart' in profalign_data else None,
            'length': float(profalign_data['length']) if 'length' in profalign_data else None,
            'pvi_points': [],
            'geometry': []
        }
        
        raw_geometry = profalign_data.get('geometry', [])
        curves_data = []
        
        # Extract PVI points and curve data
        for geom_data in raw_geometry:
            geom_type = geom_data.get('Type', None)
            
            if geom_type == 'PVI':
                pvi = {
                    'station': float(geom_data['station']),
                    'elevation': float(geom_data['elevation']),
                    'description': geom_data.get('desc', None)
                }
                profalign['pvi_points'].append(pvi)
            
            elif geom_type in ['ParaCurve', 'UnsymParaCurve', 'CircCurve']:
                curves_data.append(geom_data)
        
        # Sort PVI points by station
        profalign['pvi_points'].sort(key=lambda p: p['station'])
        
        if profalign['pvi_points']:
            # Create geometry elements for this ProfAlign
            geometry_elements = self._create_geometry_elements(
                profalign['pvi_points'], 
                curves_data
            )
            profalign['geometry'] = geometry_elements
        
        self.profalign_list.append(profalign)
    
    def _create_geometry_elements(self, pvi_points: List[Dict], curves_data: List[Dict]) -> List:
        """Create geometry elements from PVI points and curve data"""
        
        if len(pvi_points) < 2:
            return []
        
        geometry_elements = []
        
        # Map curves to their PVI positions
        curve_map = {}
        for curve_data in curves_data:
            pvi_data = curve_data.get('pvi', {})
            if pvi_data:
                pvi_station = float(pvi_data['station'])
                for i, pvi in enumerate(pvi_points):
                    if abs(pvi['station'] - pvi_station) < 1e-6:
                        curve_map[i] = curve_data
                        break
        
        # Build geometry elements
        for i in range(len(pvi_points) - 1):
            pvi_curr = pvi_points[i]
            pvi_next = pvi_points[i + 1]
            
            # Calculate grade between PVIs
            sta_diff = pvi_next['station'] - pvi_curr['station']
            elev_diff = pvi_next['elevation'] - pvi_curr['elevation']
            grade = elev_diff / sta_diff if sta_diff != 0 else 0.0
            
            # Check if there's a curve at current PVI
            if i in curve_map:
                curve_data = curve_map[i]
                
                # Get previous grade
                if geometry_elements:
                    prev_elem = geometry_elements[-1]
                    if isinstance(prev_elem, Tangent):
                        prev_grade = prev_elem.grade
                    else:
                        prev_grade = prev_elem.grade_out
                else:
                    prev_grade = grade
                
                # Create curve
                curve = self._create_curve(curve_data, prev_grade, grade)
                
                if curve:
                    # Add tangent before curve if needed
                    if geometry_elements:
                        last_elem = geometry_elements[-1]
                        last_sta_end = last_elem.get_station_range()[1]
                        curve_sta_start = curve.get_station_range()[0]
                        
                        if curve_sta_start > last_sta_end + 1e-6:
                            tangent = Tangent(
                                sta_start=last_sta_end,
                                elev_start=last_elem.get_elevation_at_station(last_sta_end),
                                sta_end=curve_sta_start,
                                elev_end=curve.elev_bvc
                            )
                            geometry_elements.append(tangent)
                    else:
                        # First element is curve
                        curve_sta_start = curve.get_station_range()[0]
                        if pvi_curr['station'] < curve_sta_start - 1e-6:
                            tangent = Tangent(
                                sta_start=pvi_curr['station'],
                                elev_start=pvi_curr['elevation'],
                                sta_end=curve_sta_start,
                                elev_end=curve.elev_bvc
                            )
                            geometry_elements.append(tangent)
                    
                    geometry_elements.append(curve)
                    
                    # Add tangent after curve if needed
                    curve_sta_end = curve.get_station_range()[1]
                    if i + 1 < len(pvi_points) - 1:
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
                                geometry_elements.append(tangent)
                    else:
                        # Last segment
                        if pvi_next['station'] > curve_sta_end + 1e-6:
                            tangent = Tangent(
                                sta_start=curve_sta_end,
                                elev_start=curve.elev_evc,
                                sta_end=pvi_next['station'],
                                elev_end=pvi_next['elevation']
                            )
                            geometry_elements.append(tangent)
            else:
                # No curve - create tangent
                if not geometry_elements:
                    tangent = Tangent(
                        sta_start=pvi_curr['station'],
                        elev_start=pvi_curr['elevation'],
                        sta_end=pvi_next['station'],
                        elev_end=pvi_next['elevation']
                    )
                    geometry_elements.append(tangent)
                else:
                    last_elem = geometry_elements[-1]
                    last_sta_end = last_elem.get_station_range()[1]
                    
                    if last_sta_end < pvi_next['station'] - 1e-6:
                        tangent = Tangent(
                            sta_start=last_sta_end,
                            elev_start=last_elem.get_elevation_at_station(last_sta_end),
                            sta_end=pvi_next['station'],
                            elev_end=pvi_next['elevation']
                        )
                        geometry_elements.append(tangent)
        
        return geometry_elements
    
    def _create_curve(self, curve_data: Dict, prev_grade: float, next_grade: float):
        """Create appropriate curve object"""
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
        """Parse surface profiles and convert to Tangent geometry"""
        
        for profsurf_data in profsurf_list:
            profsurf = {
                'name': profsurf_data.get('name', 'Surface Profile'),
                'description': profsurf_data.get('desc', None),
                'surfType': profsurf_data.get('surfType', None),
                'geometry': []
            }
            
            # Parse and sort points
            points = profsurf_data.get('points', [])
            if len(points) < 2:
                continue
            
            sorted_points = sorted(points, key=lambda p: float(p[0]))
            
            # Create tangent segments between consecutive points
            for i in range(len(sorted_points) - 1):
                sta1, elev1 = float(sorted_points[i][0]), float(sorted_points[i][1])
                sta2, elev2 = float(sorted_points[i + 1][0]), float(sorted_points[i + 1][1])
                
                tangent = Tangent(
                    sta_start=sta1,
                    elev_start=elev1,
                    sta_end=sta2,
                    elev_end=elev2,
                    desc=f"{profsurf['name']} segment {i+1}"
                )
                profsurf['geometry'].append(tangent)
            
            self.profsurf_list.append(profsurf)
    
    def _compute_profile_properties(self):
        """Compute overall profile properties"""
        
        # Determine profile station range from all profiles
        all_stations = []
        
        for profalign in self.profalign_list:
            if profalign['geometry']:
                all_stations.append(profalign['geometry'][0].get_station_range()[0])
                all_stations.append(profalign['geometry'][-1].get_station_range()[1])
        
        for profsurf in self.profsurf_list:
            if profsurf['geometry']:
                all_stations.append(profsurf['geometry'][0].get_station_range()[0])
                all_stations.append(profsurf['geometry'][-1].get_station_range()[1])
        
        if all_stations:
            if self.sta_start is None:
                self.sta_start = min(all_stations)
            if self.sta_end is None:
                self.sta_end = max(all_stations)
    
    def get_elevation_at_station(self, station: float, profalign_name: Optional[str] = None) -> Optional[float]:
        """
        Get design elevation at station from a specific ProfAlign.
        
        Args:
            station: Station to query
            profalign_name: Name of ProfAlign (uses first if None)
        """
        profalign = self._select_profalign(profalign_name)
        if not profalign:
            return None
        
        for elem in profalign['geometry']:
            sta_start, sta_end = elem.get_station_range()
            if sta_start <= station <= sta_end:
                return elem.get_elevation_at_station(station)
        return None
    
    def get_grade_at_station(self, station: float, profalign_name: Optional[str] = None) -> Optional[float]:
        """
        Get design grade at station from a specific ProfAlign.
        
        Args:
            station: Station to query
            profalign_name: Name of ProfAlign (uses first if None)
        """
        profalign = self._select_profalign(profalign_name)
        if not profalign:
            return None
        
        for elem in profalign['geometry']:
            sta_start, sta_end = elem.get_station_range()
            if sta_start <= station <= sta_end:
                return elem.get_grade_at_station(station)
        return None
    
    def get_surface_elevation_at_station(self, station: float, surface_name: Optional[str] = None) -> Optional[float]:
        """Get surface elevation at station"""
        profsurf = self._select_surface(surface_name)
        if not profsurf:
            return None
        
        for tangent in profsurf['geometry']:
            sta_start, sta_end = tangent.get_station_range()
            if sta_start <= station <= sta_end:
                return tangent.get_elevation_at_station(station)
        return None
    
    def get_surface_grade_at_station(self, station: float, surface_name: Optional[str] = None) -> Optional[float]:
        """Get surface grade at station"""
        profsurf = self._select_surface(surface_name)
        if not profsurf:
            return None
        
        for tangent in profsurf['geometry']:
            sta_start, sta_end = tangent.get_station_range()
            if sta_start <= station <= sta_end:
                return tangent.get_grade_at_station(station)
        return None
    
    def _select_profalign(self, profalign_name: Optional[str] = None) -> Optional[Dict]:
        """Helper to select ProfAlign by name"""
        if not self.profalign_list:
            return None
        
        if profalign_name:
            return next((pa for pa in self.profalign_list if pa['name'] == profalign_name), None)
        return self.profalign_list[0]
    
    def _select_surface(self, surface_name: Optional[str] = None) -> Optional[Dict]:
        """Helper to select surface profile by name"""
        if not self.profsurf_list:
            return None
        
        if surface_name:
            return next((ps for ps in self.profsurf_list if ps['name'] == surface_name), None)
        return self.profsurf_list[0]
    
    def get_cut_fill_at_station(self, station: float, 
                                profalign_name: Optional[str] = None,
                                surface_name: Optional[str] = None) -> Optional[float]:
        """Calculate cut/fill (design - surface). Positive = fill, negative = cut"""
        design_elev = self.get_elevation_at_station(station, profalign_name)
        surface_elev = self.get_surface_elevation_at_station(station, surface_name)
        
        if design_elev is None or surface_elev is None:
            return None
        
        return design_elev - surface_elev
    
    def generate_profile_points(self, step: float,
                               profalign_name: Optional[str] = None,
                               include_surface: bool = False,
                               surface_name: Optional[str] = None,
                               include_grade: bool = False) -> List[Tuple]:
        """Generate profile points at regular intervals for a specific ProfAlign"""
        profalign = self._select_profalign(profalign_name)
        if not profalign or not profalign['geometry']:
            return []
        
        sta_start = profalign['geometry'][0].get_station_range()[0]
        sta_end = profalign['geometry'][-1].get_station_range()[1]
        
        points = []
        current_station = sta_start
        
        while current_station <= sta_end:
            design_elev = self.get_elevation_at_station(current_station, profalign_name)
            
            if design_elev is not None:
                if include_surface and include_grade:
                    design_grade = self.get_grade_at_station(current_station, profalign_name)
                    surface_elev = self.get_surface_elevation_at_station(current_station, surface_name)
                    surface_grade = self.get_surface_grade_at_station(current_station, surface_name)
                    points.append((current_station, design_elev, design_grade, surface_elev, surface_grade))
                elif include_surface:
                    surface_elev = self.get_surface_elevation_at_station(current_station, surface_name)
                    points.append((current_station, design_elev, surface_elev))
                elif include_grade:
                    design_grade = self.get_grade_at_station(current_station, profalign_name)
                    points.append((current_station, design_elev, design_grade))
                else:
                    points.append((current_station, design_elev))
            
            current_station += step
        
        return points
    
    def generate_surface_points(self, step: float, surface_name: Optional[str] = None) -> List[Tuple[float, float]]:
        """Generate surface profile points"""
        profsurf = self._select_surface(surface_name)
        if not profsurf or not profsurf['geometry']:
            return []
        
        sta_start = profsurf['geometry'][0].get_station_range()[0]
        sta_end = profsurf['geometry'][-1].get_station_range()[1]
        
        points = []
        current_station = sta_start
        
        while current_station <= sta_end:
            elev = self.get_surface_elevation_at_station(current_station, surface_name)
            if elev is not None:
                points.append((current_station, elev))
            current_station += step
        
        return points
    
    def get_profalign_names(self) -> List[str]:
        """Return all ProfAlign names"""
        return [pa['name'] for pa in self.profalign_list]
    
    def get_surface_names(self) -> List[str]:
        """Return all surface profile names"""
        return [ps['name'] for ps in self.profsurf_list]
    
    def get_pvi_points(self, profalign_name: Optional[str] = None) -> List[Dict]:
        """Return PVI points for a specific ProfAlign"""
        profalign = self._select_profalign(profalign_name)
        return profalign['pvi_points'].copy() if profalign else []
    
    def get_geometry_elements(self, profalign_name: Optional[str] = None) -> List:
        """Return geometry elements for a specific ProfAlign"""
        profalign = self._select_profalign(profalign_name)
        return profalign['geometry'].copy() if profalign else []
    
    def get_surface_geometry_elements(self, surface_name: Optional[str] = None) -> List[Tangent]:
        """Return geometry elements for a surface profile"""
        profsurf = self._select_surface(surface_name)
        return profsurf['geometry'].copy() if profsurf else []
    
    def get_profalign_count(self) -> int:
        """Return number of ProfAlign profiles"""
        return len(self.profalign_list)
    
    def get_surface_count(self) -> int:
        """Return number of surface profiles"""
        return len(self.profsurf_list)
    
    def get_sta_start(self) -> Optional[float]:
        """Return profile start station"""
        return self.sta_start
    
    def get_sta_end(self) -> Optional[float]:
        """Return profile end station"""
        return self.sta_end
    
    def to_dict(self) -> Dict:
        """Export profile properties"""
        return {
            'name': self.name,
            'desc': self.description,
            'staStart': self.sta_start,
            'staEnd': self.sta_end,
            'alignmentName': self.alignment_name,
            'profalignCount': len(self.profalign_list),
            'surfaceProfileCount': len(self.profsurf_list),
            'profaligns': [
                {
                    'name': pa['name'],
                    'description': pa['description'],
                    'pviCount': len(pa['pvi_points']),
                    'geometryCount': len(pa['geometry']),
                    'pviPoints': pa['pvi_points'],
                    'geometry': [elem.to_dict() for elem in pa['geometry']]
                }
                for pa in self.profalign_list
            ],
            'surfaces': [
                {
                    'name': ps['name'],
                    'description': ps['description'],
                    'surfType': ps['surfType'],
                    'geometryCount': len(ps['geometry']),
                    'geometry': [elem.to_dict() for elem in ps['geometry']]
                }
                for ps in self.profsurf_list
            ]
        }
    
    def __repr__(self) -> str:
        return (
            f"Profile(name='{self.name}', "
            f"ProfAligns={len(self.profalign_list)}, "
            f"Surfaces={len(self.profsurf_list)})"
        )
    
    def __str__(self) -> str:
        sta_range = ""
        if self.sta_start is not None and self.sta_end is not None:
            sta_range = f", Sta {self.sta_start:.2f} to {self.sta_end:.2f}"
        
        return (
            f"Profile '{self.name}': "
            f"{len(self.profalign_list)} design profile(s), "
            f"{len(self.profsurf_list)} surface profile(s)"
            f"{sta_range}"
        )
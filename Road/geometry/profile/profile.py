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
        self.sta_start = float(data['staStart']) if 'staStart' in data and data['staStart'] is not None else None
        self.sta_end = float(data['staEnd']) if 'staEnd' in data and data['staEnd'] is not None else None
        self.alignment_name = data.get('alignmentName', None)
        
        # Reference to parent alignment
        self.parent_alignment = parent_alignment
        
        # Multiple design profiles (ProfAlign) - each has name, PVIs, and geometry
        self.profalign_list = []
        
        # Multiple surface profiles (ProfSurf) - each has name and geometry
        self.profsurf_list = []
        
        # Parse ProfSurf
        profsurfs_data = data['ProfSurf']
        for ps_data in profsurfs_data:
            self._parse_profsurf(ps_data)

        # Parse ProfAlign
        profaligns_data = data['ProfAlign']
        for pa_data in profaligns_data:
            self._parse_profalign(pa_data)
        
        # Compute profile properties
        self._compute_profile_properties()
    
    def _parse_profsurf(self, profsurf_data: Dict):
        """Parse surface profiles and convert to Tangent geometry"""
    
        # Parse and sort points
        points = profsurf_data.get('points', [])
        if len(points) < 2:
            return
        
        profsurf = {
            'name': profsurf_data.get('name', 'Surface Profile'),
            'description': profsurf_data.get('desc', None),
            'points': points,
            'elements': []
        }
        
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
            profsurf['elements'].append(tangent)
        
        self.profsurf_list.append(profsurf)
        
    def _parse_profalign(self, profalign_data: Dict):
        """Parse a single vertical alignment (ProfAlign) and create geometry"""
        
        geom_data = profalign_data.get('geometry', [])
        profalign = {
            'name': profalign_data.get('name', 'Design Profile'),
            'description': profalign_data.get('desc', None),
            'staStart': float(profalign_data['staStart']) if 'staStart' in profalign_data and profalign_data['staStart'] is not None else None,
            'length': float(profalign_data['length']) if 'length' in profalign_data and profalign_data['length'] is not None else None,
            'elements': self._create_geometry_elements(geom_data),
            'geometry': geom_data
        }

        self.profalign_list.append(profalign)

    def _create_geometry_elements(self, geom_data: List[Dict]) -> List:
        """Create geometry elements (Tangent, Parabola, Arc) from geometry data"""
        elements = []
        # Extract PVI points and curve data
        for i in range(1, len(geom_data) - 1):
            pvi_prev = geom_data[i - 1]['pvi']
            pvi_curr = geom_data[i]['pvi']
            pvi_next = geom_data[i + 1]['pvi']
            
            # Calculate grade in
            sta_diff_in = pvi_curr['station'] - pvi_prev['station']
            elev_diff_in = pvi_curr['elevation'] - pvi_prev['elevation']
            grade_in = elev_diff_in / sta_diff_in if sta_diff_in != 0 else 0.0

            # Calculate grade out
            sta_diff_out = pvi_next['station'] - pvi_curr['station']
            elev_diff_out = pvi_next['elevation'] - pvi_curr['elevation']
            grade_out = elev_diff_out / sta_diff_out if sta_diff_out != 0 else 0.0

            # Check if there's a curve at current PVI
            if 'type' in geom_data[i]:
                curve = self._create_curve(geom_data[i], grade_in, grade_out)
                
                if curve:
                    # Add tangent before curve if needed
                    if elements:
                        last_elem = elements[-1]
                        last_sta_end = last_elem.get_station_range()[1]
                        curve_sta_start = curve.get_station_range()[0]
                        
                        if curve_sta_start > last_sta_end + 1e-6:
                            tangent = Tangent(
                                sta_start=last_sta_end,
                                elev_start=last_elem.get_elevation_at_station(last_sta_end),
                                sta_end=curve_sta_start,
                                elev_end=curve.elev_bvc
                            )
                            elements.append(tangent)
                    else:
                        # Add tangent for first segment if needed
                        curve_sta_start = curve.get_station_range()[0]
                        if pvi_prev['station'] < curve_sta_start - 1e-6:
                            tangent = Tangent(
                                sta_start=pvi_prev['station'],
                                elev_start=pvi_prev['elevation'],
                                sta_end=curve_sta_start,
                                elev_end=curve.elev_bvc
                            )
                            elements.append(tangent)
                    
                    elements.append(curve)
                    
            else:
                # No curve - create tangent
                if not elements:
                    tangent = Tangent(
                        sta_start=pvi_prev['station'],
                        elev_start=pvi_prev['elevation'],
                        sta_end=pvi_curr['station'],
                        elev_end=pvi_curr['elevation']
                    )
                    elements.append(tangent)
                else:
                    last_elem = elements[-1]
                    last_sta_end = last_elem.get_station_range()[1]
                    
                    if last_sta_end < pvi_next['station'] - 1e-6:
                        tangent = Tangent(
                            sta_start=last_sta_end,
                            elev_start=last_elem.get_elevation_at_station(last_sta_end),
                            sta_end=pvi_next['station'],
                            elev_end=pvi_next['elevation']
                        )
                        elements.append(tangent)
        
        return elements
    
    def _create_curve(self, curve_data: Dict, grade_in: float, grade_out: float):
        """Create appropriate curve object"""
        geom_type = curve_data.get('type')
        
        try:
            if geom_type in ['ParaCurve', 'UnsymParaCurve']:
                return Parabola(curve_data, grade_in, grade_out)
            elif geom_type == 'CircCurve':
                return Arc(curve_data, grade_in, grade_out)
        except Exception as e:
            print(f"Warning: Failed to create curve: {str(e)}")
            return None
    
    def _compute_profile_properties(self):
        """Compute overall profile properties"""
        
        # Determine profile station range from all profiles
        all_stations = []
        
        for profalign in self.profalign_list:
            if profalign['elements']:
                all_stations.append(profalign['elements'][0].get_station_range()[0])
                all_stations.append(profalign['elements'][-1].get_station_range()[1])

        for profsurf in self.profsurf_list:
            if profsurf['elements']:
                all_stations.append(profsurf['elements'][0].get_station_range()[0])
                all_stations.append(profsurf['elements'][-1].get_station_range()[1])
        
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
        
        for elem in profalign['elements']:
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
        
        for elem in profalign['elements']:
            sta_start, sta_end = elem.get_station_range()
            if sta_start <= station <= sta_end:
                return elem.get_grade_at_station(station)
        return None
    
    def get_surface_elevation_at_station(self, station: float, surface_name: Optional[str] = None) -> Optional[float]:
        """Get surface elevation at station"""
        profsurf = self._select_surface(surface_name)
        if not profsurf:
            return None
        
        for tangent in profsurf['elements']:
            sta_start, sta_end = tangent.get_station_range()
            if sta_start <= station <= sta_end:
                return tangent.get_elevation_at_station(station)
        return None
    
    def get_surface_grade_at_station(self, station: float, surface_name: Optional[str] = None) -> Optional[float]:
        """Get surface grade at station"""
        profsurf = self._select_surface(surface_name)
        if not profsurf:
            return None
        
        for tangent in profsurf['elements']:
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
        if not profalign or not profalign['elements']:
            return []
        
        sta_start = profalign['elements'][0].get_station_range()[0]
        sta_end = profalign['elements'][-1].get_station_range()[1]
        
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
        if not profsurf or not profsurf['elements']:
            return []
        
        sta_start = profsurf['elements'][0].get_station_range()[0]
        sta_end = profsurf['elements'][-1].get_station_range()[1]
        
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
        return profalign['elements'].copy() if profalign else []
    
    def get_surface_geometry_elements(self, surface_name: Optional[str] = None) -> List[Tangent]:
        """Return geometry elements for a surface profile"""
        profsurf = self._select_surface(surface_name)
        return profsurf['elements'].copy() if profsurf else []
    
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
            'ProfAlign': [{k: v for k, v in pa.items() if k != 'elements'} for pa in self.profalign_list],
            'ProfSurf': [{k: v for k, v in ps.items() if k != 'elements'} for ps in self.profsurf_list]
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
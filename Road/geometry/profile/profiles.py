# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Dict, List, Optional
from.profile import Profile


class Profiles:
    """
    LandXML 1.2 vertical profile reader & geometry generator.
    Manages multiple vertical alignments (ProfAlign) and surface profiles (ProfSurf).
    Each uses geometry elements (Tangent, Parabola, Arc).
    """

    def __init__(self, data: Dict=None):
        """
        Initialize profile from LandXML data dictionary.
        
        Args:
            data: Dictionary containing profile data
            parent_alignment: Reference to parent Alignment object (optional)
        """
        
        # Profile metadata
        self.name = data.get('name', None)
        self.description = data.get('desc', None)
        self.start_station = data.get('staStart', None)
        self.data = data
        
        self.design_profiles: List[Profile] = []
        self.surface_profiles: List[Profile] = []
        self._parse_profiles(data)
    
    def _parse_profiles(self, data: Dict):
        """Parse profiles from LandXML data dictionary"""
        for profalign_data in data.get('ProfAlign', []):
            name = profalign_data.get('name', 'Design Profile'),
            description = profalign_data.get('desc', None),
            geom_data = profalign_data.get('geometry', [])
            pa = Profile(name, description, geom_data)
            self.design_profiles.append(pa)

        for profsurf_data in data.get('ProfSurf', []):
            name = profsurf_data.get('name', 'Surface Profile'),
            description = profsurf_data.get('desc', None),
            points = profsurf_data.get('points', [])
            geom_data = [{'pvi': {'station': float(pt[0]), 'elevation': float(pt[1])}} for pt in points]
            ps = Profile(name, description, geom_data)
            self.surface_profiles.append(ps)
    
    def get_elevation_at_station(self, profile_name: str, station: float = 0.0) -> Optional[float]:
        """
        Get design elevation at station from specified profile.
        
        Args:
            station: Station along alignment
            profalign_name: Name of the ProfAlign to query (optional)
        """
        profile = None
        for pr in self.design_profiles + self.surface_profiles:
            if pr.name == profile_name:
                profile = pr
                break
            
        if profile is None:
            return None
        
        return profile.get_elevation_at_station(station)
    
    def get_grade_at_station(self, profile_name: str, station: float = 0.0) -> Optional[float]:
        """
        Get design grade at station from specified profile.
        
        Args:
            station: Station along alignment
            profalign_name: Name of the ProfAlign to query (optional)
        """
        profile = None
        for pr in self.design_profiles + self.surface_profiles:
            if pr.name == profile_name:
                profile = pr
                break
            
        if profile is None:
            return None
        
        return profile.get_grade_at_station(station)
    
    def get_profile_by_name(self, profile_name: str) -> Optional[Profile]:
        """Return profile by name"""
        for pr in self.design_profiles + self.surface_profiles:
            if pr.name == profile_name:
                return pr
        return None
    
    def get_profalign_names(self) -> List[str]:
        """Return all ProfAlign names"""
        return [dp.name for dp in self.design_profiles]
    
    def get_surface_names(self) -> List[str]:
        """Return all surface profile names"""
        return [sp.name for sp in self.surface_profiles]
    
    def get_sta_start(self) -> Optional[float]:
        """Return profile start station"""
        return self.start_station
    
    def to_dict(self) -> Dict:
        """Export profile properties"""
        return {
            'name': self.name,
            'desc': self.description,
            'staStart': self.start_station,
            'ProfAlign': [dp.data for dp in self.design_profiles],
            'ProfSurf': [sp.data for sp in self.surface_profiles]
        }

    def __repr__(self) -> str:
        return (
            f"Profile(name='{self.name}', "
            f"Designs={len(self.design_profiles)}, "
            f"Surfaces={len(self.surface_profiles)})"
        )
    
    def __str__(self) -> str:
        return (
            f"Profile '{self.name}': "
            f"{len(self.design_profiles)} design profile(s), "
            f"{len(self.surface_profiles)} surface profile(s)"
        )
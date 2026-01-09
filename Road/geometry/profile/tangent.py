# SPDX-License-Identifier: LGPL-2.1-or-later

from .geometry import ProfileGeometry
from typing import Dict, Tuple


class Tangent(ProfileGeometry):
    """
    Vertical tangent (straight grade line).
    Represents constant grade section between vertical curves.
    """

    def __init__(self, sta_start: float, elev_start: float, sta_end: float, elev_end: float, desc: str = None):
        """
        Initialize tangent from start and end points.
        
        Args:
            sta_start: Start station
            elev_start: Start elevation
            sta_end: End station
            elev_end: End elevation
            desc: Optional description
        """
        super().__init__({'Type': 'Tangent', 'desc': desc})
        
        self.sta_start = float(sta_start)
        self.elev_start = float(elev_start)
        self.sta_end = float(sta_end)
        self.elev_end = float(elev_end)
        
        # Calculate grade (constant)
        if self.sta_end != self.sta_start:
            self.grade = (self.elev_end - self.elev_start) / (self.sta_end - self.sta_start)
        else:
            self.grade = 0.0
        
        self.length = self.sta_end - self.sta_start
    
    def get_elevation_at_station(self, station: float) -> float:
        """Calculate elevation at station using linear interpolation"""
        if station < self.sta_start or station > self.sta_end:
            raise ValueError(f"Station {station} outside tangent range [{self.sta_start:.2f}, {self.sta_end:.2f}]")
        
        # Linear: elev = elev_start + grade * (sta - sta_start)
        elevation = self.elev_start + self.grade * (station - self.sta_start)
        
        return elevation
    
    def get_grade_at_station(self, station: float) -> float:
        """Return constant grade"""
        if station < self.sta_start or station > self.sta_end:
            raise ValueError(f"Station {station} outside tangent range [{self.sta_start:.2f}, {self.sta_end:.2f}]")
        
        return self.grade
    
    def get_station_range(self) -> Tuple[float, float]:
        """Get tangent start and end stations"""
        return (self.sta_start, self.sta_end)
    
    def to_dict(self) -> Dict:
        """Export tangent properties"""
        return {
            'Type': 'Tangent',
            'staStart': self.sta_start,
            'elevStart': self.elev_start,
            'staEnd': self.sta_end,
            'elevEnd': self.elev_end,
            'grade': self.grade,
            'length': self.length,
            'description': self.description
        }
    
    def __repr__(self) -> str:
        return f"Tangent(sta {self.sta_start:.2f}-{self.sta_end:.2f}, grade={self.grade*100:.2f}%)"
    
    def __str__(self) -> str:
        return f"Tangent: L={self.length:.2f}m, Grade={self.grade*100:.2f}%"
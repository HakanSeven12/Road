# SPDX-License-Identifier: LGPL-2.1-or-later

from .geometry import ProfileGeometry
from typing import Dict, Tuple
import math


class Arc(ProfileGeometry):
    """
    Circular vertical curve.
    Less common than parabolic, but used in some standards.
    """

    def __init__(self, data: Dict, prev_grade: float, next_grade: float):
        """
        Initialize circular vertical curve.
        
        Args:
            data: Dictionary containing:
                - length: float (required)
                - radius: float (optional)
                - pvi: dict with station/elevation (required)
                - desc: str (optional)
            prev_grade: Grade coming into curve
            next_grade: Grade going out of curve
        """
        super().__init__(data)
        
        if 'length' not in data:
            raise ValueError("Arc must have 'length'")
        
        self.length = float(data['length'])
        self.radius = float(data['radius']) if 'radius' in data else None
        
        # PVI point
        pvi_data = data.get('pvi', {})
        if not pvi_data:
            raise ValueError("Arc must have 'pvi' data")
        
        self.pvi_station = float(pvi_data['station'])
        self.pvi_elevation = float(pvi_data['elevation'])
        
        # Calculate curve start and end
        self.sta_start = self.pvi_station - self.length / 2
        self.sta_end = self.pvi_station + self.length / 2
        
        # Store grades
        self.grade_in = prev_grade
        self.grade_out = next_grade
        self.grade_change = self.grade_out - self.grade_in
        
        # Calculate radius if not provided
        if self.radius is None and self.grade_change != 0:
            delta_angle = math.atan(self.grade_change)
            self.radius = self.length / delta_angle if delta_angle != 0 else float('inf')
        
        # Calculate BVC and EVC elevations
        self.elev_bvc = self.pvi_elevation - (self.length / 2) * self.grade_in
        self.elev_evc = self.pvi_elevation + (self.length / 2) * self.grade_out
    
    def get_elevation_at_station(self, station: float) -> float:
        """
        Calculate elevation using parabolic approximation.
        (True circular formula is complex; parabolic is very close for small grades)
        """
        if station < self.sta_start or station > self.sta_end:
            raise ValueError(f"Station {station} outside curve range")
        
        # Use parabolic approximation
        x = station - self.sta_start
        elevation = self.elev_bvc + self.grade_in * x + (self.grade_change * x * x) / (2 * self.length)
        
        return elevation
    
    def get_grade_at_station(self, station: float) -> float:
        """Calculate grade at station"""
        if station < self.sta_start or station > self.sta_end:
            raise ValueError(f"Station {station} outside curve range")
        
        x = station - self.sta_start
        grade = self.grade_in + (self.grade_change * x) / self.length
        
        return grade
    
    def get_station_range(self) -> Tuple[float, float]:
        """Get curve range"""
        return (self.sta_start, self.sta_end)
    
    def to_dict(self) -> Dict:
        """Export curve properties"""
        return {
            'Type': 'CircCurve',
            'length': self.length,
            'radius': self.radius,
            'pvi': {
                'station': self.pvi_station,
                'elevation': self.pvi_elevation
            },
            'staStart': self.sta_start,
            'staEnd': self.sta_end,
            'gradeIn': self.grade_in,
            'gradeOut': self.grade_out,
            'description': self.description
        }
    
    def __repr__(self) -> str:
        return f"Arc(L={self.length:.2f}m, R={self.radius:.2f}m)"
    
    def __str__(self) -> str:
        return f"Circular Arc: L={self.length:.2f}m, R={self.radius:.2f}m"
# SPDX-License-Identifier: LGPL-2.1-or-later

from .geometry import ProfileGeometry
from typing import Dict, Tuple
import math


class Arc(ProfileGeometry):
    """
    Circular vertical curve.
    Less common than parabolic, but used in some standards.
    """
    def __init__(self, data: Dict, grade_in: float, grade_out: float):
        """
        Initialize circular vertical curve.
        
        Args:
            data: Dictionary containing:
                - length: float (optional if radius given)
                - radius: float (optional if length given)
                - pvi: dict with station/elevation (required)
                - desc: str (optional)
            grade_in: Grade coming into curve
            grade_out: Grade going out of curve
        """
        super().__init__(data)
        
        # At least one of length or radius must be provided
        if 'length' not in data and 'radius' not in data:
            raise ValueError("CircCurve must have either 'length' or 'radius'")
        
        # PVI point
        pvi_data = data.get('pvi', {})
        if not pvi_data:
            raise ValueError("Arc must have 'pvi' data")
        
        self.pvi_station = float(pvi_data['station'])
        self.pvi_elevation = float(pvi_data['elevation'])
        
        # Store grades
        self.grade_in = grade_in
        self.grade_out = grade_out
        self.grade_change = self.grade_out - self.grade_in
        
        # Calculate deflection angle (exact calculation using arctan)
        # Δ = arctan(g2) - arctan(g1) = angle change in radians
        delta_angle = math.atan(self.grade_out) - math.atan(self.grade_in)
        
        # Calculate length and radius relationship
        # For circular curve: L = R * Δ
        
        if 'length' in data and 'radius' in data:
            # Both provided, use them directly
            self.length = float(data['length'])
            self.radius = float(data['radius'])
        elif 'length' in data:
            # Only length provided, calculate radius
            self.length = float(data['length'])
            if abs(delta_angle) > 1e-10:
                # R = L / Δ
                self.radius = self.length / abs(delta_angle)
            else:
                self.radius = float('inf')
        else:
            # Only radius provided, calculate length
            self.radius = float(data['radius'])
            # L = R * Δ
            self.length = self.radius * abs(delta_angle)
        
        # Calculate curve start and end
        self.sta_start = self.pvi_station - self.length / 2
        self.sta_end = self.pvi_station + self.length / 2
        
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
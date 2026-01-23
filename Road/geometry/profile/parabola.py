# SPDX-License-Identifier: LGPL-2.1-or-later

from .geometry import ProfileGeometry   
from typing import Dict, Tuple, Optional


class Parabola(ProfileGeometry):
    """
    Parabolic vertical curve (symmetric or asymmetric).
    Used for smooth transitions between grade lines.
    """

    def __init__(self, data: Dict, grade_in: float, grade_out: float):
        """
        Initialize parabolic curve.
        
        Args:
            data: Dictionary containing:
                - length: float (total curve length, required)
                - lengthIn: float (length before PVI, optional - if not provided, symmetric)
                - lengthOut: float (length after PVI, optional - if not provided, symmetric)
                - pvi: dict with station/elevation (required from Civil3D format)
                - desc: str (optional)
            grade_in: Grade coming into curve (from previous element)
            grade_out: Grade going out of curve (to next element)
        """
        super().__init__(data)
        
        if 'length' not in data:
            raise ValueError("Parabola must have 'length'")
        
        self.length = float(data['length'])
        
        # Check if asymmetric
        self.is_asymmetric = 'lengthIn' in data or 'lengthOut' in data
        
        if self.is_asymmetric:
            # Asymmetric curve
            self.length_in = float(data.get('lengthIn', self.length / 2))
            self.length_out = float(data.get('lengthOut', self.length / 2))
        else:
            # Symmetric curve
            self.length_in = self.length / 2
            self.length_out = self.length / 2
        
        # PVI point
        pvi_data = data.get('pvi', {})
        if not pvi_data:
            raise ValueError("Parabola must have 'pvi' data")
        
        self.pvi_station = float(pvi_data['station'])
        self.pvi_elevation = float(pvi_data['elevation'])
        
        # Calculate curve start and end
        self.sta_start = self.pvi_station - self.length_in
        self.sta_end = self.pvi_station + self.length_out
        
        # Store grades
        self.grade_in = grade_in
        self.grade_out = grade_out
        self.grade_change = self.grade_out - self.grade_in
        
        # K value (rate of vertical curvature)
        self.k_value = self.length / abs(self.grade_change) if self.grade_change != 0 else float('inf')
        
        # Calculate elevations at curve BVC (beginning) and EVC (end)
        self.elev_bvc = self.pvi_elevation - self.length_in * self.grade_in
        self.elev_evc = self.pvi_elevation + self.length_out * self.grade_out
    
    def get_elevation_at_station(self, station: float) -> float:
        """
        Calculate elevation at given station using parabolic formula.
        Handles both symmetric and asymmetric curves.
        
        Args:
            station: Station to query
            
        Returns:
            Elevation at station
        """
        if station < self.sta_start or station > self.sta_end:
            raise ValueError(f"Station {station} outside curve range [{self.sta_start:.2f}, {self.sta_end:.2f}]")
        
        if not self.is_asymmetric:
            # Symmetric parabola
            x = station - self.sta_start
            elevation = self.elev_bvc + self.grade_in * x + (self.grade_change * x * x) / (2 * self.length)
        else:
            # Asymmetric parabola
            if station <= self.pvi_station:
                # Before PVI - use incoming portion
                x = station - self.sta_start
                elevation = self.elev_bvc + self.grade_in * x + (self.grade_change * x * x) / (2 * self.length)
            else:
                # After PVI - use outgoing portion
                x = station - self.pvi_station
                elevation = self.pvi_elevation + self.grade_out * x - (self.grade_change * (self.length_out - x) ** 2) / (2 * self.length)
        
        return elevation
    
    def get_grade_at_station(self, station: float) -> float:
        """
        Calculate grade at given station.
        Grade varies linearly along the curve.
        
        Args:
            station: Station to query
            
        Returns:
            Grade (slope) as decimal
        """
        if station < self.sta_start or station > self.sta_end:
            raise ValueError(f"Station {station} outside curve range [{self.sta_start:.2f}, {self.sta_end:.2f}]")
        
        if not self.is_asymmetric:
            # Symmetric curve
            x = station - self.sta_start
            grade = self.grade_in + (self.grade_change * x) / self.length
        else:
            # Asymmetric curve
            if station <= self.pvi_station:
                x = station - self.sta_start
                grade = self.grade_in + (self.grade_change * x) / self.length
            else:
                x = station - self.pvi_station
                grade = self.grade_out - (self.grade_change * (self.length_out - x)) / self.length
        
        return grade
    
    def get_station_range(self) -> Tuple[float, float]:
        """Get curve start and end stations"""
        return (self.sta_start, self.sta_end)
    
    def get_high_low_point(self) -> Optional[Tuple[float, float]]:
        """
        Find high or low point on curve (where grade = 0).
        
        Returns:
            (station, elevation) of turning point, or None if no turning point
        """
        # Turning point occurs where grade = 0
        # For symmetric: 0 = g1 + (g2-g1)*x/L → x = -g1*L/(g2-g1)
        
        if abs(self.grade_change) < 1e-10:
            # No grade change, no turning point
            return None
        
        if not self.is_asymmetric:
            # Symmetric curve
            x = -self.grade_in * self.length / self.grade_change
            
            if 0 <= x <= self.length:
                station = self.sta_start + x
                elevation = self.get_elevation_at_station(station)
                return (station, elevation)
        else:
            # Asymmetric curve - check both portions
            # Before PVI
            x = -self.grade_in * self.length / self.grade_change
            if 0 <= x <= self.length_in:
                station = self.sta_start + x
                elevation = self.get_elevation_at_station(station)
                return (station, elevation)
            
            # After PVI
            # Need to solve for where grade = 0 in outgoing portion
            # This is more complex for asymmetric curves
            pass
        
        return None
    
    def to_dict(self) -> Dict:
        """Export curve properties"""
        result = {
            'Type': 'ParaCurve' if not self.is_asymmetric else 'UnsymParaCurve',
            'length': self.length,
            'pvi': {
                'station': self.pvi_station,
                'elevation': self.pvi_elevation
            },
            'staStart': self.sta_start,
            'staEnd': self.sta_end,
            'gradeIn': self.grade_in,
            'gradeOut': self.grade_out,
            'gradeChange': self.grade_change,
            'kValue': self.k_value,
            'elevBVC': self.elev_bvc,
            'elevEVC': self.elev_evc,
            'description': self.description
        }
        
        if self.is_asymmetric:
            result['lengthIn'] = self.length_in
            result['lengthOut'] = self.length_out
        
        return result
    
    def __repr__(self) -> str:
        if self.is_asymmetric:
            return f"Parabola(L_in={self.length_in:.2f}m, L_out={self.length_out:.2f}m, asymmetric)"
        else:
            return f"Parabola(L={self.length:.2f}m, K={self.k_value:.1f})"
    
    def __str__(self) -> str:
        curve_type = "Asymmetric" if self.is_asymmetric else "Symmetric"
        return (
            f"{curve_type} Parabola: L={self.length:.2f}m, "
            f"Grade: {self.grade_in*100:.2f}% → {self.grade_out*100:.2f}%"
        )
# SPDX-License-Identifier: LGPL-2.1-or-later

import math
from abc import ABC, abstractmethod
from typing import Dict, Tuple, List


class Geometry(ABC):
    """
    Abstract base class for LandXML 1.2 geometry elements (Line, Curve, Spiral).
    Defines common interface and shared functionality for all alignment geometry.
    """

    def __init__(self, data: Dict):
        # Common attributes for all geometry types
        self.name = data.get('name', None)
        self.description = data.get('desc', None)
        self.sta_start = float(data['staStart']) if 'staStart' in data else None
        self.start_point = data.get('Start', None)
        self.end_point = data.get('End', None)
        
        if self.start_point is None or self.end_point is None:
            raise ValueError("Start and End coordinates must be provided")
    
    @abstractmethod
    def compute_missing_values(self):
        """Calculate all missing optional attributes from geometry"""
        pass
    
    @abstractmethod
    def get_point_at_distance(self, s: float) -> Tuple[float, float]:
        """Get point coordinates at distance s along the geometry element"""
        pass
    
    @abstractmethod
    def generate_points(self, step: float) -> List[Tuple[float, float]]:
        """Generate points along the element at regular intervals"""
        pass
    
    @abstractmethod
    def get_orthogonal(self, s: float, side: str = 'left') -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Get both the point and orthogonal vector at distance s along the line."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict:
        """Export element properties as dictionary"""
        pass
    
    def get_length(self) -> float:
        """Return element length"""
        return self.length
    
    def get_direction(self) -> float:
        """Return element direction at start point"""
        return self.direction
    
    def get_start_point(self) -> Tuple[float, float]:
        """Return start point coordinates"""
        return self.start_point
    
    def get_end_point(self) -> Tuple[float, float]:
        """Return end point coordinates"""
        return self.end_point
    
    def get_sta_start(self) -> float:
        """Return station start value"""
        return self.sta_start
    
    def get_sta_end(self) -> float:
        """Return station end value (start + length)"""
        if self.sta_start is not None and self.length is not None:
            return self.sta_start + self.length
        return None
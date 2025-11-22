# SPDX-License-Identifier: LGPL-2.1-or-later

from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Optional, Union


class Geometry(ABC):
    """
    Abstract base class for LandXML 1.2 geometry elements (Line, Curve, Spiral).
    Defines common interface and shared functionality for all alignment geometry.
    """

    def __init__(self, data: Dict):
        # Common attributes for all geometry types
        # Required attributes
        self.name = data.get('name', None)
        self.description = data.get('desc', None)
        self.sta_start = float(data['staStart']) if 'staStart' in data else None
        
        # Geometry control points
        self.start_point = data.get('Start', None)
        self.end_point = data.get('End', None)
        
        # Reference to coordinate system (set by parent alignment)
        self._coordinate_system = None

        if self.start_point is None or self.end_point is None:
            raise ValueError("Start and End coordinates must be provided")
    
    @abstractmethod
    def compute_missing_values(self):
        """Calculate all missing optional attributes from geometry"""
        pass
    
    @abstractmethod
    def get_key_points(self) -> Union[Tuple, List]:
        """Get key points in raw coordinates (no transformation)"""
        pass

    def get_key_points_transformed(self) -> Union[Tuple, List]:
        """
        Get key points with coordinate transformation applied.
        Uses parent alignment's coordinate system if available.
        
        Returns:
            Transformed key points
        """
        raw_points = self.get_key_points()
        
        if self._coordinate_system is None:
            return raw_points
        
        # Transform based on return type
        if isinstance(raw_points, tuple):
            return tuple(
                self._coordinate_system.transform_to_system(pt) 
                for pt in raw_points
            )
        elif isinstance(raw_points, list):
            return [
                self._coordinate_system.transform_to_system(pt) 
                for pt in raw_points
            ]
        
        return raw_points
    
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
        """Get both the point and orthogonal vector at distance s along the geometry."""
        pass

    @abstractmethod
    def project_point(self, point: Tuple[float, float]) -> Optional[float]:
        """Project point onto line and return distance along geometry from start."""
        pass

    @abstractmethod
    def get_type(self) -> str:
        """Get geometry element type."""
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

    def __str__(self) -> str:
        """Human-readable string representation"""
        return self.__repr__()

    def __eq__(self, other) -> bool:
        """Check equality between two geometry objects"""
        if not isinstance(other, self.__class__):
            return False
        
        return (
            self.start_point == other.start_point and
            self.end_point == other.end_point and
            abs(self.length - other.length) < 1e-6
        )

    def __ne__(self, other) -> bool:
        """Check inequality between two geometry objects"""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Make geometry objects hashable"""
        return hash((
            self.__class__.__name__,
            self.start_point,
            self.end_point,
            round(self.length, 6)
        ))

    def __len__(self) -> int:
        """Return length as integer (for compatibility)"""
        return int(self.length)

    def __bool__(self) -> bool:
        """Line is True if it has positive length"""
        return self.length > 0
    
    def __getstate__(self) -> Dict:
        """Return state for pickling/JSON serialization"""
        return self.to_dict()

    def __setstate__(self, state: Dict):
        """Restore state from unpickling/JSON deserialization"""
        self.__init__(state)
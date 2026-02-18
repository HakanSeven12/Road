# SPDX-License-Identifier: LGPL-2.1-or-later

from abc import ABC, abstractmethod
from typing import Dict, Tuple


class ProfileGeometry(ABC):
    """
    Abstract base class for vertical profile geometry elements.
    Defines common interface for vertical curves and tangents.
    """

    def __init__(self, data: Dict):
        """Initialize common profile geometry attributes"""
        self.geom_type = data.get('Type', None)
        self.description = data.get('desc', None)
    
    @abstractmethod
    def get_elevation_at_station(self, station: float) -> float:
        """Get elevation at given station along this geometry element"""
        pass
    
    @abstractmethod
    def get_grade_at_station(self, station: float) -> float:
        """Get grade (slope) at given station"""
        pass
    
    @abstractmethod
    def get_station_range(self) -> Tuple[float, float]:
        """Get (start_station, end_station) for this element"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict:
        """Export element properties as dictionary"""
        pass
    
    def get_type(self) -> str:
        """Get geometry element type"""
        return self.geom_type
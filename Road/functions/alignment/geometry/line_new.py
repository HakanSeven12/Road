# SPDX-License-Identifier: LGPL-2.1-or-later

import math
from typing import Dict, Tuple
from .geometry import Geometry


class Line(Geometry):
    """
    LandXML 1.2 line element reader & geometry generator.
    Supports straight line segments and auto-computes all missing optional attributes.
    """

    def __init__(self, data: Dict):
        # Required attributes
        super().__init__(data)
        
        if self.start_point is None or self.end_point is None:
            raise ValueError("Start and End coordinates must be provided")
        
        # Optional attributes
        self.direction = float(data['dir']) if 'dir' in data else None
        self.length = float(data['length']) if 'length' in data else None
        
        # Auto compute missing values
        self.compute_missing_values()
    
    def compute_missing_values(self):
        """Calculate all missing optional attributes from geometry"""
        
        # Calculate direction if not provided
        if self.direction is None:
            dx = self.end_point[0] - self.start_point[0]
            dy = self.end_point[1] - self.start_point[1]
            self.direction = math.atan2(dy, dx)
        
        # Calculate length if not provided
        if self.length is None:
            dx = self.end_point[0] - self.start_point[0]
            dy = self.end_point[1] - self.start_point[1]
            self.length = math.sqrt(dx**2 + dy**2)
        
        if self.length < 0:
            raise ValueError("Length must be positive")
    
    def get_point_at_distance(self, s: float) -> Tuple[float, float]:
        """Get point coordinates at distance s along the line from start point"""
        
        if s < 0 or s > self.length:
            raise ValueError(f"Distance {s} outside line length {self.length}")
        
        # Calculate point using direction and distance
        x = self.start_point[0] + s * math.cos(self.direction)
        y = self.start_point[1] + s * math.sin(self.direction)
        
        return x, y
    
    def generate_points(self, step: float) -> list:
        """Generate points along the line at regular intervals"""
        
        if step <= 0:
            raise ValueError("Step must be positive")
        
        points = []
        s = 0.0
        
        while s < self.length:
            x, y = self.get_point_at_distance(s)
            points.append((x, y))
            s += step
        
        # Add final end point
        x, y = self.get_point_at_distance(self.length)
        points.append((x, y))
        
        return points
    
    def get_key_points(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Return start, middle, and end points of the line"""
        
        return self.start_point, self.end_point
    
    def get_orthogonal(self, s: float, side: str = 'left') -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Get both the point and orthogonal vector at distance s along the line.
        
        Args:
            s: Distance along the line from start point
            side: Direction of orthogonal vector - 'left' or 'right'
            
        Returns:
            Tuple containing:
            - Point coordinates as (x, y)
            - Unit orthogonal vector as (x, y)
        """

        if side not in ['left', 'right']:
            raise ValueError("side must be 'left' or 'right'")
        
        point = self.get_point_at_distance(s)
        
        # Calculate orthogonal vector (perpendicular to line direction)
        if side == 'left':
            orthogonal_direction = self.direction + math.pi / 2
        else:  # right
            orthogonal_direction = self.direction - math.pi / 2
        
        orthogonal = (math.cos(orthogonal_direction), math.sin(orthogonal_direction))
        
        return point, orthogonal


    def to_dict(self) -> Dict:
        """Export line properties as dictionary"""
        
        return {
            'Type': 'Line',
            'name': self.name,
            'description': self.description,
            'staStart': self.sta_start,
            'length': self.length,
            'dir': self.direction,
            'start': self.start_point,
            'end': self.end_point
        }
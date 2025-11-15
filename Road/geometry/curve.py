# SPDX-License-Identifier: LGPL-2.1-or-later

import math
from typing import Dict, Tuple, Optional, List
from .geometry import Geometry


class Curve(Geometry):
    """
    LandXML 1.2 curve element reader & geometry generator.
    Supports circular arc curves and auto-computes all missing optional attributes.
    """

    VALID_TYPES = ['arc', 'chord']

    def __init__(self, data: Dict):
        # Required attributes
        super().__init__(data)
        self.rotation = data['rot']
        
        # Geometry control points
        self.center_point = data.get('Center', None)
        self.pi_point = data.get('PI', None)
        
        if self.start_point is None or self.center_point is None or self.end_point is None:
            raise ValueError("Start, Center and End coordinates must be provided")
        
        # Calculate radius from start point to center
        dx = self.center_point[0] - self.start_point[0]
        dy = self.center_point[1] - self.start_point[1]
        self.radius = math.sqrt(dx**2 + dy**2)
        
        if self.radius <= 0:
            raise ValueError("Radius must be positive")
        
        # Optional attributes
        self.curve_type = data.get('crvType', 'arc')
        self.chord = float(data['chord']) if 'chord' in data else None
        self.delta = float(data['delta']) if 'delta' in data else None
        self.dir_start = float(data['dirStart']) if 'dirStart' in data else None
        self.dir_end = float(data['dirEnd']) if 'dirEnd' in data else None
        self.length = float(data['length']) if 'length' in data else None
        self.mid_ordinate = float(data['midOrd']) if 'midOrd' in data else None
        self.tangent = float(data['tangent']) if 'tangent' in data else None
        self.external = float(data['external']) if 'external' in data else None
        
        # For large arcs, store multiple PI points
        self.pi_points = []
        
        # Auto compute missing values
        self.compute_missing_values()
    
    def compute_missing_values(self):
        """Calculate all missing optional attributes from geometry"""
        
        # Calculate central angle (delta) first - needed for other calculations
        if self.delta is None:
            start_angle = math.atan2(
                self.start_point[1] - self.center_point[1],
                self.start_point[0] - self.center_point[0]
            )
            end_angle = math.atan2(
                self.end_point[1] - self.center_point[1],
                self.end_point[0] - self.center_point[0]
            )
            
            delta = end_angle - start_angle
            
            # Normalize delta based on rotation
            if self.rotation == 'cw':
                if delta > 0:
                    delta -= 2 * math.pi
            else:
                if delta < 0:
                    delta += 2 * math.pi
            
            self.delta = abs(delta)
        
        # Calculate arc length
        if self.length is None:
            self.length = self.radius * self.delta
        
        # Calculate start and end directions
        if self.dir_start is None:
            start_angle = math.atan2(
                self.start_point[1] - self.center_point[1],
                self.start_point[0] - self.center_point[0]
            )
            if self.rotation == 'cw':
                self.dir_start = start_angle - math.pi / 2
            else:
                self.dir_start = start_angle + math.pi / 2
        
        # Calculate end direction
        if self.dir_end is None:
            sign = 1 if self.rotation == 'ccw' else -1
            self.dir_end = self.dir_start + self.delta * sign
        
        # Calculate PI point(s) - handle large arcs by subdividing
        if self.pi_point is None or not self.pi_points:
            self.pi_points = self._calculate_pi_points()
            # For backward compatibility, set single PI point
            if self.pi_points:
                self.pi_point = self.pi_points[0]
        
        if self.chord is None:
            half_delta = self.delta / 2
            self.chord = 2 * self.radius * math.sin(half_delta)
        
        # Calculate tangent length (from start/end point to PI)
        if self.tangent is None:
            half_delta = self.delta / 2
            self.tangent = self.radius * math.tan(half_delta)
        
        # Calculate mid-ordinate (sagitta)
        if self.mid_ordinate is None:
            half_delta = self.delta / 2
            self.mid_ordinate = self.radius * (1 - math.cos(half_delta))
        
        # Calculate external distance
        if self.external is None:
            half_delta = self.delta / 2
            self.external = self.radius * (1 / math.cos(half_delta) - 1)

    def _calculate_pi_points(self) -> List[Tuple[float, float]]:
        """
        Calculate PI point(s) for the arc.
        For arcs >= 180 degrees, subdivide into smaller arcs and calculate PI for each.
        """
        
        pi_points = []
        
        if self.delta >= math.pi:
            # Subdivide the arc into smaller segments
            # Calculate midpoint on the arc
            mid_distance = self.length / 2
            mid_point = self.get_point_at_distance(mid_distance)
            
            # First segment: start -> mid
            pi1 = self._calculate_single_pi_point(self.start_point, mid_point)
            if pi1:
                pi_points.append(pi1)
            
            # Second segment: mid -> end
            pi2 = self._calculate_single_pi_point(mid_point, self.end_point)
            if pi2:
                pi_points.append(pi2)
        else:
            # For smaller arcs, calculate single PI point
            pi = self._calculate_single_pi_point(self.start_point, self.end_point)
            if pi:
                pi_points.append(pi)
        
        return pi_points

    def _calculate_single_pi_point(self, point1: Tuple[float, float], 
                                   point2: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calculate PI point intersection from tangent lines at two points on the arc.
        Returns None if tangent lines are parallel.
        """
        
        # Direction from center to first point
        angle1 = math.atan2(
            point1[1] - self.center_point[1],
            point1[0] - self.center_point[0]
        )
        
        # Direction from center to second point
        angle2 = math.atan2(
            point2[1] - self.center_point[1],
            point2[0] - self.center_point[0]
        )
        
        # Tangent directions at both points (perpendicular to radius)
        if self.rotation == 'cw':
            tangent1 = angle1 - math.pi / 2
            tangent2 = angle2 - math.pi / 2
        else:
            tangent1 = angle1 + math.pi / 2
            tangent2 = angle2 + math.pi / 2
        
        # PI point is intersection of two tangent lines
        # Line 1: point1 + t1 * (cos(tangent1), sin(tangent1))
        # Line 2: point2 + t2 * (cos(tangent2), sin(tangent2))
        
        cos_t1 = math.cos(tangent1)
        sin_t1 = math.sin(tangent1)
        cos_t2 = math.cos(tangent2)
        sin_t2 = math.sin(tangent2)
        
        # Solve for intersection using parametric equations
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        
        denom = cos_t1 * sin_t2 - sin_t1 * cos_t2
        
        # Check if lines are parallel (denominator near zero)
        if abs(denom) < 1e-10:
            return None
        
        t1 = (dx * sin_t2 - dy * cos_t2) / denom
        
        pi_x = point1[0] + t1 * cos_t1
        pi_y = point1[1] + t1 * sin_t1
        
        return (pi_x, pi_y)

    def get_point_at_distance(self, s: float) -> Tuple[float, float]:
        """Get point coordinates at distance s along the arc from start point"""
        
        if s < 0 or s > self.length:
            raise ValueError(f"Distance {s} outside arc length {self.length}")
        
        # Calculate angle traversed at distance s
        angle_traversed = s / self.radius
        
        # Get starting angle from center
        start_angle = math.atan2(
            self.start_point[1] - self.center_point[1],
            self.start_point[0] - self.center_point[0]
        )
        
        # Calculate current angle based on rotation
        if self.rotation == 'cw':
            current_angle = start_angle - angle_traversed
        else:
            current_angle = start_angle + angle_traversed
        
        # Calculate point on arc
        x = self.center_point[0] + self.radius * math.cos(current_angle)
        y = self.center_point[1] + self.radius * math.sin(current_angle)
        
        return x, y
    
    def generate_points(self, step: float) -> list:
        """Generate points along the arc at regular intervals"""
        
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
    
    def get_key_points(self) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        """Return start, middle (arc midpoint), and end points of the curve"""
        
        # Middle point is at half of arc length
        mid_point = self.get_point_at_distance(self.length / 2)
        
        return self.start_point, mid_point, self.end_point

    def get_orthogonal(self, s: float, side: str = 'left') -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Get orthogonal vector at distance s along the arc.
        
        Args:
            s: Distance along the arc from start point
            side: Direction of orthogonal vector - 'left' or 'right'
            
        Returns:
            Tuple containing:
            - Point coordinates as (x, y)
            - Unit orthogonal vector as (x, y)
        """

        if side not in ['left', 'right']:
            raise ValueError("side must be 'left' or 'right'")
        
        point = self.get_point_at_distance(s)
        
        # Calculate angle at current point
        angle_traversed = s / self.radius
        start_angle = math.atan2(
            self.start_point[1] - self.center_point[1],
            self.start_point[0] - self.center_point[0]
        )
        
        if self.rotation == 'cw':
            current_angle = start_angle - angle_traversed
        else:
            current_angle = start_angle + angle_traversed
        
        # Calculate tangent direction at current point
        # Tangent is perpendicular to radius
        if self.rotation == 'cw':
            tangent_direction = current_angle - math.pi / 2
        else:
            tangent_direction = current_angle + math.pi / 2
        
        # Calculate orthogonal direction based on side
        if side == 'left':
            # Left is 90 degrees counterclockwise from tangent
            orthogonal_direction = tangent_direction + math.pi / 2
        else:  # right
            # Right is 90 degrees clockwise from tangent
            orthogonal_direction = tangent_direction - math.pi / 2
        
        orthogonal = (math.cos(orthogonal_direction), math.sin(orthogonal_direction))
        
        return point, orthogonal

    def project_point(self, point: Tuple[float, float]) -> Optional[float]:
        """
        Project point onto curve and return distance along curve from start.
        
        Args:
            point: (x, y) coordinates to project
            
        Returns:
            Distance along curve from start point, or None if projection is outside curve
        """
        # Calculate angle from center to point
        dx = point[0] - self.center_point[0]
        dy = point[1] - self.center_point[1]
        point_angle = math.atan2(dy, dx)
        
        # Calculate start angle
        start_angle = math.atan2(
            self.start_point[1] - self.center_point[1],
            self.start_point[0] - self.center_point[0]
        )
        
        # Calculate angle difference
        angle_diff = point_angle - start_angle
        
        # Normalize based on rotation
        if self.rotation == 'cw':
            # Clockwise rotation
            if angle_diff > 0:
                angle_diff -= 2 * math.pi
            angle_traversed = abs(angle_diff)
        else:
            # Counter-clockwise rotation
            if angle_diff < 0:
                angle_diff += 2 * math.pi
            angle_traversed = angle_diff
        
        # Check if angle is within curve bounds
        if angle_traversed < 0 or angle_traversed > self.delta:
            return None
        
        # Calculate distance along curve
        distance = self.radius * angle_traversed
        
        return distance

    def to_dict(self) -> Dict:
        """Export curve properties as dictionary"""
        
        return {
            'Type': 'Curve',
            'name': self.name,
            'description': self.description,
            'crvType': self.curve_type,
            'staStart': self.sta_start,
            'radius': self.radius,
            'rot': self.rotation,
            'delta': self.delta,
            'length': self.length,
            'chord': self.chord,
            'tangent': self.tangent,
            'midOrd': self.mid_ordinate,
            'external': self.external,
            'dirStart': self.dir_start,
            'dirEnd': self.dir_end,
            'Start': self.start_point,
            'Center': self.center_point,
            'End': self.end_point,
            'PI': self.pi_point,
            'pi_points': self.pi_points  # All PI points for large arcs
        }

    def __repr__(self) -> str:
        """String representation of curve"""
        return (
            f"Curve(radius={self.radius:.2f}, length={self.length:.2f}, "
            f"delta={math.degrees(self.delta):.2f}°, rot='{self.rotation}')"
        )

    def __str__(self) -> str:
        """Human-readable string representation"""
        return (
            f"Curve: R={self.radius:.2f}m, L={self.length:.2f}m, "
            f"Δ={math.degrees(self.delta):.2f}°, {self.rotation.upper()}"
        )

    def __eq__(self, other) -> bool:
        """Check equality between two curves"""
        if not isinstance(other, Curve):
            return False
        
        return (
            self.start_point == other.start_point and
            self.end_point == other.end_point and
            self.center_point == other.center_point and
            abs(self.radius - other.radius) < 1e-6 and
            abs(self.length - other.length) < 1e-6 and
            abs(self.delta - other.delta) < 1e-6 and
            self.rotation == other.rotation
        )

    def __hash__(self) -> int:
        """Make curve objects hashable"""
        return hash((
            'Curve',
            self.start_point,
            self.end_point,
            self.center_point,
            round(self.radius, 6),
            round(self.delta, 6),
            self.rotation
        ))
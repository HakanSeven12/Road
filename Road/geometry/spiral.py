# SPDX-License-Identifier: LGPL-2.1-or-later

import math
from scipy.special import fresnel
from typing import Dict, Tuple, Optional, List
from .geometry import Geometry


class Spiral(Geometry):
    """
    LandXML 1.2 spiral element reader & geometry generator.
    Supports clothoid spiral and auto-computes all missing optional attributes.
    """

    VALID_TYPES = ['clothoid', 'bloss', 'cosine', 'sine', 'biquadratic']

    def __init__(self, data: Dict):
        self._validate_data(data)
        super().__init__(data)

        # Required attributes
        self.length = float(data['length'])
        self.radius_end = float(data['radiusEnd'])
        self.radius_start = float(data['radiusStart'])
        self.rotation = data['rot']

        # Geometry control points
        self.pi_point = data.get('PI', None)

        if self.start_point is None or self.pi_point is None or self.end_point is None:
            raise ValueError("Start, PI and End coordinates must be provided")

        # Optional attributes
        self.spiral_type = data.get('spiType', 'clothoid')
        self.theta = float(data['theta']) if 'theta' in data else None
        self.total_y = float(data['totalY']) if 'totalY' in data else None
        self.total_x = float(data['totalX']) if 'totalX' in data else None
        self.tan_long = float(data['tanLong']) if 'tanLong' in data else None
        self.tan_short = float(data['tanShort']) if 'tanShort' in data else None
        self.dir_end = float(data['dirEnd']) if 'dirEnd' in data else None
        self.dir_start = float(data['dirStart']) if 'dirStart' in data else None
        self.constant = float(data['constant']) if 'constant' in data else None
        self.chord = float(data['chord']) if 'chord' in data else None

        # Auto compute
        self.compute_missing_values()

    def _validate_data(self, data: Dict):
        required = ['length', 'radiusEnd', 'radiusStart', 'rot']
        for f in required:
            if f not in data:
                raise ValueError(f"Missing required field: {f}")
        if data['rot'] not in ['cw', 'ccw']:
            raise ValueError("rot must be 'cw' or 'ccw'")
        if 'spiType' in data and data['spiType'] not in self.VALID_TYPES:
            raise ValueError("Invalid spiral type")

    def compute_missing_values(self):
        if self.constant is None:
            # Correct constant A calculation
            # Entry/Exit spiral (infinite → finite OR finite → infinite)
            if self.radius_start == float('inf') and self.radius_end != float('inf'):
                self.constant = math.sqrt(self.radius_end * self.length)
            elif self.radius_end == float('inf') and self.radius_start != float('inf'):
                self.constant = math.sqrt(self.radius_start * self.length)
            else:
                # Compound spiral (finite → finite): Euler spiral segment
                R1 = self.radius_start
                R2 = self.radius_end
                self.constant = math.sqrt(R1 * R2 * self.length / abs(R1 - R2))

        if True: #self.theta is None:
            R = self.radius_end if self.radius_start == float('inf') else self.radius_start
            self.theta = self.length / (2 * R)

        if True: #self.dir_start is None:
            dx = self.pi_point[0] - self.start_point[0]
            dy = self.pi_point[1] - self.start_point[1]
            if dx == 0 and dy == 0:
                raise ValueError("Start and PI cannot be identical")
            self.dir_start = math.atan2(dy, dx)

        sign = 1 if self.rotation == 'ccw' else -1
        self.dir_end = self.dir_start + self.theta * sign

        end_x, end_y = self.get_point_at_distance(self.length)

        if self.total_x is None:
            self.total_x = end_x
        if self.total_y is None:
            self.total_y = end_y

        if self.tan_long is None:
            self.tan_long = end_x
        if self.tan_short is None:
            self.tan_short = end_y

        if self.chord is None:
            self.chord = math.sqrt(end_x ** 2 + end_y ** 2)

    def get_point_at_distance(self, s: float) -> Tuple[float, float]:
        """
        Get point coordinates at distance s along the spiral from start point.
        Handles reversed spirals automatically.
        
        Args:
            s: Distance along spiral from alignment start point
            
        Returns:
            (x, y) coordinates in global coordinate system
        """
        if s < 0 or s > self.length:
            raise ValueError(f"Distance {s} outside spiral length {self.length}")
        
        # Check if spiral is reversed
        is_reversed = self.radius_end > self.radius_start
        
        # For reversed spirals, calculate from the opposite end
        if is_reversed:
            s_local = self.length - s
        else:
            s_local = s
        
        # Get local coordinates
        if self.radius_start != float('inf') and self.radius_end != float('inf'):
            xl, yl = self._compound_clothoid_point(s_local)
        else:
            xl, yl = self._clothoid_point(s_local)
        
        # Determine transformation parameters
        start = self.start_point
        dir_angle = self.dir_start
        
        if is_reversed:
            start = self.end_point
            dir_angle = self.dir_end + math.pi
        
        # Transform to global coordinates
        cos_a = math.cos(dir_angle)
        sin_a = math.sin(dir_angle)
        
        x = start[0] + xl * cos_a - yl * sin_a
        y = start[1] + xl * sin_a + yl * cos_a
        
        return (x, y)

    def _clothoid_point(self, L: float) -> Tuple[float, float]:
        sign = 1 if self.rotation == 'ccw' else -1
        if self.radius_end > self.radius_start:
            sign *= -1

        A = self.constant * math.sqrt(math.pi)
        t = L / A
        S, C = fresnel(t)
        x = A * C
        y = A * S * sign
        return x, y
    
    def _compound_clothoid_point(self, L: float) -> Tuple[float, float]:
        sign = 1 if self.rotation == 'ccw' else -1
        R1 = self.radius_start
        R2 = self.radius_end
        A = self.constant

        if R2 > R1:
            R1, R2 = R2, R1
            sign *= -1

        # s-values
        s1 = A**2 / R1
        s2 = A**2 / R2
        s = s1 + (L / self.length) * (s2 - s1)

        # raw clothoid absolute coords (with its internal sign)
        x2, y2 = self._clothoid_point(s)
        x1, y1 = self._clothoid_point(s1)

        dx = x2 - x1
        dy = y2 - y1

        # heading difference (sign only affects dphi)
        phi_s1  = sign * s1**2 / (2 * A**2)

        cos_p = math.cos(phi_s1)
        sin_p = math.sin(phi_s1)

        # rotate the segment WITHOUT any additional sign flips
        xr = dx * cos_p + dy * sin_p
        yr = -dx * sin_p + dy * cos_p

        return xr, yr

    def generate_points(self, step: float) -> List[Tuple[float, float]]:
        """
        Generate points along the spiral at regular intervals.
        Uses get_point_at_distance which handles reversed spirals automatically.
        
        Args:
            step: Distance interval between points
            
        Returns:
            List of (x, y) coordinate tuples in global coordinate system
        """
        if step <= 0:
            raise ValueError("Step must be positive")

        points = []
        s = 0.0

        # Generate points at regular intervals
        while s < self.length:
            point = self.get_point_at_distance(s)
            points.append(point)
            s += step

        # Add final end point
        end_point = self.get_point_at_distance(self.length)
        points.append(end_point)

        return points

    def get_orthogonal(self, s: float, side: str = 'left') -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Get both the point and orthogonal vector at distance s along the spiral.
        Handles reversed spirals automatically.
        
        Args:
            s: Distance along the spiral from alignment start point
            side: Direction of orthogonal vector - 'left' or 'right'
            
        Returns:
            Tuple containing:
            - Point coordinates as (x, y) in global coordinate system
            - Unit orthogonal vector as (x, y)
        """

        if side not in ['left', 'right']:
            raise ValueError("side must be 'left' or 'right'")
        
        # Check if spiral is reversed
        is_reversed = self.radius_end > self.radius_start
        
        # For reversed spirals, calculate from the opposite end
        if is_reversed:
            s_local = self.length - s
        else:
            s_local = s
        
        # Get the local point coordinates
        if self.radius_start != float('inf') and self.radius_end != float('inf'):
            xl, yl = self._compound_clothoid_point(s_local)
        else:
            xl, yl = self._clothoid_point(s_local)
        
        # Determine start point and rotation for transformation
        start = self.start_point
        dir_angle = self.dir_start
        sign = 1
        
        if is_reversed:
            start = self.end_point
            dir_angle = self.dir_end + math.pi
            sign = -1
        
        # Transform local coordinates to global coordinates
        cos_a = math.cos(dir_angle)
        sin_a = math.sin(dir_angle)
        
        x = start[0] + xl * cos_a - yl * sin_a
        y = start[1] + xl * sin_a + yl * cos_a
        point = (x, y)
        
        # Calculate tangent direction using numerical differentiation
        delta = 1e-6
        
        if s_local - delta >= 0:
            if self.radius_start != float('inf') and self.radius_end != float('inf'):
                xl_before, yl_before = self._compound_clothoid_point(s_local - delta)
            else:
                xl_before, yl_before = self._clothoid_point(s_local - delta)
        else:
            xl_before, yl_before = xl, yl
        
        if s_local + delta <= self.length:
            if self.radius_start != float('inf') and self.radius_end != float('inf'):
                xl_after, yl_after = self._compound_clothoid_point(s_local + delta)
            else:
                xl_after, yl_after = self._clothoid_point(s_local + delta)
        else:
            xl_after, yl_after = xl, yl
        
        # Local tangent (in local coordinate system)
        dx_local = xl_after - xl_before
        dy_local = yl_after - yl_before
        
        tangent_length = math.sqrt(dx_local**2 + dy_local**2)
        
        if tangent_length < 1e-10:
            raise ValueError("Cannot determine tangent direction at this point")
        
        # Normalize local tangent
        tangent_x_local = dx_local / tangent_length
        tangent_y_local = dy_local / tangent_length
        
        # Transform tangent to global coordinates
        tangent_x_global = tangent_x_local * cos_a - tangent_y_local * sin_a
        tangent_y_global = tangent_x_local * sin_a + tangent_y_local * cos_a
        
        # Orthogonal vector based on side
        if side == 'left':  # 90 degrees counterclockwise from tangent
            orthogonal = (-tangent_y_global * sign, tangent_x_global * sign)
        else:  # right - 90 degrees clockwise from tangent
            orthogonal = (tangent_y_global * sign, -tangent_x_global * sign)

        return point, orthogonal

    def project_point(self, point: Tuple[float, float]) -> Optional[float]:
        """
        Project a point onto the spiral and return distance along spiral.
        Handles reversed spirals automatically.
        Uses a robust 1D parabolic search over arc length.
        
        Args:
            point: (x, y) coordinates to project
            
        Returns:
            Distance along spiral from alignment start point, or None if outside bounds
        """

        # Check if spiral is reversed
        is_reversed = self.radius_end > self.radius_start
        
        # Transform to local system
        start = self.start_point
        dir_angle = self.dir_start

        if is_reversed:
            start = self.end_point
            dir_angle = self.dir_end + math.pi

        cos_a = math.cos(dir_angle)
        sin_a = math.sin(dir_angle)

        dx = point[0] - start[0]
        dy = point[1] - start[1]

        local_x = dx * cos_a + dy * sin_a
        local_y = -dx * sin_a + dy * cos_a

        # Distance-squared function in local coords
        def f(s_loc):
            if self.radius_start != float('inf') and self.radius_end != float('inf'):
                xl, yl = self._compound_clothoid_point(s_loc)
            else:
                xl, yl = self._clothoid_point(s_loc)
            return (xl - local_x)**2 + (yl - local_y)**2

        # Initial coarse search (samples)
        N = 50
        s_values = [i * self.length / N for i in range(N + 1)]
        d_values = [f(s) for s in s_values]

        i_min = min(range(len(d_values)), key=lambda i: d_values[i])

        # Bracket minimum
        if i_min == 0:
            a, b = s_values[0], s_values[1]
        elif i_min == N:
            a, b = s_values[N - 1], s_values[N]
        else:
            a = s_values[i_min - 1]
            b = s_values[i_min + 1]

        # Parabolic refinement
        tol = 1e-7
        for _ in range(60):
            m1 = a + (b - a) * 0.25
            m2 = a + (b - a) * 0.5
            m3 = a + (b - a) * 0.75

            f1, f2, f3 = f(m1), f(m2), f(m3)

            # Pick best sub-interval
            if f1 < f2:
                b = m2
            elif f3 < f2:
                a = m2
            else:
                a = m1
                b = m3

            if b - a < tol:
                break

        distance_local = (a + b) / 2

        if distance_local < 0 or distance_local > self.length:
            return None
        
        # Convert back to alignment distance
        if is_reversed:
            distance = self.length - distance_local
        else:
            distance = distance_local
        
        return distance

    def to_dict(self) -> Dict:
        return {
            'Type': 'Spiral',
            'name': self.name,
            'description': self.description,
            'spiType': self.spiral_type,
            'staStart': self.sta_start,
            'Start': self.start_point,
            'End': self.end_point,
            'PI': self.pi_point,
            'length': self.length,
            'radiusStart': self.radius_start,
            'radiusEnd': self.radius_end,
            'rot': self.rotation,
            'theta': self.theta,
            'totalX': self.total_x,
            'totalY': self.total_y,
            'tanLong': self.tan_long,
            'tanShort': self.tan_short,
            'dirStart': self.dir_start,
            'dirEnd': self.dir_end,
            'constant': self.constant,
            'chord': self.chord,
        }

    def __repr__(self) -> str:
        """String representation of spiral"""
        r_start = f"{self.radius_start:.2f}" if self.radius_start != float('inf') else "∞"
        r_end = f"{self.radius_end:.2f}" if self.radius_end != float('inf') else "∞"
        
        return (
            f"Spiral(type='{self.spiral_type}', length={self.length:.2f}, "
            f"R_start={r_start}, R_end={r_end}, rot='{self.rotation}')"
        )


    def __str__(self) -> str:
        """Human-readable string representation"""
        r_start = f"{self.radius_start:.2f}m" if self.radius_start != float('inf') else "∞"
        r_end = f"{self.radius_end:.2f}m" if self.radius_end != float('inf') else "∞"
        
        return (
            f"Spiral: L={self.length:.2f}m, A={self.constant:.2f}, "
            f"R: {r_start} → {r_end}, {self.rotation.upper()}"
        )


    def __eq__(self, other) -> bool:
        """Check equality between two spirals"""
        if not isinstance(other, Spiral):
            return False
        
        return (
            self.start_point == other.start_point and
            self.end_point == other.end_point and
            self.pi_point == other.pi_point and
            abs(self.length - other.length) < 1e-6 and
            abs(self.radius_start - other.radius_start) < 1e-6 and
            abs(self.radius_end - other.radius_end) < 1e-6 and
            abs(self.constant - other.constant) < 1e-6 and
            self.rotation == other.rotation and
            self.spiral_type == other.spiral_type
        )


    def __hash__(self) -> int:
        """Make spiral objects hashable"""
        return hash((
            'Spiral',
            self.start_point,
            self.end_point,
            self.pi_point,
            round(self.length, 6),
            round(self.radius_start, 6),
            round(self.radius_end, 6),
            round(self.constant, 6),
            self.rotation,
            self.spiral_type
        ))


    def __len__(self) -> int:
        """Return length as integer (for compatibility)"""
        return int(self.length)


    def __bool__(self) -> bool:
        """Spiral is True if it has positive length"""
        return self.length > 0

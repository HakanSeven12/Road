# SPDX-License-Identifier: LGPL-2.1-or-later

import math
from scipy.special import fresnel
from typing import Dict, Tuple
from .geometry import Geometry


class Spiral(Geometry):
    """
    LandXML 1.2 spiral element reader & geometry generator.
    Supports clothoid spiral and auto-computes all missing optional attributes.
    """

    VALID_TYPES = ['clothoid', 'bloss', 'cosine', 'sine', 'biquadratic']

    def __init__(self, data: Dict):
        #self._validate_data(data)
        super().__init__(data)

        # Required attributes
        self.length = float(data['Length'])
        self.radius_end = float(data['EndRadius'])
        self.radius_start = float(data['StartRadius'])
        self.rotation = 'ccw' if data['Direction'] == -1 else 'cw'

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

        if self.theta is None:
            R = self.radius_end if self.radius_start == float('inf') else self.radius_start
            self.theta = self.length / (2 * abs(R))

        if self.dir_start is None:
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

    # LOCAL CLOTHOID
    def get_point_at_distance(self, s: float) -> Tuple[float, float]:
        if s < 0 or s > self.length:
            raise ValueError(f"Distance {s} outside spiral length {self.length}")
        if self.radius_start != float('inf') and self.radius_end != float('inf'):
            return self._compound_clothoid_point(s)
        return self._clothoid_point(s)

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

    # POINT GENERATION WITH INLINE ROTATION AND TRANSLATION
    def generate_points(self, step: float):
        if step <= 0:
            raise ValueError("Step must be positive")

        start = self.start_point
        dir = self.dir_start

        if self.radius_end > self.radius_start:
            start = self.end_point
            dir = self.dir_end + math.pi

        pts = []
        s = 0.0

        cos_a = math.cos(dir)
        sin_a = math.sin(dir)
        sx, sy = start[0], start[1]

        while s < self.length:
            xl, yl = self.get_point_at_distance(s)
            X = sx + xl * cos_a - yl * sin_a
            Y = sy + xl * sin_a + yl * cos_a
            pts.append((X, Y))
            s += step

        xl, yl = self.get_point_at_distance(self.length)
        X = sx + xl * cos_a - yl * sin_a
        Y = sy + xl * sin_a + yl * cos_a
        pts.append((X, Y))

        return pts

    def get_point_and_orthogonal(self, s: float, side: str = 'left') -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Get both the point and orthogonal vector at distance s along the spiral.
        
        Args:
            s: Distance along the spiral from start point
            side: Direction of orthogonal vector - 'left' or 'right' (relative to spiral direction)
            
        Returns:
            Tuple containing:
            - Point coordinates as (x, y) in global coordinate system
            - Unit orthogonal vector as (x, y)
        """
        
        if side not in ['left', 'right']:
            raise ValueError("side must be 'left' or 'right'")
        
        # Get the local point coordinates at distance s
        xl, yl = self.get_point_at_distance(s)
        
        # Determine start point and rotation for transformation
        start = self.start_point
        dir_angle = self.dir_start
        
        if self.radius_end > self.radius_start:
            start = self.end_point
            dir_angle = self.dir_end + math.pi
        
        # Transform local coordinates to global coordinates
        cos_a = math.cos(dir_angle)
        sin_a = math.sin(dir_angle)
        
        x = start[0] + xl * cos_a - yl * sin_a
        y = start[1] + xl * sin_a + yl * cos_a
        point = (x, y)
        
        # Calculate tangent direction using numerical differentiation
        delta = 1e-6
        
        if s - delta >= 0:
            xl_before, yl_before = self.get_point_at_distance(s - delta)
        else:
            xl_before, yl_before = self.get_point_at_distance(0)
        
        if s + delta <= self.length:
            xl_after, yl_after = self.get_point_at_distance(s + delta)
        else:
            xl_after, yl_after = self.get_point_at_distance(self.length)
        
        # Local tangent
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
            orthogonal = (-tangent_y_global, tangent_x_global)
        else:  # right - 90 degrees clockwise from tangent
            orthogonal = (tangent_y_global, -tangent_x_global)
    
        return point, orthogonal

    def to_dict(self) -> Dict:
        return {
            'Type': 'Spiral',
            'name': self.name,
            'description': self.description,
            'spiType': self.spiral_type,
            'staStart': self.sta_start,
            'start': self.start_point,
            'end': self.end_point,
            'pi': self.pi_point,
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
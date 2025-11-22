# SPDX-License-Identifier: LGPL-2.1-or-later

import math
from typing import Tuple, List, Optional
from enum import Enum


class SystemType(Enum):
    """Coordinate system types"""
    GLOBAL = 'global'
    LOCAL = 'local'
    CUSTOM = 'custom'

class CoordinateSystem:
    """
    Coordinate system transformation manager for alignment geometry.
    Handles transformations between global, local, and custom coordinate systems.
    Supports coordinate swapping between LandXML format and FreeCAD format.
    """
    
    def __init__(self, system_type: str = 'global', 
                 origin: Optional[Tuple[float, float]] = None,
                 rotation: Optional[float] = None,
                 swap: bool = False):
        """
        Initialize coordinate system.
        
        Args:
            system_type: Type of coordinate system - 'global', 'local', or 'custom'
            origin: Origin point (x, y) for local/custom systems
            rotation: Rotation angle in radians for local/custom systems
            swap: If True, swap coordinates for output
                  LandXML internal: (Northing, Easting)
                  FreeCAD output: (Easting, Northing) when swap_xy=True
        """
        self.swap = swap
        self.set_system(system_type, origin, rotation)
    
    def set_system(self, system_type: str, 
                   origin: Optional[Tuple[float, float]] = None,
                   rotation: Optional[float] = None):
        """
        Set or change the coordinate system.
        
        Args:
            system_type: Type of coordinate system - 'global', 'local', or 'custom'
            origin: Origin point (x, y). Required for 'custom' system
            rotation: Rotation angle in radians. Optional, defaults to 0.0
        """
        if system_type not in [st.value for st in SystemType]:
            raise ValueError(f"system_type must be one of: {[st.value for st in SystemType]}")
        
        self.system_type = system_type
        
        if system_type == 'global':
            self.origin = (0.0, 0.0)
            self.rotation = 0.0
        else:
            if origin is None and system_type == 'custom':
                raise ValueError("origin is required for custom coordinate system")
            
            self.origin = origin if origin is not None else (0.0, 0.0)
            self.rotation = rotation if rotation is not None else 0.0
        
        # Precompute transformation matrices
        self._update_matrices()
    
    def _update_matrices(self):
        """Precompute rotation matrix coefficients for efficiency"""
        self.cos_rotation = math.cos(self.rotation)
        self.sin_rotation = math.sin(self.rotation)
        self.cos_rotation_inv = math.cos(-self.rotation)
        self.sin_rotation_inv = math.sin(-self.rotation)
    
    def set_swap(self, swap: bool):
        """
        Enable or disable XY coordinate swapping for output.
        
        Args:
            swap: If True, swap X and Y coordinates in output
                  LandXML: (Northing, Easting) → Output: (Easting, Northing)
        """
        self.swap = swap
    
    def get_swap(self) -> bool:
        """Check if XY swapping is enabled"""
        return self.swap
    
    def _apply_swap(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """
        Apply coordinate swap for output if enabled.
        LandXML internal: (Northing, Easting)
        Output with swap: (Easting, Northing)
        """
        if self.swap:
            return (point[1], point[0])  # Swap: (N, E) → (E, N)
        return point
    
    def _reverse_swap(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """
        Reverse coordinate swap for input if enabled.
        Input with swap: (Easting, Northing)
        LandXML internal: (Northing, Easting)
        """
        if self.swap:
            return (point[1], point[0])  # Swap back: (E, N) → (N, E)
        return point
    
    def set_origin(self, origin: Tuple[float, float]):
        """
        Set the origin point for the coordinate system.
        
        Args:
            origin: Origin point (x, y) in global coordinates
        """
        self.origin = origin
    
    def set_rotation(self, rotation: float):
        """
        Set the rotation angle for the coordinate system.
        
        Args:
            rotation: Rotation angle in radians
        """
        self.rotation = rotation
        self._update_matrices()
    
    def get_origin(self) -> Tuple[float, float]:
        """Get the current origin point"""
        return self.origin
    
    def get_rotation(self) -> float:
        """Get the current rotation angle in radians"""
        return self.rotation
    
    def get_rotation_degrees(self) -> float:
        """Get the current rotation angle in degrees"""
        return math.degrees(self.rotation)
    
    def is_global(self) -> bool:
        """Check if current system is global"""
        return self.system_type == 'global'
    
    def transform_to_system(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """
        Transform point from internal LandXML format to current coordinate system.
        
        Args:
            point: Point in internal format (Northing, Easting)
            
        Returns:
            Point in current coordinate system with swap applied if enabled
        """
        if self.system_type == 'global':
            # Only apply swap for global system
            return self._apply_swap(point)
        
        # Translate (move origin)
        x = point[0] - self.origin[0]
        y = point[1] - self.origin[1]
        
        # Rotate (counter-clockwise by -rotation angle)
        x_new = x * self.cos_rotation_inv - y * self.sin_rotation_inv
        y_new = x * self.sin_rotation_inv + y * self.cos_rotation_inv
        
        # Apply swap to output
        return self._apply_swap((x_new, y_new))
    
    def transform_from_system(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """
        Transform point from current coordinate system to internal LandXML format.
        
        Args:
            point: Point in current coordinate system (possibly swapped)
            
        Returns:
            Point in internal format (Northing, Easting)
        """
        # Reverse swap first to get back to internal format
        point = self._reverse_swap(point)
        
        if self.system_type == 'global':
            return point
        
        # Rotate back (clockwise by rotation angle)
        x_rot = point[0] * self.cos_rotation - point[1] * self.sin_rotation
        y_rot = point[0] * self.sin_rotation + point[1] * self.cos_rotation
        
        # Translate back (restore origin)
        x = x_rot + self.origin[0]
        y = y_rot + self.origin[1]
        
        return (x, y)
    
    def transform_points_to_system(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Transform multiple points from global to current coordinate system.
        
        Args:
            points: List of points in global coordinates
            
        Returns:
            List of points in current coordinate system
        """
        if self.system_type == 'global':
            return points.copy()
        
        return [self.transform_to_system(p) for p in points]
    
    def transform_points_from_system(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Transform multiple points from current coordinate system to global.
        
        Args:
            points: List of points in current coordinate system
            
        Returns:
            List of points in global coordinates
        """
        if self.system_type == 'global':
            return points.copy()
        
        return [self.transform_from_system(p) for p in points]
    
    def transform_vector_to_system(self, vector: Tuple[float, float]) -> Tuple[float, float]:
        """
        Transform a vector (direction) from global to current coordinate system.
        Note: Vectors don't undergo translation, only rotation and optional axis swap.
        
        Args:
            vector: Vector in global coordinates (vx, vy)
            
        Returns:
            Vector in current coordinate system (vx, vy)
        """
        if self.system_type == 'global':
            return self._apply_swap(vector)
        
        # Only rotate, no translation for vectors
        vx = vector[0] * self.cos_rotation_inv - vector[1] * self.sin_rotation_inv
        vy = vector[0] * self.sin_rotation_inv + vector[1] * self.cos_rotation_inv
        
        # Apply axis swap
        return self._apply_swap((vx, vy))
    
    def transform_vector_from_system(self, vector: Tuple[float, float]) -> Tuple[float, float]:
        """
        Transform a vector (direction) from current coordinate system to global.
        Note: Vectors don't undergo translation, only rotation and optional axis swap.
        
        Args:
            vector: Vector in current coordinate system (vx, vy)
            
        Returns:
            Vector in global coordinates (vx, vy)
        """
        # Reverse axis swap first
        vector = self._reverse_swap(vector)
        
        if self.system_type == 'global':
            return vector
        
        # Only rotate back, no translation for vectors
        vx = vector[0] * self.cos_rotation - vector[1] * self.sin_rotation
        vy = vector[0] * self.sin_rotation + vector[1] * self.cos_rotation
        
        return (vx, vy)
    
    def transform_angle_to_system(self, angle: float) -> float:
        """
        Transform an angle from global to current coordinate system.
        
        Args:
            angle: Angle in radians in global coordinates
            
        Returns:
            Angle in radians in current coordinate system
        """
        if self.system_type == 'global':
            return angle
        
        return angle - self.rotation
    
    def transform_angle_from_system(self, angle: float) -> float:
        """
        Transform an angle from current coordinate system to global.
        
        Args:
            angle: Angle in radians in current coordinate system
            
        Returns:
            Angle in radians in global coordinates
        """
        if self.system_type == 'global':
            return angle
        
        return angle + self.rotation
    
    def get_transformation_matrix(self) -> Tuple[Tuple[float, float, float], 
                                                  Tuple[float, float, float],
                                                  Tuple[float, float, float]]:
        """
        Get the 3x3 homogeneous transformation matrix for global to current system.
        
        Returns:
            3x3 transformation matrix as tuple of tuples:
            [[cos(θ), -sin(θ), -x0*cos(θ) + y0*sin(θ)],
             [sin(θ),  cos(θ), -x0*sin(θ) - y0*cos(θ)],
             [0,       0,       1                     ]]
        """
        if self.system_type == 'global':
            return ((1.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0),
                    (0.0, 0.0, 1.0))
        
        c = self.cos_rotation_inv
        s = self.sin_rotation_inv
        x0, y0 = self.origin
        
        return ((c, -s, -x0 * c + y0 * s),
                (s,  c, -x0 * s - y0 * c),
                (0.0, 0.0, 1.0))
    
    def get_inverse_transformation_matrix(self) -> Tuple[Tuple[float, float, float], 
                                                         Tuple[float, float, float],
                                                         Tuple[float, float, float]]:
        """
        Get the 3x3 homogeneous transformation matrix for current system to global.
        
        Returns:
            3x3 inverse transformation matrix as tuple of tuples
        """
        if self.system_type == 'global':
            return ((1.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0),
                    (0.0, 0.0, 1.0))
        
        c = self.cos_rotation
        s = self.sin_rotation
        x0, y0 = self.origin
        
        return ((c, -s, x0),
                (s,  c, y0),
                (0.0, 0.0, 1.0))
    
    def to_dict(self) -> dict:
        """
        Export coordinate system properties as dictionary.
        
        Returns:
            Dictionary containing system type, origin, and rotation
        """
        return {
            'system_type': self.system_type,
            'origin': self.origin,
            'rotation': self.rotation,
            'rotation_degrees': math.degrees(self.rotation),
            'swap': self.swap
        }
    
    def __repr__(self) -> str:
        """String representation"""
        swap_info = ", swap=True" if self.swap else ""
        
        if self.system_type == 'global':
            return f"CoordinateSystem(type='global'{swap_info})"
        
        return (f"CoordinateSystem(type='{self.system_type}', "
                f"origin={self.origin}, "
                f"rotation={self.rotation:.4f} rad / {math.degrees(self.rotation):.2f}°"
                f"{swap_info})")
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        swap_info = " [Swap XY Enabled]" if self.swap else ""
        
        if self.system_type == 'global':
            return f"Global Coordinate System{swap_info}"
        
        return (f"{self.system_type.capitalize()} Coordinate System: "
                f"Origin=({self.origin[0]:.2f}, {self.origin[1]:.2f}), "
                f"Rotation={math.degrees(self.rotation):.2f}°{swap_info}")
    
    def __eq__(self, other) -> bool:
        """Check equality between two coordinate systems"""
        if not isinstance(other, CoordinateSystem):
            return False
        
        return (self.system_type == other.system_type and
                abs(self.origin[0] - other.origin[0]) < 1e-6 and
                abs(self.origin[1] - other.origin[1]) < 1e-6 and
                abs(self.rotation - other.rotation) < 1e-6)
    
    def __hash__(self) -> int:
        """Make coordinate system hashable"""
        return hash((
            self.system_type,
            round(self.origin[0], 6),
            round(self.origin[1], 6),
            round(self.rotation, 6)
        ))
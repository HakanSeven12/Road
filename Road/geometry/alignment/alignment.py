# SPDX-License-Identifier: LGPL-2.1-or-later

import math
from typing import Dict, List, Tuple, Optional, Union
from ...functions.coordinate_system import CoordinateSystem
from ..profile.profile import Profile
from .line import Line
from .curve import Curve
from .spiral import Spiral


class Alignment:
    """
    LandXML 1.2 horizontal alignment reader & geometry generator.
    Manages a sequence of Line, Curve, and Spiral geometry elements with station equations.
    """

    def __init__(self, data: Dict):
        """
        Initialize alignment from LandXML data dictionary.
        
        Args:
            data: Dictionary containing alignment attributes and geometry elements
        """
        # Alignment metadata
        self.name = data.get('name', None)
        self.description = data.get('desc', None)
        self.length = float(data['length']) if 'length' in data else None
        self.sta_start = float(data['staStart']) if 'staStart' in data else 0.0
        
        # Alignment start point (optional)
        self.start_point = data.get('start', None)

        # Geometry elements list
        self.elements: List[Union[Line, Curve, Spiral]] = []
        
        # Coordinate system for transformations
        coord_sys_data = data['coordinateSystem'] if 'coordinateSystem' in data else {'system_type': 'global'}
        self.coordinate_system = CoordinateSystem(
            system_type=coord_sys_data.get('system_type', 'global'),
            origin=tuple(coord_sys_data['origin']) if 'origin' in coord_sys_data else None,
            rotation=coord_sys_data.get('rotation', None),
            swap=coord_sys_data.get('swap', False)
        )

        # Alignment PI points (Point of Intersection)
        self.align_pis: List[Dict] = []
        
        # Parse alignment PI points
        if 'AlignPIs' in data and data['AlignPIs']:
            self._parse_align_pis(data['AlignPIs'])
        elif 'alignPIs' in data and data['alignPIs']:  # Also handle lowercase version
            self._parse_align_pis(data['alignPIs'])
        
        # Station equations list (sorted by internal station)
        self.station_equations: List[Dict] = []
        
        # Parse station equations first (before geometry)
        if 'StaEquation' in data and data['StaEquation']:
            self._parse_station_equations(data['StaEquation'])
        elif 'stationEquations' in data and data['stationEquations']:  # Also handle lowercase version
            self._parse_station_equations(data['stationEquations'])
        
        # Parse coordinate geometry elements
        if 'CoordGeom' in data and data['CoordGeom']:
            self._parse_coord_geom(data['CoordGeom'])
        
        # Validate and compute alignment properties
        #self._validate_alignment()
        self._compute_alignment_properties()
    
        # Profile data (optional)
        self.profile = None
        
        # Parse profile if present
        if 'Profile' in data and data['Profile']:
            try:
                self.profile = Profile(data['Profile'], parent_alignment=self)
            except Exception as e:
                print(f"Warning: Failed to parse profile: {str(e)}")
    
    def set_coordinate_system(self, system_type: str, 
                            origin: Optional[Tuple[float, float]] = None,
                            rotation: Optional[float] = None):
        """
        Set the coordinate system for alignment calculations.
        
        Args:
            system_type: 'global', 'local', or 'custom'
            origin: Origin point for custom system (x, y)
            rotation: Rotation angle in radians
        """
        if system_type == 'local':
            # Local system uses alignment start point as origin
            origin = self.start_point
            rotation = self._calculate_start_direction()
        
        self.coordinate_system.set_system(system_type, origin, rotation)
    
    def get_coordinate_system(self) -> CoordinateSystem:
        """Get the current coordinate system object"""
        return self.coordinate_system
    
    def _calculate_start_direction(self) -> float:
        """Calculate direction at alignment start"""
        if not self.elements:
            return 0.0
        
        first_elem = self.elements[0]
        if hasattr(first_elem, 'direction'):
            return first_elem.direction
        elif hasattr(first_elem, 'dir_start'):
            return first_elem.dir_start
        return 0.0
    
    # Get profile methods
    def get_profile(self) -> Optional['Profile']:
        """
        Get the profile associated with this alignment.
        
        Returns:
            Profile object or None if no profile is associated
        """
        return self.profile

    def set_profile(self, profile_data: Dict):
        """
        Set or update the profile for this alignment.
        
        Args:
            profile_data: Dictionary containing profile data
        """
        try:
            self.profile = Profile(profile_data, parent_alignment=self)
        except Exception as e:
            raise ValueError(f"Failed to set profile: {str(e)}")

    def has_profile(self) -> bool:
        """Check if alignment has an associated profile"""
        return self.profile is not None

    def get_elevation_at_station(self, station: float, profalign_name: Optional[str] = None) -> Optional[float]:
        """
        Get design elevation at station from profile.
        
        Args:
            station: Station to query
            profalign_name: Name of ProfAlign (uses first if None)
            
        Returns:
            Elevation at station or None if no profile exists
        """
        if self.profile is None:
            return None
        
        return self.profile.get_elevation_at_station(station, profalign_name)

    def get_3d_point_at_station(self, station: float, profalign_name: Optional[str] = None) -> Optional[Tuple[float, float, float]]:
        """
        Get 3D point coordinates (X, Y, Z) at station along alignment.
        Combines horizontal alignment coordinates with profile elevation.
        
        Args:
            station: Station to query
            profalign_name: Name of ProfAlign (uses first if None)
            
        Returns:
            (x, y, z) coordinates at station or None if profile is missing
        """
        if self.profile is None:
            return None
        
        # Get horizontal coordinates
        x, y = self.get_point_at_station(station)
        
        # Get elevation from profile
        z = self.profile.get_elevation_at_station(station, profalign_name)
        
        if z is None:
            return None
        
        return (x, y, z)
    
    def _parse_align_pis(self, align_pis_list: List[Dict]):
        """Parse and store alignment PI points"""
        
        for i, pi_data in enumerate(align_pis_list):
            try:
                pi_point = pi_data.get('point', None)
                
                if pi_point is None:
                    raise ValueError(f"PI point {i} missing 'point' coordinate")
                
                # Ensure point is tuple of floats
                if not isinstance(pi_point, (tuple, list)) or len(pi_point) != 2:
                    raise ValueError(f"PI point {i} must be (x, y) coordinate")
                
                pi = {
                    'point': (float(pi_point[0]), float(pi_point[1])),
                    'station': float(pi_data['station']) if 'station' in pi_data else None,
                    'description': pi_data.get('desc', pi_data.get('description', None))
                }
                
                self.align_pis.append(pi)
                
            except Exception as e:
                raise ValueError(f"Error parsing alignment PI {i}: {str(e)}")
        
        # Sort by station if stations are provided
        if all(pi['station'] is not None for pi in self.align_pis):
            self.align_pis.sort(key=lambda pi: pi['station'])
    
    def _parse_station_equations(self, sta_eq_list: List[Dict]):
        """Parse and store station equation dictionaries"""
        
        for i, eq_data in enumerate(sta_eq_list):
            try:
                sta_ahead = float(eq_data['staAhead'])
                sta_back = float(eq_data['staBack'])
                sta_internal = float(eq_data.get('staInternal', sta_back))
                description = eq_data.get('desc', eq_data.get('description', None))
                
                equation = {
                    'staAhead': sta_ahead,
                    'staBack': sta_back,
                    'staInternal': sta_internal,
                    'adjustment': eq_data.get('adjustment', sta_ahead - sta_back),
                    'description': description
                }
                
                self.station_equations.append(equation)
                
            except Exception as e:
                raise ValueError(f"Error parsing station equation {i}: {str(e)}")
        
        # Sort by internal station
        self.station_equations.sort(key=lambda eq: eq['staInternal'])
        
        # Validate station equations don't overlap
        for i in range(len(self.station_equations) - 1):
            if self.station_equations[i]['staInternal'] >= self.station_equations[i+1]['staInternal']:
                raise ValueError(
                    f"Station equations must be in ascending order: "
                    f"{self.station_equations[i]['staInternal']} >= "
                    f"{self.station_equations[i+1]['staInternal']}"
                )
    
    def _parse_coord_geom(self, coord_geom_list: List[Dict]):
        """Parse and create geometry elements from CoordGeom list"""
        
        for i, geom_data in enumerate(coord_geom_list):
            geom_type = geom_data.get('Type', None)
            
            if geom_type is None:
                raise ValueError(f"Geometry element {i} missing 'Type' field")
            
            try:
                if geom_type == 'Line':
                    element = Line(geom_data)
                elif geom_type == 'Curve':
                    element = Curve(geom_data)
                elif geom_type == 'Spiral':
                    element = Spiral(geom_data)
                else:
                    raise ValueError(f"Unknown geometry type: {geom_type}")
                
                # Store reference to parent alignment's coordinate system
                element._coordinate_system = self.coordinate_system
                
                self.elements.append(element)
                
            except Exception as e:
                raise ValueError(f"Error parsing geometry element {i} ({geom_type}): {str(e)}")

    def _validate_alignment(self):
        """Validate alignment continuity and geometry"""
        
        if not self.elements:
            raise ValueError("Alignment must contain at least one geometry element")
        
        # Check if alignment start point matches first element start point
        if self.start_point is not None:
            first_elem_start = self.elements[0].get_start_point()
            tolerance = 1e-3
            
            dx = abs(self.start_point[0] - first_elem_start[0])
            dy = abs(self.start_point[1] - first_elem_start[1])
            
            if dx > tolerance or dy > tolerance:
                raise ValueError(
                    f"Alignment start point {self.start_point} does not match "
                    f"first element start point {first_elem_start}"
                )
        
        # Check continuity between consecutive elements
        tolerance = 1e-3
        
        for i in range(len(self.elements) - 1):
            current = self.elements[i]
            next_elem = self.elements[i + 1]
            
            current_end = current.get_end_point()
            next_start = next_elem.get_start_point()
            
            dx = abs(current_end[0] - next_start[0])
            dy = abs(current_end[1] - next_start[1])
            
            if dx > tolerance or dy > tolerance:
                raise ValueError(
                    f"Gap detected between elements {i} and {i+1}: "
                    f"end point {current_end} != start point {next_start}"
                )
    
    def _compute_alignment_properties(self):
        """Compute total alignment length and update station values"""
        
        # Set alignment start point from first element if not provided
        if self.start_point is None and self.elements:
            self.start_point = self.elements[0].get_start_point()
        
        # Calculate total length if not provided (based on geometry)
        if self.length is None:
            self.length = sum(elem.get_length() for elem in self.elements)
        
        # Update internal station values for each element if not set
        current_internal_station = self.sta_start
        
        for element in self.elements:
            if element.sta_start is None:
                # Convert internal station to displayed station
                element.sta_start = self.internal_to_station(current_internal_station)
            else:
                # Element has station, convert to internal for tracking
                current_internal_station = self.station_to_internal(element.sta_start)
            
            current_internal_station += element.get_length()
        
        # Compute stations for PI points if not provided
        self._compute_pi_stations()
    
    def _compute_pi_stations(self):
        """Compute station values for PI points based on their coordinates"""
        
        for pi in self.align_pis:
            if pi['station'] is None:
                # Try to find station by projecting PI point onto alignment
                pi['station'] = self._find_station_for_point(pi['point'])
    
    def _find_station_for_point(self, point: Tuple[float, float]) -> Optional[float]:
        """
        Find station value for a given point by projecting onto alignment elements.
        Returns the station of closest point on alignment.
        """
        
        min_distance = float('inf')
        closest_station = None
        
        # Check each element for closest projection
        for element in self.elements:
            try:
                # Project point onto element
                distance_along_element = element.project_point(point)
                
                if distance_along_element is not None:
                    # Get point on element at this distance
                    projected_point = element.get_point_at_distance(distance_along_element)
                    
                    # Calculate distance from original point to projected point
                    dx = point[0] - projected_point[0]
                    dy = point[1] - projected_point[1]
                    distance = math.sqrt(dx**2 + dy**2)
                    
                    if distance < min_distance:
                        min_distance = distance
                        # Convert element distance to alignment station
                        elem_sta_start_internal = self.station_to_internal(element.sta_start)
                        internal_station = elem_sta_start_internal + distance_along_element
                        closest_station = self.internal_to_station(internal_station)
                        
            except Exception:
                continue
        
        return closest_station

    def station_to_internal(self, station: float) -> float:
        """
        Convert displayed station to internal station (for geometry calculations).
        
        Args:
            station: Displayed station value
            
        Returns:
            Internal station value (continuous, no adjustments)
        """
        
        if not self.station_equations:
            return station
        
        # Start with the input station
        internal = station
        
        # Apply each station equation that affects this station
        for eq in self.station_equations:
            if station < eq['staBack']:
                # Station is before this equation, no adjustment needed
                break
            elif station >= eq['staAhead']:
                # Station is after this equation
                # Convert to internal by removing the adjustment
                # internal = staInternal + (station - staAhead)
                internal = eq['staInternal'] + (station - eq['staAhead'])
            else:
                # Station is in the gap between staBack and staAhead
                # This shouldn't happen in valid data, but handle it
                # Assume the station maps to staInternal
                internal = eq['staInternal']
                break
        
        return internal

    def internal_to_station(self, internal_station: float) -> float:
        """
        Convert internal station to displayed station.
        
        Args:
            internal_station: Internal station value (continuous)
            
        Returns:
            Displayed station value (with equation adjustments)
        """
        
        if not self.station_equations:
            return internal_station
        
        # Start with the input internal station
        station = internal_station
        
        # Find the last equation that affects this internal station
        for eq in self.station_equations:
            if internal_station < eq['staInternal']:
                # Internal station is before this equation, no adjustment needed
                break
            else:
                # Internal station is at or after this equation
                # Convert to displayed by applying the adjustment
                # station = staAhead + (internal - staInternal)
                station = eq['staAhead'] + (internal_station - eq['staInternal'])
        
        return station

    def get_element_at_station(self, station: float) -> Optional[Union[Line, Curve, Spiral]]:
        """
        Find geometry element at given displayed station.
        
        Args:
            station: Displayed station value to query
            
        Returns:
            Geometry element at station, or None if station is out of range
        """
        
        # Convert to internal station for geometry lookup
        internal_station = self.station_to_internal(station)
        
        sta_start_internal = self.station_to_internal(self.sta_start)
        sta_end_internal = sta_start_internal + self.length
        
        if internal_station < sta_start_internal or internal_station > sta_end_internal:
            return None
        
        for element in self.elements:
            elem_sta_start_internal = self.station_to_internal(element.sta_start)
            elem_sta_end_internal = elem_sta_start_internal + element.get_length()
            
            if elem_sta_start_internal <= internal_station <= elem_sta_end_internal:
                return element
        
        return None
    
    def get_point_at_station(self, station: float) -> Tuple[float, float]:
        """
        Get point coordinates at given displayed station along alignment.
        
        Args:
            station: Displayed station value to query
            
        Returns:
            (x, y) coordinates at station
            
        Raises:
            ValueError: If station is outside alignment range
        """
        
        # Convert to internal station
        internal_station = self.station_to_internal(station)
        
        sta_start_internal = self.station_to_internal(self.sta_start)
        sta_end_internal = sta_start_internal + self.length
        
        if internal_station < sta_start_internal:
            raise ValueError(
                f"Station {station} (internal: {internal_station:.2f}) "
                f"before alignment start {self.sta_start} (internal: {sta_start_internal:.2f})"
            )
        
        if internal_station > sta_end_internal:
            raise ValueError(
                f"Station {station} (internal: {internal_station:.2f}) "
                f"beyond alignment end (internal: {sta_end_internal:.2f})"
            )
        
        # Find element containing this internal station
        for element in self.elements:
            elem_sta_start_internal = self.station_to_internal(element.sta_start)
            elem_sta_end_internal = elem_sta_start_internal + element.get_length()
            
            if elem_sta_start_internal <= internal_station <= elem_sta_end_internal:
                distance = internal_station - elem_sta_start_internal
                global_point = element.get_point_at_distance(distance)
                
                # Transform to current coordinate system
                return self.coordinate_system.transform_to_system(global_point)
        
        raise ValueError(f"No element found at station {station}")
    
    def get_orthogonal_at_station(
        self, 
        station: float, 
        side: str = 'left'
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Get point and orthogonal vector at given displayed station.
        
        Args:
            station: Displayed station value to query
            side: Direction of orthogonal - 'left' or 'right'
            
        Returns:
            Tuple containing:
            - Point coordinates as (x, y)
            - Unit orthogonal vector as (x, y)
            
        Raises:
            ValueError: If station is outside alignment range
        """
        
        if side not in ['left', 'right']:
            raise ValueError("side must be 'left' or 'right'")
        
        # Convert to internal station
        internal_station = self.station_to_internal(station)
        
        # Find element containing this internal station
        for element in self.elements:
            elem_sta_start_internal = self.station_to_internal(element.sta_start)
            elem_sta_end_internal = elem_sta_start_internal + element.get_length()
            
            if elem_sta_start_internal <= internal_station <= elem_sta_end_internal:
                distance = internal_station - elem_sta_start_internal
                global_point, global_vector = element.get_orthogonal(distance, side)
                
                # Transform both point and vector
                point = self.coordinate_system.transform_to_system(global_point)
                vector = self.coordinate_system.transform_vector_to_system(global_vector)
                
                return point, vector
        
        raise ValueError(f"No element found at station {station}")

    def get_station_offset(self, point: Tuple[float, float], 
                          input_system: str = 'current') -> Optional[Tuple[float, float]]:
        """
        Calculates the station and offset of a point relative to the alignment.
        
        Finds the closest point on the alignment (projection) and returns
        its displayed station and the perpendicular offset distance.

        Args:
            point: (x, y) coordinates of the point to query.
            input_system: 'current' - same as alignment's system, 'global' - global coords

        Returns:
            A tuple (station, offset) if a valid projection is found, (None, None) otherwise.
            - station: Displayed station value of the closest point on the alignment.
            - offset: Perpendicular offset distance from the alignment.
                      Convention:
                      - Negative (-) value means the point is to the LEFT of the alignment.
                      - Positive (+) value means the point is to the RIGHT of the alignment.
        """
        
        # Transform input point to global if needed
        if input_system == 'current' and not self.coordinate_system.is_global():
            global_point = self.coordinate_system.transform_from_system(point)
        else:
            global_point = point

        min_offset_dist = float('inf')
        best_station = None
        best_signed_offset = None

        for element in self.elements:
            try:
                # 1. Project the point onto the element's geometry.
                # This should return the distance along the element
                # from its start point to the closest projected point.
                distance_along = element.project_point(global_point)

                if distance_along is None:
                    # The projection does not fall on this element segment
                    continue

                # 2. Get the coordinates of the projected point
                projected_point = element.get_point_at_distance(distance_along)

                # 3. Calculate the magnitude of the offset distance
                dx = global_point[0] - projected_point[0]
                dy = global_point[1] - projected_point[1]
                current_offset_dist = math.sqrt(dx**2 + dy**2)

                # 4. Check if this is the closest projection found so far
                if current_offset_dist < min_offset_dist:
                    min_offset_dist = current_offset_dist

                    # 5. Calculate the station value
                    elem_sta_start_internal = self.station_to_internal(element.sta_start)
                    internal_station = elem_sta_start_internal + distance_along
                    displayed_station = self.internal_to_station(internal_station)
                    best_station = displayed_station

                    # 6. Determine the sign of the offset (left/right)
                    if current_offset_dist < 1e-3: 
                        # Point is effectively on the alignment (within tolerance)
                        best_signed_offset = 0.0
                    else:
                        # Get the 'left' orthogonal vector at the projected point
                        _, left_ortho_vec = element.get_orthogonal(distance_along, 'left')
                        
                        # Create the vector from the projected point to the query point
                        vector_to_point = (dx, dy) 
                        
                        # Calculate the dot product
                        # If vector_to_point and left_ortho_vec are in the same direction
                        # (dot_product > 0), the point is to the LEFT.
                        dot_product = (vector_to_point[0] * left_ortho_vec[0]) + \
                                      (vector_to_point[1] * left_ortho_vec[1])
                        
                        if dot_product > 0:
                            # Point is to the LEFT (Convention: Left = Negative)
                            best_signed_offset = -current_offset_dist
                        else:
                            # Point is to the RIGHT (Convention: Right = Positive)
                            best_signed_offset = current_offset_dist
            
            except Exception:
                # Ignore any element that fails projection
                continue
        
        if best_station is not None:
            return (best_station, best_signed_offset)
        else:
            # No valid projection found on any alignment element
            return None, None

    def generate_points(self, step: float) -> List[Tuple[float, float, float]]:
        """
        Generate points along entire alignment at regular station intervals.
        
        Args:
            step: Station interval between points (in displayed station)
            
        Returns:
            List of (station, x, y) tuples (station is displayed value)
        """
        
        if step <= 0:
            raise ValueError("Step must be positive")
        
        points = []
        current_station = self.sta_start
        sta_end = self.internal_to_station(
            self.station_to_internal(self.sta_start) + self.length
        )
        
        while current_station <= sta_end:
            try:
                x, y = self.get_point_at_station(current_station)
                points.append((current_station, x, y))
            except ValueError:
                # Reached end of alignment
                break
            
            current_station += step
        
        # Ensure end point is included
        if not points or abs(points[-1][0] - sta_end) > 1e-6:
            try:
                x, y = self.get_point_at_station(sta_end)
                points.append((sta_end, x, y))
            except ValueError:
                pass
        
        return points
    
    def generate_offset_points(
        self, 
        offset: float, 
        step: float, 
        side: str = 'left'
    ) -> List[Tuple[float, float, float]]:
        """
        Generate points offset from alignment centerline.
        
        Args:
            offset: Perpendicular offset distance from centerline (positive value)
            step: Station interval between points (in displayed station)
            side: Side to offset - 'left' or 'right'
            
        Returns:
            List of (station, x, y) tuples for offset points (station is displayed value)
        """
        
        if offset < 0:
            raise ValueError("Offset must be positive")
        
        if step <= 0:
            raise ValueError("Step must be positive")
        
        if side not in ['left', 'right']:
            raise ValueError("side must be 'left' or 'right'")
        
        offset_points = []
        current_station = self.sta_start
        sta_end = self.internal_to_station(
            self.station_to_internal(self.sta_start) + self.length
        )
        
        while current_station <= sta_end:
            try:
                point, orthogonal = self.get_orthogonal_at_station(current_station, side)
                
                # Calculate offset point
                offset_x = point[0] + offset * orthogonal[0]
                offset_y = point[1] + offset * orthogonal[1]
                
                offset_points.append((current_station, offset_x, offset_y))
                
            except ValueError:
                break
            
            current_station += step
        
        # Ensure end point is included
        if not offset_points or abs(offset_points[-1][0] - sta_end) > 1e-6:
            try:
                point, orthogonal = self.get_orthogonal_at_station(sta_end, side)
                offset_x = point[0] + offset * orthogonal[0]
                offset_y = point[1] + offset * orthogonal[1]
                offset_points.append((sta_end, offset_x, offset_y))
            except ValueError:
                pass
        
        return offset_points

    def generate_stations(
        self,
        start_station: Optional[float] = None,
        end_station: Optional[float] = None,
        increments: Optional[Union[float, Dict[str, float]]] = None,
        at_geometry_points: bool = True
    ) -> List[float]:
        """
        Generate station list along alignment based on element types and increments.
        
        Args:
            start_station: Start station (displayed). If None, uses alignment start
            end_station: End station (displayed). If None, uses alignment end
            increments: Station increment(s). Can be:
                - Single float: Same increment for all elements
                - Dict with keys 'Line', 'Curve', 'Spiral': Different increments per type
                If None, uses default of 10.0 for all types
            at_geometry_points: If True, add stations at geometry transition points
            
        Returns:
            List of station values (displayed, sorted, unique)
            
        Example:
            # Single increment for all
            stations = alignment.generate_stations(increments=5.0)
            
            # Different increments per element type
            stations = alignment.generate_stations(
                increments={'Line': 20.0, 'Curve': 5.0, 'Spiral': 2.0}
            )
        """
        # Set default start/end stations
        if start_station is None:
            start_station = self.sta_start
        if end_station is None:
            end_station = self.get_sta_end()
        
        # Validate station range
        if start_station > end_station:
            raise ValueError(
                f"start_station ({start_station}) must be <= end_station ({end_station})"
            )
        
        # Validate stations are within alignment
        align_start = self.sta_start
        align_end = self.get_sta_end()
        
        if start_station < align_start or end_station > align_end:
            raise ValueError(
                f"Station range ({start_station} to {end_station}) "
                f"outside alignment range ({align_start} to {align_end})"
            )
        
        # Process increments parameter
        if increments is None:
            # Default increment
            increment_dict = {'Line': 10.0, 'Curve': 10.0, 'Spiral': 10.0}
        elif isinstance(increments, (int, float)):
            # Single increment for all types
            increment_dict = {
                'Line': float(increments),
                'Curve': float(increments),
                'Spiral': float(increments)
            }
        elif isinstance(increments, dict):
            # Use provided dictionary, fill missing with default
            increment_dict = {
                'Line': float(increments.get('Line', 10.0)),
                'Curve': float(increments.get('Curve', 10.0)),
                'Spiral': float(increments.get('Spiral', 10.0))
            }
        else:
            raise ValueError(
                "increments must be None, a number, or a dict with 'Line', 'Curve', 'Spiral' keys"
            )
        
        # Validate increments are positive
        for elem_type, inc in increment_dict.items():
            if inc <= 0:
                raise ValueError(f"Increment for {elem_type} must be positive, got {inc}")
        
        stations = set()
        
        # Always add start and end stations
        stations.add(start_station)
        stations.add(end_station)
        
        # Add geometry points if requested
        if at_geometry_points:
            for element in self.elements:
                elem_start = element.sta_start
                elem_length = element.get_length()
                elem_start_internal = self.station_to_internal(elem_start)
                elem_end_internal = elem_start_internal + elem_length
                elem_end = self.internal_to_station(elem_end_internal)
                
                # Add element start and end if within range
                if start_station <= elem_start <= end_station:
                    stations.add(elem_start)
                if start_station <= elem_end <= end_station:
                    stations.add(elem_end)
        
        # Generate regular increment stations
        # Find the first increment station >= start_station
        for element in self.elements:
            elem_type = element.get_type()
            increment = increment_dict.get(elem_type, 10.0)
            
            elem_start = element.sta_start
            elem_length = element.get_length()
            elem_start_internal = self.station_to_internal(elem_start)
            elem_end_internal = elem_start_internal + elem_length
            elem_end = self.internal_to_station(elem_end_internal)
            
            # Skip if element is completely outside requested range
            if elem_end < start_station or elem_start > end_station:
                continue
            
            # Find first increment station in this element
            # Round start_station up to nearest increment
            first_increment = math.ceil(start_station / increment) * increment
            
            # Generate stations at increment intervals
            current_station = first_increment
            
            while current_station <= end_station:
                # Check if this station is within this element's range
                current_internal = self.station_to_internal(current_station)
                
                # Check if within element bounds
                if elem_start_internal <= current_internal <= elem_end_internal:
                    stations.add(current_station)
                
                current_station += increment
        
        # Convert to sorted list
        stations_list = sorted(list(stations))
        
        return stations_list

    def get_align_pis(self) -> List[Dict]:
        """
        Return list of all alignment PI points with coordinates transformed 
        to current coordinate system.
        
        Returns:
            List of PI dictionaries with point coordinates in current coordinate system
        """
        transformed_pis = []
        
        for pi in self.align_pis:
            # Copy PI data
            pi_copy = pi.copy()
            
            # Transform point coordinates to current coordinate system
            if pi_copy['point'] is not None:
                global_point = pi_copy['point']
                pi_copy['point'] = self.coordinate_system.transform_to_system(global_point)
            
            transformed_pis.append(pi_copy)
        
        return transformed_pis


    def get_pi_at_station(self, station: float, tolerance: float = 1e-6) -> Optional[Dict]:
        """
        Find PI point at or near given station with coordinates transformed 
        to current coordinate system.
        
        Args:
            station: Station value to query
            tolerance: Maximum station difference to consider as match
            
        Returns:
            PI dictionary with point coordinates in current coordinate system if found, 
            None otherwise
        """
        for pi in self.align_pis:
            if pi['station'] is not None and abs(pi['station'] - station) <= tolerance:
                # Copy PI data
                pi_copy = pi.copy()
                
                # Transform point coordinates to current coordinate system
                if pi_copy['point'] is not None:
                    global_point = pi_copy['point']
                    pi_copy['point'] = self.coordinate_system.transform_to_system(global_point)
                
                return pi_copy
        
        return None
    
    def get_station_equations(self) -> List[Dict]:
        """Return list of all station equations"""
        return self.station_equations.copy()
    
    def get_elements(self) -> List[Union[Line, Curve, Spiral]]:
        """Return list of all geometry elements in alignment"""
        return self.elements.copy()
    
    def get_element_count(self) -> int:
        """Return number of geometry elements in alignment"""
        return len(self.elements)
    
    def get_start_point(self) -> Tuple[float, float]:
        """
        Return alignment start point coordinates in current coordinate system.
        
        Returns:
            (x, y) coordinates of alignment start point
        """
        if self.start_point is not None:
            global_point = self.start_point
        elif self.elements:
            global_point = self.elements[0].get_start_point()
        else:
            raise ValueError("Alignment has no elements")
        
        # Transform to current coordinate system
        return self.coordinate_system.transform_to_system(global_point)


    def get_end_point(self) -> Tuple[float, float]:
        """
        Return alignment end point coordinates in current coordinate system.
        
        Returns:
            (x, y) coordinates of alignment end point
        """
        if not self.elements:
            raise ValueError("Alignment has no elements")
        
        global_point = self.elements[-1].get_end_point()
        
        # Transform to current coordinate system
        return self.coordinate_system.transform_to_system(global_point)

    def get_length(self) -> float:
        """Return total alignment length (geometric, not adjusted by equations)"""
        return self.length
    
    def get_sta_start(self) -> float:
        """Return alignment start station (displayed)"""
        return self.sta_start
    
    def get_sta_end(self) -> float:
        """Return alignment end station (displayed, with equation adjustments)"""
        internal_end = self.station_to_internal(self.sta_start) + self.length
        return self.internal_to_station(internal_end)
        
    def to_dict(self) -> Dict:
        """
        Export alignment properties as dictionary.
        Note: Coordinates in the dictionary are returned in the GLOBAL coordinate system,
        regardless of the current coordinate system setting.
        
        Returns:
            Dictionary containing alignment metadata and all geometry elements
        """
        # Get points in global coordinate system for export
        global_start = self.start_point if self.start_point is not None else \
                    (self.elements[0].get_start_point() if self.elements else None)
        
        global_end = self.elements[-1].get_end_point() if self.elements else None
        
        result = {
            'name': self.name,
            'desc': self.description,
            'length': self.length,
            'staStart': self.sta_start,
            'staEnd': self.get_sta_end(),
            'start': global_start,
            'endPoint': global_end,
            'elementCount': len(self.elements),
            'piCount': len(self.align_pis),
            'stationEquationCount': len(self.station_equations),
            'AlignPIs': self.align_pis,
            'StaEquation': self.station_equations,
            'CoordGeom': [elem.to_dict() for elem in self.elements],
            'coordinateSystem': self.coordinate_system.to_dict()
        }
        
        # Add profile if present
        if self.profile is not None:
            result['Profile'] = self.profile.to_dict()
        
        return result
    
    def __repr__(self) -> str:
        """String representation of alignment"""
        pi_info = f", PIs={len(self.align_pis)}" if self.align_pis else ""
        eq_info = f", equations={len(self.station_equations)}" if self.station_equations else ""
        return (
            f"Alignment(name='{self.name}', "
            f"length={self.length:.2f}, "
            f"elements={len(self.elements)}"
            f"{pi_info}"
            f"{eq_info}, "
            f"sta_start={self.sta_start:.2f})"
        )
        
    def __str__(self) -> str:
        """Human-readable string representation"""
        pi_info = f", {len(self.align_pis)} PIs" if self.align_pis else ""
        eq_info = f", {len(self.station_equations)} equations" if self.station_equations else ""
        
        return (
            f"Alignment '{self.name}': {self.length:.2f}m, "
            f"{len(self.elements)} elements{pi_info}{eq_info}, "
            f"Sta {self.sta_start:.2f} to {self.get_sta_end():.2f}"
        )

    def __eq__(self, other) -> bool:
        """Check equality between two alignments"""
        if not isinstance(other, Alignment):
            return False
        
        return (
            self.name == other.name and
            abs(self.length - other.length) < 1e-6 and
            abs(self.sta_start - other.sta_start) < 1e-6 and
            len(self.elements) == len(other.elements) and
            all(e1 == e2 for e1, e2 in zip(self.elements, other.elements))
        )

    def __ne__(self, other) -> bool:
        """Check inequality between two alignments"""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Make alignment objects hashable"""
        return hash((
            'Alignment',
            self.name,
            round(self.length, 6),
            round(self.sta_start, 6),
            len(self.elements)
        ))

    def __len__(self) -> int:
        """Return number of geometry elements"""
        return len(self.elements)

    def __bool__(self) -> bool:
        """Alignment is True if it has elements"""
        return hasattr(self, 'elements') and len(self.elements) > 0

    def __contains__(self, station: float) -> bool:
        """Check if station is within alignment range"""
        sta_end = self.get_sta_end()
        return self.sta_start <= station <= sta_end

    def __iter__(self):
        """Iterate over geometry elements"""
        return iter(self.elements)

    def __getitem__(self, index: Union[int, slice]):
        """
        Get element by index or slice.
        Supports negative indexing.
        """
        return self.elements[index]

    def __reversed__(self):
        """Iterate over elements in reverse order"""
        return reversed(self.elements)

    def __add__(self, other):
        """
        Concatenate two alignments (not fully implemented).
        This would require complex geometry validation.
        """
        raise NotImplementedError(
            "Alignment concatenation not yet implemented. "
            "Use extend() method to manually add elements."
        )

    def __iadd__(self, other):
        """In-place addition (not implemented)"""
        raise NotImplementedError("In-place alignment addition not supported")

    def __format__(self, format_spec: str) -> str:
        """
        Custom formatting support.
        
        Format specs:
            'short' or 's' - Brief summary
            'long' or 'l' - Detailed information
            'csv' or 'c' - CSV-friendly format
        """
        if format_spec in ('short', 's', ''):
            return f"{self.name}: {self.length:.2f}m, {len(self.elements)} elements"
        elif format_spec in ('long', 'l'):
            return (
                f"Alignment: {self.name}\n"
                f"  Description: {self.description or 'N/A'}\n"
                f"  Length: {self.length:.2f}m\n"
                f"  Station: {self.sta_start:.2f} to {self.get_sta_end():.2f}\n"
                f"  Elements: {len(self.elements)}\n"
                f"  PIs: {len(self.align_pis)}\n"
                f"  Equations: {len(self.station_equations)}"
            )
        elif format_spec in ('csv', 'c'):
            return (
                f"{self.name},{self.length:.2f},{self.sta_start:.2f},"
                f"{self.get_sta_end():.2f},{len(self.elements)}"
            )
        else:
            raise ValueError(f"Unknown format specifier: {format_spec}")

    def __getstate__(self):
        """Return state for JSON serialization"""
        return self.to_dict()
    
    def __setstate__(self, state):
        """Restore state from JSON deserialization"""
        self.__init__(state)

    @staticmethod
    def from_pis(
        pi_list: List[Dict],
        name: str = "Alignment",
        sta_start: float = 0.0,
        coordinate_system: Optional[Dict] = None
    ) -> 'Alignment':
        """
        Create alignment from PI (Point of Intersection) points.
        Automatically generates geometry elements between consecutive PIs.
        
        Args:
            pi_list: List of PI dictionaries:
                {
                    'point': (x, y),
                    'radius': float (optional) - if None, creates straight line
                    'spiral_in': float (optional) - entry spiral length
                    'spiral_out': float (optional) - exit spiral length
                    'desc': str (optional)
                }
            name: Alignment name
            sta_start: Starting station value
            coordinate_system: Optional coordinate system configuration
            
        Returns:
            New Alignment instance
        """
        if len(pi_list) < 2:
            raise ValueError("At least 2 PI points required")
        
        coord_geom = []
        previous_segment_end = pi_list[0]['point']  # Start from first PI point

        for i in range(1, len(pi_list) - 1):
            pi_previous = pi_list[i - 1]
            pi_current = pi_list[i]
            pi_next = pi_list[i + 1] if i + 1 < len(pi_list) else None
            
            segment_geoms = Alignment._create_segment_geometry(
                pi_previous,
                pi_current,
                pi_next,
                previous_segment_end
            )
            
            coord_geom.extend(segment_geoms)
            
            # Track the end point of this segment for next iteration
            previous_segment_end = segment_geoms[-1]['End']

        # Handle last segment to final PI
        dist = math.sqrt(
            (pi_list[-1]['point'][0] - previous_segment_end[0])**2 + 
            (pi_list[-1]['point'][1] - previous_segment_end[1])**2
        )
        if dist > 1e-6:  # If there's a gap
            coord_geom.append({
                'Type': 'Line', 
                'Start': previous_segment_end, 
                'End': pi_list[-1]['point']
            })
        
        alignment_data = {
            'name': name,
            'staStart': sta_start,
            'CoordGeom': coord_geom,
            'AlignPIs': pi_list
        }
        
        if coordinate_system:
            alignment_data['coordinateSystem'] = coordinate_system
        
        return Alignment(alignment_data)

    @staticmethod
    def _create_segment_geometry(
        pi_previous: Dict,
        pi_current: Dict,
        pi_next: Optional[Dict],
        previous_segment_end: Optional[Tuple[float, float]] = None
    ) -> List[Dict]:
        """
        Create geometry elements between two consecutive PI points.
        Adds connecting line if there's a gap between previous segment and current segment.
        """
        pt_previous = pi_previous['point']
        pt_current = pi_current['point']
        pt_next = pi_next['point'] if pi_next else None
        
        if pt_next is None:
            # Last segment - straight line only
            elements = []
            # Check if connecting line needed from previous segment
            if previous_segment_end:
                dist = math.sqrt(
                    (pt_current[0] - previous_segment_end[0])**2 + 
                    (pt_current[1] - previous_segment_end[1])**2
                )
                if dist > 1e-6:  # If there's a gap
                    elements.append({
                        'Type': 'Line', 
                        'Start': previous_segment_end, 
                        'End': pt_current
                    })
            return elements

        # Curve parameters are at NEXT PI
        radius = pi_current.get('radius', None)
        spiral_in = pi_current.get('spiral_in', None)
        spiral_out = pi_current.get('spiral_out', None)
        
        # Calculate direction to check for minimal deflection
        dir_in = math.atan2(pt_current[1] - pt_previous[1], pt_current[0] - pt_previous[0])
        dir_out = math.atan2(pt_current[1] - pt_next[1], pt_current[0] - pt_next[0])

        # Calculate deflection angle
        delta = dir_out - dir_in
        while delta > math.pi:
            delta -= 2 * math.pi
        while delta < -math.pi:
            delta += 2 * math.pi
        
        # Straight line if no curve or minimal deflection
        if abs(delta) < 1e-6 or radius is None:
            elements = []
            # Check if connecting line needed from previous segment
            if previous_segment_end:
                dist = math.sqrt(
                    (pt_current[0] - previous_segment_end[0])**2 + 
                    (pt_current[1] - previous_segment_end[1])**2
                )
                if dist > 1e-6:  # If there's a gap
                    elements.append({
                        'Type': 'Line', 
                        'Start': previous_segment_end, 
                        'End': pt_current
                    })
            return elements
        
        curve_elements = Alignment._create_curve_geometry(
            pt_previous,pt_current, pt_next,
            radius, spiral_in, spiral_out)
        
        # Add connecting line if there's a gap from previous segment to first element of current segment
        if previous_segment_end and curve_elements:
            first_element_start = curve_elements[0]['Start']
            dist = math.sqrt(
                (first_element_start[0] - previous_segment_end[0])**2 + 
                (first_element_start[1] - previous_segment_end[1])**2
            )
            if dist > 1e-6:  # If there's a gap
                # Insert connecting line at the beginning
                curve_elements.insert(0, {
                    'Type': 'Line', 
                    'Start': previous_segment_end, 
                    'End': first_element_start
                })
        
        return curve_elements

    @staticmethod
    def _create_curve_geometry(
        pt_start: Tuple[float, float],
        pt_pi: Tuple[float, float],
        pt_end: Tuple[float, float],
        radius: float,
        spiral_in_length: float,
        spiral_out_length: float,
    ) -> List[Dict]:
        """
        Create Spiral + Curve + Spiral geometry.
        Handles cases where spirals can be zero (simple curve) or only one spiral exists.
        
        Args:
            pt_start: Starting point of the segment
            pt_pi: Point of Intersection
            pt_end: End point of the segment (next PI or alignment end)
            radius: Curve radius
            spiral_in_length: Entry spiral length (can be 0 or None)
            spiral_out_length: Exit spiral length (can be 0 or None)
            is_first_segment: True if this is the first segment in alignment
            
        Returns:
            List of geometry element dictionaries
        """
        from scipy.special import fresnel
        
        elements = []
        
        # Calculate incoming direction (from start to PI)
        dir_in = math.atan2(pt_pi[1] - pt_start[1], pt_pi[0] - pt_start[0])
        
        # Calculate outgoing direction (from PI to end)
        dir_out = math.atan2(pt_end[1] - pt_pi[1], pt_end[0] - pt_pi[0])
        
        # Calculate deflection angle
        delta = dir_out - dir_in
        
        # Normalize delta to [-π, π]
        while delta > math.pi:
            delta -= 2 * math.pi
        while delta < -math.pi:
            delta += 2 * math.pi
        
        # Determine rotation direction
        if delta > 0:
            rotation = 'cw'
        else:
            rotation = 'ccw'
        
        # Use absolute value of delta for calculations
        delta_abs = abs(delta)
        
        # Normalize spiral lengths (treat None or negative as zero)
        spiral_in_length = max(0.0, spiral_in_length or 0.0)
        spiral_out_length = max(0.0, spiral_out_length or 0.0)

        # Calculate spiral angles
        theta_in = spiral_in_length / (2 * radius) if spiral_in_length > 0 else 0.0
        theta_out = spiral_out_length / (2 * radius) if spiral_out_length > 0 else 0.0
        
        # Calculate entry spiral parameters
        if spiral_in_length > 0:
            A_in = math.sqrt(spiral_in_length * radius * math.pi)
            t_in = spiral_in_length / A_in
            S_in, C_in = fresnel(t_in)
            x_in = A_in * C_in
            y_in = A_in * S_in
            cx_in = x_in - radius * math.sin(theta_in)
            cy_in = y_in + radius * math.cos(theta_in)
            tangent_in = cy_in * math.tan(delta_abs / 2) + cx_in
            long_in = x_in - y_in / math.tan(theta_in)

        else:
            x_in = 0.0
            y_in = 0.0
            tangent_in = radius / math.tan(delta_abs / 2)
        
        # Calculate exit spiral parameters
        if spiral_out_length > 0:
            A_out = math.sqrt(spiral_out_length * radius * math.pi)
            t_out = spiral_out_length / A_out
            S_out, C_out = fresnel(t_out)
            x_out = A_out * C_out
            y_out = A_out * S_out
            cx_out = x_out - radius * math.sin(theta_out)
            cy_out = y_out + radius * math.cos(theta_out)
            tangent_out = cy_out * math.tan(delta_abs / 2) + cx_out
            long_out = x_out - y_out / math.tan(theta_out)

        else:
            x_out = 0.0
            y_out = 0.0
            tangent_out = radius / math.tan(delta_abs / 2)
        
        # Remaining curve angle
        delta_curve = delta_abs - theta_in - theta_out
        if delta_curve < 0:
            raise ValueError(
                f"Spiral lengths too long: total spiral angle ({theta_in + theta_out:.4f}) "
                f"exceeds deflection angle ({delta_abs:.4f})"
            )

        # TS (Tangent to Spiral) or TC (Tangent to Curve) point
        ts_x = pt_pi[0] - tangent_in * math.cos(dir_in)
        ts_y = pt_pi[1] - tangent_in * math.sin(dir_in)
        
        sign = 1 if rotation == 'cw' else -1
        cos_in = math.cos(dir_in)
        sin_in = math.sin(dir_in)
        
        # SC (Spiral to Curve) or same as TS if no entry spiral
        if spiral_in_length > 0:
            sc_x = ts_x + x_in * cos_in - sign * y_in * sin_in
            sc_y = ts_y + x_in * sin_in + sign * y_in * cos_in
            dir_sc = dir_in + sign * theta_in
        else:
            sc_x = ts_x
            sc_y = ts_y
            dir_sc = dir_in
        
        # Curve center
        center_angle = dir_sc + math.pi / 2 if rotation == 'cw' else dir_sc - math.pi / 2
        center_x = sc_x + radius * math.cos(center_angle)
        center_y = sc_y + radius * math.sin(center_angle)
        
        # CS (Curve to Spiral) or CT (Curve to Tangent) point
        dir_cs = dir_out - sign * theta_out
        cs_angle = center_angle + delta_curve if rotation == 'cw' else center_angle - delta_curve
        cs_x = center_x + radius * math.cos(cs_angle - math.pi)
        cs_y = center_y + radius * math.sin(cs_angle - math.pi)
        
        # ST (Spiral to Tangent) or same as CS if no exit spiral
        if spiral_out_length > 0:
            cos_out = math.cos(dir_out)
            sin_out = math.sin(dir_out)
            st_x = cs_x + x_out * cos_out + sign * y_out * sin_out
            st_y = cs_y + x_out * sin_out - sign * y_out * cos_out
        else:
            st_x = cs_x
            st_y = cs_y
        
        # Entry spiral (only if length > 0)
        if spiral_in_length > 0:
            # Entry spiral PI is at the tangent intersection
            pi_in_x = ts_x + long_in * math.cos(dir_in)
            pi_in_y = ts_y + long_in * math.sin(dir_in)

            elements.append({
                'Type': 'Spiral',
                'Start': (ts_x, ts_y),
                'End': (sc_x, sc_y),
                'PI': (pi_in_x, pi_in_y),
                'length': spiral_in_length,
                'radiusStart': float('inf'),
                'radiusEnd': radius,
                'rot': rotation
            })
        
        # Circular curve (always present)
        elements.append({
            'Type': 'Curve',
            'Start': (sc_x, sc_y),
            'End': (cs_x, cs_y),
            'Center': (center_x, center_y),
            'PI': pt_pi,
            'rot': rotation
        })
        
        # Exit spiral (only if length > 0)
        if spiral_out_length > 0:
            # Exit spiral PI is at the tangent intersection
            pi_out_x = st_x - long_in * math.cos(dir_out)
            pi_out_y = st_y - long_in * math.sin(dir_out)

            elements.append({
                'Type': 'Spiral',
                'Start': (cs_x, cs_y),
                'End': (st_x, st_y),
                'PI': (pi_out_x, pi_out_y),
                'length': spiral_out_length,
                'radiusStart': radius,
                'radiusEnd': float('inf'),
                'rot': rotation
            })
        
        return elements
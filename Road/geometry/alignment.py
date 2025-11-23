# SPDX-License-Identifier: LGPL-2.1-or-later

import math
from typing import Dict, List, Tuple, Optional, Union
from ..functions.coordinate_system import CoordinateSystem
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
                  Expected structure:
                  {
                      'name': str,
                      'desc': str (optional),
                      'length': float,
                      'staStart': float,
                      'start': (x, y) (optional) - alignment start point,
                      'AlignPIs': [  # optional - Point of Intersection points
                          {
                              'station': float (optional),
                              'point': (x, y),
                              'desc': str (optional)
                          },
                          ...
                      ],
                      'StaEquation': [  # optional
                          {
                              'staAhead': float,
                              'staBack': float,
                              'staInternal': float (optional),
                              'desc': str (optional)
                          },
                          ...
                      ],
                      'CoordGeom': [
                          {geometry element data},
                          ...
                      ]
                  }
        """
        # Alignment metadata
        self.name = data.get('name', None)
        self.description = data.get('desc', None)
        self.length = float(data['length']) if 'length' in data else None
        self.sta_start = float(data['staStart']) if 'staStart' in data else 0.0
        
        # Alignment start point (optional)
        self.start_point = data.get('start', None)

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
        
        # Geometry elements list
        self.elements: List[Union[Line, Curve, Spiral]] = []
        
        # Parse coordinate geometry elements
        if 'CoordGeom' in data and data['CoordGeom']:
            self._parse_coord_geom(data['CoordGeom'])
        
        # Validate and compute alignment properties
        self._validate_alignment()
        self._compute_alignment_properties()
    
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
        
        return {
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
        return len(self.elements) > 0

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
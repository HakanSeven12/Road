# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Tuple, Optional, List, Union, Dict
from pyproj import CRS, Transformer
from pyproj.exceptions import CRSError
import pyproj


class CoordinateSystem:
    """
    Coordinate system handler using pyproj for coordinate transformations.
    Supports EPSG codes, WKT strings, and coordinate transformations between systems.
    """
    def __init__(self, coord_sys_data: Optional[dict] = None):
        """
        Initialize coordinate system from LandXML coordinate system data.
        
        Args:
            coord_sys_data: Dictionary containing coordinate system info from LandXML
                        Can include 'wkt', 'epsgCode', 'ogcWktCode', 'name', etc.
        """
        self.coord_sys_data = coord_sys_data or {}
        self.crs = None
        self.epsg_code = None
        self.wkt_code = None
        self.name = self.coord_sys_data.get('name', 'Unknown')
        
        # Try to initialize CRS from available data
        self._initialize_crs()

    def _initialize_crs(self):
        """Initialize CRS object from available coordinate system data"""
        
        # Priority 1: Try WKT from LandXML reader (most reliable)
        if 'wkt' in self.coord_sys_data:
            try:
                self.crs = CRS.from_wkt(self.coord_sys_data['wkt'])
                self.wkt_code = self.coord_sys_data['wkt']
                return
            except CRSError as e:
                print(f"Warning: Failed to create CRS from stored WKT - {str(e)}")
        
        # Priority 2: Try EPSG code from main level
        if 'epsgCode' in self.coord_sys_data:
            self.epsg_code = self.coord_sys_data['epsgCode']
            try:
                self.crs = CRS.from_epsg(int(self.epsg_code))
                return
            except (ValueError, CRSError) as e:
                print(f"Warning: Failed to create CRS from EPSG:{self.epsg_code} - {str(e)}")
        
        # Priority 3: Try EPSG code from HorizontalCoordinateSystem
        if 'HorizontalCoordinateSystem' in self.coord_sys_data:
            horiz_cs = self.coord_sys_data['HorizontalCoordinateSystem']
            if 'epsgCode' in horiz_cs:
                self.epsg_code = horiz_cs['epsgCode']
                try:
                    self.crs = CRS.from_epsg(int(self.epsg_code))
                    return
                except (ValueError, CRSError) as e:
                    print(f"Warning: Failed to create CRS from EPSG:{self.epsg_code} - {str(e)}")
        
        # Priority 4: Try OGC WKT code
        if 'ogcWktCode' in self.coord_sys_data:
            self.wkt_code = self.coord_sys_data['ogcWktCode']
            try:
                self.crs = CRS.from_wkt(self.wkt_code)
                return
            except CRSError as e:
                print(f"Warning: Failed to create CRS from WKT - {str(e)}")
        
        # Priority 5: Try WKT from HorizontalCoordinateSystem
        if 'HorizontalCoordinateSystem' in self.coord_sys_data:
            horiz_cs = self.coord_sys_data['HorizontalCoordinateSystem']
            if 'ogcWktCode' in horiz_cs:
                self.wkt_code = horiz_cs['ogcWktCode']
                try:
                    self.crs = CRS.from_wkt(self.wkt_code)
                    return
                except CRSError as e:
                    print(f"Warning: Failed to create CRS from WKT - {str(e)}")
        
        # If no CRS could be initialized
        if self.crs is None:
            print("Warning: Could not initialize coordinate system from available data")

    def set_crs_from_epsg(self, epsg_code: Union[int, str]):
        """
        Set coordinate system from EPSG code.
        
        Args:
            epsg_code: EPSG code (e.g., 4326 for WGS84, 3857 for Web Mercator)
        """
        try:
            self.epsg_code = str(epsg_code)
            self.crs = CRS.from_epsg(int(epsg_code))
            self.name = self.crs.name
        except (ValueError, CRSError) as e:
            raise ValueError(f"Failed to create CRS from EPSG:{epsg_code} - {str(e)}")
    
    def set_crs_from_wkt(self, wkt_string: str):
        """
        Set coordinate system from WKT string.
        
        Args:
            wkt_string: Well-Known Text representation of coordinate system
        """
        try:
            self.wkt_code = wkt_string
            self.crs = CRS.from_wkt(wkt_string)
            self.name = self.crs.name
        except CRSError as e:
            raise ValueError(f"Failed to create CRS from WKT - {str(e)}")
    
    def is_valid(self) -> bool:
        """
        Check if coordinate system is valid and usable.
        
        Returns:
            True if CRS is initialized, False otherwise
        """
        return self.crs is not None
    
    def get_epsg_code(self) -> Optional[str]:
        """
        Get EPSG code if available.
        
        Returns:
            EPSG code as string or None
        """
        if self.crs and self.crs.to_epsg():
            return str(self.crs.to_epsg())
        return self.epsg_code
    
    def get_name(self) -> str:
        """
        Get coordinate system name.
        
        Returns:
            Name of the coordinate system
        """
        if self.crs:
            return self.crs.name
        return self.name
    
    def get_authority(self) -> Optional[str]:
        """
        Get the authority (e.g., 'EPSG') of the CRS.
        
        Returns:
            Authority name or None
        """
        if self.crs and self.crs.to_authority():
            return self.crs.to_authority()[0]
        return None
    
    def is_geographic(self) -> bool:
        """
        Check if coordinate system is geographic (lat/lon).
        
        Returns:
            True if geographic, False if projected or None if unknown
        """
        if self.crs:
            return self.crs.is_geographic
        return False
    
    def is_projected(self) -> bool:
        """
        Check if coordinate system is projected (e.g., UTM).
        
        Returns:
            True if projected, False if geographic or None if unknown
        """
        if self.crs:
            return self.crs.is_projected
        return False
    
    def get_axis_info(self) -> List[dict]:
        """
        Get information about coordinate axes.
        
        Returns:
            List of dictionaries with axis information
        """
        if not self.crs:
            return []
        
        axis_info = []
        for axis in self.crs.axis_info:
            axis_info.append({
                'name': axis.name,
                'abbrev': axis.abbrev,
                'direction': axis.direction,
                'unit_name': axis.unit_name
            })
        return axis_info
    
    def create_transformer_to(self, target_epsg: Union[int, str], 
                             always_xy: bool = True) -> Optional[Transformer]:
        """
        Create a transformer to convert coordinates to target coordinate system.
        
        Args:
            target_epsg: Target EPSG code
            always_xy: If True, accept x,y (easting, northing) order
                      If False, use traditional lat,lon order for geographic CRS
        
        Returns:
            Transformer object or None if source CRS is not valid
        """
        if not self.is_valid():
            print("Error: Source coordinate system is not valid")
            return None
        
        try:
            target_crs = CRS.from_epsg(int(target_epsg))
            transformer = Transformer.from_crs(
                self.crs, 
                target_crs, 
                always_xy=always_xy
            )
            return transformer
        except (ValueError, CRSError) as e:
            print(f"Error: Failed to create transformer - {str(e)}")
            return None
    
    def create_transformer_from(self, source_epsg: Union[int, str],
                               always_xy: bool = True) -> Optional[Transformer]:
        """
        Create a transformer to convert coordinates from source coordinate system to this system.
        
        Args:
            source_epsg: Source EPSG code
            always_xy: If True, accept x,y (easting, northing) order
        
        Returns:
            Transformer object or None if target CRS is not valid
        """
        if not self.is_valid():
            print("Error: Target coordinate system is not valid")
            return None
        
        try:
            source_crs = CRS.from_epsg(int(source_epsg))
            transformer = Transformer.from_crs(
                source_crs,
                self.crs,
                always_xy=always_xy
            )
            return transformer
        except (ValueError, CRSError) as e:
            print(f"Error: Failed to create transformer - {str(e)}")
            return None
    
    def transform_to(self, x: float, y: float, z: Optional[float] = None,
                    target_epsg: Union[int, str] = None) -> Tuple:
        """
        Transform coordinates to target coordinate system.
        
        Args:
            x: X coordinate (easting or longitude)
            y: Y coordinate (northing or latitude)
            z: Z coordinate (elevation), optional
            target_epsg: Target EPSG code
        
        Returns:
            Transformed coordinates as (x, y) or (x, y, z) tuple
        """
        transformer = self.create_transformer_to(target_epsg)
        if transformer is None:
            raise ValueError("Failed to create transformer")
        
        if z is not None:
            return transformer.transform(x, y, z)
        else:
            return transformer.transform(x, y)
    
    def transform_from(self, x: float, y: float, z: Optional[float] = None,
                      source_epsg: Union[int, str] = None) -> Tuple:
        """
        Transform coordinates from source coordinate system to this system.
        
        Args:
            x: X coordinate in source system
            y: Y coordinate in source system
            z: Z coordinate (elevation), optional
            source_epsg: Source EPSG code
        
        Returns:
            Transformed coordinates as (x, y) or (x, y, z) tuple
        """
        transformer = self.create_transformer_from(source_epsg)
        if transformer is None:
            raise ValueError("Failed to create transformer")
        
        if z is not None:
            return transformer.transform(x, y, z)
        else:
            return transformer.transform(x, y)
    
    def transform_points_to(self, points: List[Tuple], 
                           target_epsg: Union[int, str]) -> List[Tuple]:
        """
        Transform multiple points to target coordinate system.
        
        Args:
            points: List of (x, y) or (x, y, z) tuples
            target_epsg: Target EPSG code
        
        Returns:
            List of transformed coordinate tuples
        """
        transformer = self.create_transformer_to(target_epsg)
        if transformer is None:
            raise ValueError("Failed to create transformer")
        
        transformed_points = []
        for point in points:
            if len(point) == 3:
                result = transformer.transform(point[0], point[1], point[2])
            else:
                result = transformer.transform(point[0], point[1])
            transformed_points.append(result)
        
        return transformed_points
    
    def get_info(self) -> dict:
        """
        Get comprehensive information about the coordinate system.
        
        Returns:
            Dictionary with coordinate system information
        """
        info = {
            'name': self.get_name(),
            'epsg_code': self.get_epsg_code(),
            'authority': self.get_authority(),
            'is_valid': self.is_valid(),
            'is_geographic': self.is_geographic() if self.is_valid() else None,
            'is_projected': self.is_projected() if self.is_valid() else None,
            'axis_info': self.get_axis_info()
        }
        
        # Add original LandXML data
        if self.coord_sys_data:
            info['landxml_data'] = self.coord_sys_data
        
        return info
    
    def __repr__(self) -> str:
        """String representation of coordinate system"""
        if self.is_valid():
            epsg = self.get_epsg_code()
            if epsg:
                return f"CoordinateSystem(EPSG:{epsg}, {self.get_name()})"
            return f"CoordinateSystem({self.get_name()})"
        return "CoordinateSystem(Invalid)"
    
    def __str__(self) -> str:
        """User-friendly string representation"""
        return self.__repr__()
    
    @staticmethod
    def get_country_list() -> List[str]:
        """
        Get list of all available countries/regions with coordinate systems.
        
        Returns:
            Sorted list of country names
        """
        countries = set()
        
        # Get all projected CRS
        crs_list = pyproj.database.query_crs_info(
            auth_name="EPSG",
            pj_types=[pyproj.enums.PJType.PROJECTED_CRS]
        )
        
        for crs_info in crs_list:
            if crs_info.area_of_use and crs_info.area_of_use.name:
                # Split area names that contain multiple countries
                area_name = crs_info.area_of_use.name
                
                # Handle common separators
                if ' - ' in area_name:
                    parts = area_name.split(' - ')
                    countries.add(parts[0].strip())
                elif ' and ' in area_name:
                    parts = area_name.split(' and ')
                    for part in parts:
                        countries.add(part.strip())
                else:
                    countries.add(area_name.strip())
        
        return sorted(list(countries))
    
    @staticmethod
    def get_crs_by_country(country_name: str, 
                          include_geographic: bool = False,
                          include_deprecated: bool = False) -> List[Dict]:
        """
        Get all coordinate systems for a specific country.
        
        Args:
            country_name: Country or region name (e.g., 'Turkey', 'United States')
            include_geographic: Include geographic (lat/lon) coordinate systems
            include_deprecated: Include deprecated coordinate systems
        
        Returns:
            List of dictionaries with CRS information:
            {
                'code': EPSG code,
                'name': CRS name,
                'type': 'projected' or 'geographic',
                'area': area of use name,
                'deprecated': True/False
            }
        """
        result = []
        
        # Define CRS types to query
        pj_types = [pyproj.enums.PJType.PROJECTED_CRS]
        if include_geographic:
            pj_types.append(pyproj.enums.PJType.GEOGRAPHIC_2D_CRS)
            pj_types.append(pyproj.enums.PJType.GEOGRAPHIC_3D_CRS)
        
        # Query CRS database
        crs_list = pyproj.database.query_crs_info(
            auth_name="EPSG",
            pj_types=pj_types
        )
        
        # Filter by country name
        country_lower = country_name.lower()
        
        for crs_info in crs_list:
            # Skip deprecated if requested
            if not include_deprecated and crs_info.deprecated:
                continue
            
            # Check if country name matches
            if crs_info.area_of_use and crs_info.area_of_use.name:
                area_lower = crs_info.area_of_use.name.lower()
                
                # Check if country name is in area description
                if country_lower in area_lower:
                    crs_type = 'geographic' if 'GEOGRAPHIC' in crs_info.type.name else 'projected'
                    
                    result.append({
                        'code': crs_info.code,
                        'name': crs_info.name,
                        'type': crs_type,
                        'area': crs_info.area_of_use.name,
                        'deprecated': crs_info.deprecated,
                        'bounds': {
                            'west': crs_info.area_of_use.west,
                            'south': crs_info.area_of_use.south,
                            'east': crs_info.area_of_use.east,
                            'north': crs_info.area_of_use.north
                        } if crs_info.area_of_use else None
                    })
        
        # Sort by EPSG code
        result.sort(key=lambda x: int(x['code']))
        
        return result
    
    @staticmethod
    def search_crs(search_term: str, 
                   max_results: int = 50,
                   include_deprecated: bool = False) -> List[Dict]:
        """
        Search for coordinate systems by name or description.
        
        Args:
            search_term: Search term (e.g., 'UTM', 'WGS84', 'Turkey')
            max_results: Maximum number of results to return
            include_deprecated: Include deprecated coordinate systems
        
        Returns:
            List of dictionaries with CRS information
        """
        result = []
        search_lower = search_term.lower()
        
        # Query all CRS types
        crs_list = pyproj.database.query_crs_info(auth_name="EPSG")
        
        for crs_info in crs_list:
            # Skip deprecated if requested
            if not include_deprecated and crs_info.deprecated:
                continue
            
            # Search in name and area
            name_match = search_lower in crs_info.name.lower()
            area_match = False
            
            if crs_info.area_of_use and crs_info.area_of_use.name:
                area_match = search_lower in crs_info.area_of_use.name.lower()
            
            if name_match or area_match:
                crs_type = 'geographic' if 'GEOGRAPHIC' in crs_info.type.name else 'projected'
                
                result.append({
                    'code': crs_info.code,
                    'name': crs_info.name,
                    'type': crs_type,
                    'area': crs_info.area_of_use.name if crs_info.area_of_use else 'Unknown',
                    'deprecated': crs_info.deprecated
                })
                
                # Limit results
                if len(result) >= max_results:
                    break
        
        return result
    
    @staticmethod
    def get_utm_zone_for_location(longitude: float, latitude: float) -> Dict:
        """
        Get appropriate UTM zone for a given location.
        
        Args:
            longitude: Longitude in decimal degrees
            latitude: Latitude in decimal degrees
        
        Returns:
            Dictionary with UTM zone information and EPSG code
        """
        # Calculate UTM zone number
        zone_number = int((longitude + 180) / 6) + 1
        
        # Determine hemisphere
        hemisphere = 'north' if latitude >= 0 else 'south'
        
        # Calculate EPSG code
        # Northern hemisphere: 32600 + zone_number (WGS84)
        # Southern hemisphere: 32700 + zone_number (WGS84)
        if hemisphere == 'north':
            epsg_code = 32600 + zone_number
        else:
            epsg_code = 32700 + zone_number
        
        return {
            'zone_number': zone_number,
            'hemisphere': hemisphere,
            'epsg_code': epsg_code,
            'name': f'WGS 84 / UTM zone {zone_number}{hemisphere[0].upper()}'
        }
    
    def to_dict(self) -> Dict:
        """
        Convert CoordinateSystem to dictionary representation.
        Useful for serialization and storage.
        
        Returns:
            Dictionary containing all coordinate system data
        """
        result = {
            'coord_sys_data': self.coord_sys_data,
            'epsg_code': self.epsg_code,
            'wkt_code': self.wkt_code,
            'name': self.name
        }
        
        # Add CRS WKT representation if available
        if self.crs is not None:
            try:
                result['crs_wkt'] = self.crs.to_wkt()
            except Exception:
                pass
        
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'CoordinateSystem':
        """
        Create CoordinateSystem from dictionary representation.
        
        Args:
            data: Dictionary containing coordinate system data
            
        Returns:
            CoordinateSystem instance
        """
        coord_sys_data = data.get('coord_sys_data', {})
        instance = cls(coord_sys_data)
        
        # Try to restore from stored WKT if CRS initialization failed
        if instance.crs is None and 'crs_wkt' in data:
            try:
                instance.crs = CRS.from_wkt(data['crs_wkt'])
            except CRSError:
                pass
        
        return instance

    def __getstate__(self) -> Dict:
        """
        Prepare CoordinateSystem for pickling.
        CRS objects cannot be pickled directly, so we store WKT representation.
        
        Returns:
            Dictionary of picklable state
        """
        state = self.__dict__.copy()
        
        # Store CRS as WKT string instead of CRS object
        if self.crs is not None:
            try:
                state['_crs_wkt'] = self.crs.to_wkt()
            except Exception:
                state['_crs_wkt'] = None
        else:
            state['_crs_wkt'] = None
        
        # Remove unpicklable CRS object
        state['crs'] = None
        
        return state

    def __setstate__(self, state: Dict):
        """
        Restore CoordinateSystem from pickled state.
        Reconstructs CRS object from WKT representation.
        
        Args:
            state: Dictionary of pickled state
        """
        self.__dict__.update(state)
        
        # Restore CRS from WKT if available
        _crs_wkt = state.get('_crs_wkt')
        if _crs_wkt:
            try:
                self.crs = CRS.from_wkt(_crs_wkt)
            except CRSError as e:
                print(f"Warning: Failed to restore CRS from pickled state: {str(e)}")
                self.crs = None
        else:
            # Try to reinitialize CRS from coord_sys_data
            self._initialize_crs()
"""
LandXML Coordinate System Integration Module
Provides coordinate system management and transformation using pyproj
"""

from pyproj import CRS, Transformer
from typing import Optional, Tuple, List
import xml.etree.ElementTree as ET


class CoordinateSystem:
    """
    Handles coordinate system definitions and transformations for LandXML files.
    Supports EPSG codes, WKT definitions, and custom coordinate system parameters.
    """
    
    def __init__(self):
        """Initialize the coordinate system manager"""
        self.source_crs: Optional[CRS] = None
        self.target_crs: Optional[CRS] = None
        self.transformer: Optional[Transformer] = None
        self.system_name: str = ""
        self.description: str = ""
        
    def set_source_crs_from_epsg(self, epsg_code: int) -> bool:
        """
        Set source coordinate system from EPSG code
        
        Args:
            epsg_code: EPSG code (e.g., 4326 for WGS84)
            
        Returns:
            True if successful
        """
        try:
            self.source_crs = CRS.from_epsg(epsg_code)
            self.system_name = f"EPSG:{epsg_code}"
            return True
        except Exception as e:
            print(f"Error setting EPSG code {epsg_code}: {e}")
            return False
    
    def set_source_crs_from_wkt(self, wkt: str) -> bool:
        """
        Set source coordinate system from WKT string
        
        Args:
            wkt: Well-Known Text representation of coordinate system
            
        Returns:
            True if successful
        """
        try:
            self.source_crs = CRS.from_wkt(wkt)
            return True
        except Exception as e:
            print(f"Error parsing WKT: {e}")
            return False
    
    def set_target_crs_from_epsg(self, epsg_code: int) -> bool:
        """
        Set target coordinate system for transformations
        
        Args:
            epsg_code: Target EPSG code
            
        Returns:
            True if successful
        """
        try:
            self.target_crs = CRS.from_epsg(epsg_code)
            self._update_transformer()
            return True
        except Exception as e:
            print(f"Error setting target EPSG code {epsg_code}: {e}")
            return False
    
    def _update_transformer(self):
        """Update the transformer when source or target CRS changes"""
        if self.source_crs and self.target_crs:
            self.transformer = Transformer.from_crs(
                self.source_crs, 
                self.target_crs, 
                always_xy=True
            )
    
    def transform_point(self, x: float, y: float, z: float = 0.0) -> Tuple[float, float, float]:
        """
        Transform a single point from source to target coordinate system
        
        Args:
            x: X coordinate (or longitude)
            y: Y coordinate (or latitude)
            z: Z coordinate (elevation)
            
        Returns:
            Tuple of transformed (x, y, z) coordinates
        """
        if not self.transformer:
            raise ValueError("Transformer not initialized. Set both source and target CRS.")
        
        x_new, y_new = self.transformer.transform(x, y)
        return (x_new, y_new, z)
    
    def transform_points(self, points: List[Tuple[float, float, float]]) -> List[Tuple[float, float, float]]:
        """
        Transform multiple points from source to target coordinate system
        
        Args:
            points: List of (x, y, z) coordinate tuples
            
        Returns:
            List of transformed (x, y, z) coordinate tuples
        """
        if not self.transformer:
            raise ValueError("Transformer not initialized. Set both source and target CRS.")
        
        transformed = []
        for x, y, z in points:
            x_new, y_new = self.transformer.transform(x, y)
            transformed.append((x_new, y_new, z))
        
        return transformed
    
    def get_source_crs_info(self) -> dict:
        """
        Get information about the source coordinate system
        
        Returns:
            Dictionary with CRS information
        """
        if not self.source_crs:
            return {}
        
        return {
            'name': self.system_name or self.source_crs.name,
            'type': self.source_crs.type_name,
            'is_geographic': self.source_crs.is_geographic,
            'is_projected': self.source_crs.is_projected,
            'units': self.source_crs.axis_info[0].unit_name if self.source_crs.axis_info else None,
            'wkt': self.source_crs.to_wkt()
        }
    
    def export_to_landxml(self) -> str:
        """
        Export current coordinate system as LandXML fragment
        
        Returns:
            XML string representation
        """
        if not self.source_crs:
            return ""
        
        # Try to get EPSG code
        epsg = None
        if self.source_crs.to_authority():
            auth, code = self.source_crs.to_authority()
            if auth == 'EPSG':
                epsg = code
        
        if epsg:
            xml = f'<CoordinateSystem name="{self.system_name}" epsgCode="{epsg}"'
        else:
            xml = f'<CoordinateSystem name="{self.system_name}"'
        
        if self.description:
            xml += f' desc="{self.description}"'
        
        xml += ' />'
        return xml
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
LandXML Surface Parser
Handles parsing of Surface elements (TIN surfaces) from LandXML files.
"""

from typing import Dict, List
import xml.etree.ElementTree as ET
from .landxml_config import (
    SURFACE_CONFIG,
    FACE_CONFIG
)


class SurfaceParser:
    """
    Parser for LandXML Surface elements.
    Handles TIN surfaces with points (P) and faces (F) elements.
    """
    
    def __init__(self, reader):
        """
        Initialize surface parser with reference to main reader.
        
        Args:
            reader: LandXMLReader instance for accessing helper methods
        """
        self.reader = reader
    
    def parse_surface_points(self, surface_elem: ET.Element) -> List[Dict]:
        """
        Parse P (Point) elements within a Surface Definition element.
        
        Args:
            surface_elem: Surface Definition XML element
            
        Returns:
            List of point dictionaries with id and coordinates
        """
        points = []
        
        # First find the Pnts container element
        pnts_elem = self.reader._find_element(surface_elem, 'Pnts')
        if pnts_elem is None:
            return points
        
        # Find all P elements within Pnts
        p_elements = self.reader._find_all_elements(pnts_elem, 'P')
        
        for p_elem in p_elements:
            try:
                # Get point ID
                point_id = p_elem.attrib.get('id')
                if not point_id:
                    continue
                
                # Get point coordinates from text
                point_text = p_elem.text
                if not point_text:
                    continue
                
                coords = self.reader._parse_point(point_text.strip())
                if coords:
                    point_data = {
                        'id': point_id,
                        'easting': coords[1],
                        'northing': coords[0]
                    }
                    
                    # Add elevation if present
                    if len(coords) >= 3:
                        point_data['elevation'] = coords[2]
                    
                    points.append(point_data)
                    
            except Exception as e:
                print(f"Warning: Failed to parse surface point: {str(e)}")
                continue
        
        return points
    
    def parse_surface_faces(self, surface_elem: ET.Element) -> List[Dict]:
        """
        Parse F (Face) elements within a Surface Definition element.
        
        Args:
            surface_elem: Surface Definition XML element
            
        Returns:
            List of face dictionaries with point references
        """
        faces = []
        
        # First find the Faces container element
        faces_elem = self.reader._find_element(surface_elem, 'Faces')
        if faces_elem is None:
            return faces
        
        # Find all F elements within Faces
        f_elements = self.reader._find_all_elements(faces_elem, 'F')
        
        for f_elem in f_elements:
            try:
                face_text = f_elem.text
                if not face_text:
                    continue
                
                # Parse point IDs (typically 3 for triangular faces)
                point_ids = face_text.strip().split()
                if len(point_ids) < 3:
                    continue

                # Check invisible flag
                is_invisible = (f_elem.attrib.get('i') == "1")

                face_data = {
                    "points": point_ids,
                    "n": f_elem.attrib.get("n"),
                    "invisible": is_invisible
                }

                faces.append(face_data)

            except Exception as e:
                print(f"Warning: Failed to parse surface face: {str(e)}")
                continue

        return faces
    
    def parse_surface(self, surface_elem: ET.Element) -> Dict:
        """
        Parse single Surface element.
        
        Args:
            surface_elem: XML element representing a Surface
            
        Returns:
            Dictionary with parsed Surface data
        """
        surface_data = {}
        
        # Parse Surface attributes
        config = SURFACE_CONFIG
        attributes = self.reader._parse_attributes(surface_elem, config['attr_map'])
        surface_data.update(attributes)
        
        # Find Definition element (contains Pnts and Faces elements)
        definition_elem = self.reader._find_element(surface_elem, 'Definition')
        
        if definition_elem is not None:
            # Parse surface type
            surf_type = definition_elem.attrib.get('surfType', 'TIN')
            surface_data['surfType'] = surf_type
            
            # Parse points (P elements within Pnts)
            points = self.parse_surface_points(definition_elem)
            if points:
                surface_data['points'] = points
            
            # Parse faces (F elements within Faces) - for TIN surfaces
            faces = self.parse_surface_faces(definition_elem)
            if faces:
                surface_data['faces'] = faces
        
        return surface_data
    
    def read_all_surfaces(self) -> List[Dict]:
        """
        Read all Surfaces from LandXML file.
        
        Returns:
            List of Surface data dictionaries
        """
        surfaces = []
        
        # Find Surfaces container
        surfaces_elem = self.reader._find_element(self.reader.root, 'Surfaces')
        
        if surfaces_elem is None:
            print("Warning: No Surfaces element found in LandXML file")
            return surfaces
        
        # Find all Surface elements
        surface_elements = self.reader._find_all_elements(surfaces_elem, 'Surface')
        
        if not surface_elements:
            print("Warning: No Surface elements found in LandXML file")
            return surfaces
        
        # Parse each Surface
        for surface_elem in surface_elements:
            try:
                surface_data = self.parse_surface(surface_elem)
                # Only add if surface has at least name
                if 'name' in surface_data:
                    surfaces.append(surface_data)
            except Exception as e:
                print(f"Warning: Failed to parse Surface: {str(e)}")
                continue
        
        return surfaces
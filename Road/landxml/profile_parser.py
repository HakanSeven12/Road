# SPDX-License-Identifier: LGPL-2.1-or-later

"""
LandXML Profile Parser
Handles parsing of Profile, ProfAlign, and ProfSurf elements from LandXML files.
"""

from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
from .landxml_config import (
    PROFILE_CONFIG,
    PROFALIGN_CONFIG,
    PROFSURF_CONFIG,
    PROFILE_GEOMETRY_CONFIG
)


class ProfileParser:
    """
    Parser for LandXML Profile elements.
    Handles ProfAlign (vertical alignment geometry) and ProfSurf (surface profiles).
    """
    
    def __init__(self, reader):
        """
        Initialize profile parser with reference to main reader.
        
        Args:
            reader: LandXMLReader instance for accessing helper methods
        """
        self.reader = reader
    
    def parse_pvi(self, pvi_elem: ET.Element) -> Dict:
        """
        Parse PVI (Profile Vertical Intersection) element.
        
        Args:
            pvi_elem: PVI XML element
            
        Returns:
            Dictionary with parsed PVI data
        """
        pvi_data = {}
        
        # Parse PVI coordinates from text
        pvi_text = pvi_elem.text
        if pvi_text:
            coords = pvi_text.strip().replace(',', ' ').split()
            if len(coords) >= 2:
                pvi_data['station'] = float(coords[0])
                pvi_data['elevation'] = float(coords[1])
        
        # Parse attributes
        if 'desc' in pvi_elem.attrib:
            pvi_data['desc'] = pvi_elem.attrib['desc']
        
        return pvi_data
    
    def parse_pntlist2d(self, pntlist_elem: ET.Element) -> List[tuple]:
        """
        Parse PntList2D element containing profile points.
        
        Args:
            pntlist_elem: PntList2D XML element
            
        Returns:
            List of (station, elevation) tuples
        """
        points = []
        content = pntlist_elem.text
        if content:
            coords = content.strip().replace(',', ' ').split()
            # First value is station, second is elevation
            for i in range(0, len(coords) - 1, 2):
                points.append((float(coords[i]), float(coords[i+1])))
                    
        return points
    
    def parse_profile_geometry_element(self, geom_elem: ET.Element, geom_type: str) -> Optional[Dict]:
        """
        Parse profile geometry elements (PVI, CircCurve, ParaCurve, UnsymParaCurve, PntList2D).
        Uses Civil3D format where curve elements contain PVI coordinates in text content.
        
        Args:
            geom_elem: XML element to parse
            geom_type: Type of geometry
        
        Returns:
            Dictionary with parsed geometry data or None
        """
        if geom_type not in PROFILE_GEOMETRY_CONFIG:
            return None
        
        config = PROFILE_GEOMETRY_CONFIG[geom_type]
        geom_data = {'Type': geom_type}
        
        # Parse attributes
        attributes = self.reader._parse_attributes(geom_elem, config['attr_map'])
        geom_data.update(attributes)
        
        # Special handling for different geometry types
        if geom_type == 'PVI':
            # PVI coordinates are in element text
            pvi_text = geom_elem.text
            if pvi_text:
                coords = pvi_text.strip().replace(',', ' ').split()
                if len(coords) >= 2:
                    geom_data['station'] = float(coords[0])
                    geom_data['elevation'] = float(coords[1])
        
        elif geom_type in ['CircCurve', 'ParaCurve', 'UnsymParaCurve']:
            # Civil3D format: PVI coordinates in element text content
            elem_text = geom_elem.text
            if elem_text and elem_text.strip():
                coords = elem_text.strip().replace(',', ' ').split()
                if len(coords) >= 2:
                    geom_data['pvi'] = {
                        'station': float(coords[0]),
                        'elevation': float(coords[1])
                    }
        
        return geom_data
    
    def parse_profalign(self, profalign_elem: ET.Element) -> Dict:
        """
        Parse ProfAlign element (vertical alignment geometry).
        
        Args:
            profalign_elem: ProfAlign XML element
            
        Returns:
            Dictionary with parsed ProfAlign data
        """
        profalign_data = {}
        
        # Parse attributes
        attributes = self.reader._parse_attributes(profalign_elem, PROFALIGN_CONFIG['attr_map'])
        profalign_data.update(attributes)
        
        # Parse geometry elements (PVI, CircCurve, ParaCurve, UnsymParaCurve, PntList2D)
        # These elements define the vertical alignment in order
        geom_list = []
        for child in profalign_elem:
            tag = child.tag
            if '}' in tag:
                tag = tag.split('}')[1]
            
            if tag in PROFILE_GEOMETRY_CONFIG:
                try:
                    geom_data = self.parse_profile_geometry_element(child, tag)
                    if geom_data:
                        geom_list.append(geom_data)
                except Exception as e:
                    print(f"Warning: Failed to parse {tag} element: {str(e)}")
                    continue
        
        if geom_list:
            profalign_data['geometry'] = geom_list
        
        return profalign_data
    
    def parse_profsurf(self, profsurf_elem: ET.Element) -> Dict:
        """
        Parse ProfSurf element (surface profile).
        
        Args:
            profsurf_elem: ProfSurf XML element
            
        Returns:
            Dictionary with parsed ProfSurf data
        """
        profsurf_data = {}
        
        # Parse attributes
        attributes = self.reader._parse_attributes(profsurf_elem, PROFSURF_CONFIG['attr_map'])
        profsurf_data.update(attributes)
        
        # Parse PntList2D (list of station-elevation points)
        pntlist_elem = self.reader._find_element(profsurf_elem, 'PntList2D')
        if pntlist_elem is not None:
            points = self.parse_pntlist2d(pntlist_elem)
            if points:
                profsurf_data['points'] = points
        
        return profsurf_data
    
    def parse_profile(self, profile_elem: ET.Element, alignment_name: Optional[str] = None) -> Dict:
        """
        Parse Profile element.
        
        Args:
            profile_elem: Profile XML element
            alignment_name: Name of parent alignment (optional)
            
        Returns:
            Dictionary with parsed Profile data
        """
        profile_data = {}
        
        # Parse profile attributes
        attributes = self.reader._parse_attributes(profile_elem, PROFILE_CONFIG['attr_map'])
        profile_data.update(attributes)
        
        # Add reference to parent alignment if provided
        if alignment_name:
            profile_data['alignmentName'] = alignment_name
        
        # Parse all ProfAlign elements (can be multiple)
        profalign_list = []
        profalign_elements = self.reader._find_all_elements(profile_elem, 'ProfAlign')
        
        for profalign_elem in profalign_elements:
            try:
                profalign_data = self.parse_profalign(profalign_elem)
                if profalign_data:
                    profalign_list.append(profalign_data)
            except Exception as e:
                print(f"Warning: Failed to parse ProfAlign: {str(e)}")
                continue
        
        if profalign_list:
            # Store as list if multiple, single dict if only one
            if len(profalign_list) == 1:
                profile_data['ProfAlign'] = profalign_list[0]
            else:
                profile_data['ProfAlign'] = profalign_list
        
        # Parse all ProfSurf elements (surface profiles)
        profsurf_list = []
        profsurf_elements = self.reader._find_all_elements(profile_elem, 'ProfSurf')
        
        for profsurf_elem in profsurf_elements:
            try:
                profsurf_data = self.parse_profsurf(profsurf_elem)
                if profsurf_data:
                    profsurf_list.append(profsurf_data)
            except Exception as e:
                print(f"Warning: Failed to parse ProfSurf: {str(e)}")
                continue
        
        if profsurf_list:
            profile_data['ProfSurf'] = profsurf_list
        
        return profile_data
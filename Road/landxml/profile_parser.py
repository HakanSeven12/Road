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
    
    def parse_pntlist2d(self, pntlist_elem: ET.Element) -> List[tuple]:
        """
        Parse PntList2D element containing profile points.
        
        Args:
            pntlist_elem: PntList2D XML element
            
        Returns:
            List of (station, elevation) tuples
        """
        points = []
        
        # Find all P elements
        p_elements = self.reader._find_all_elements(pntlist_elem, 'P')
        
        for p_elem in p_elements:
            p_text = p_elem.text
            if p_text:
                coords = p_text.strip().replace(',', ' ').split()
                if len(coords) >= 2:
                    # First value is station, second is elevation
                    station = float(coords[0])
                    elevation = float(coords[1])
                    points.append((station, elevation))
        
        return points
    
    def parse_profile_geometry_element(self, geom_elem: ET.Element, geom_type: str) -> Optional[Dict]:
        """
        Parse profile geometry elements (CircCurve, ParaCurve, PntList2D).
        
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
        
        # Special handling for PntList2D
        if geom_type == 'PntList2D':
            points = self.parse_pntlist2d(geom_elem)
            if points:
                geom_data['points'] = points
        
        # Parse Start/End points for curves
        if geom_type in ['CircCurve', 'ParaCurve']:
            start_elem = self.reader._find_element(geom_elem, 'Start')
            if start_elem is not None and start_elem.text:
                coords = start_elem.text.strip().replace(',', ' ').split()
                if len(coords) >= 2:
                    geom_data['start'] = {
                        'station': float(coords[0]),
                        'elevation': float(coords[1])
                    }
            
            end_elem = self.reader._find_element(geom_elem, 'End')
            if end_elem is not None and end_elem.text:
                coords = end_elem.text.strip().replace(',', ' ').split()
                if len(coords) >= 2:
                    geom_data['end'] = {
                        'station': float(coords[0]),
                        'elevation': float(coords[1])
                    }
            
            # Parse PI (Point of Intersection) for curves
            pi_elem = self.reader._find_element(geom_elem, 'PI')
            if pi_elem is not None and pi_elem.text:
                coords = pi_elem.text.strip().replace(',', ' ').split()
                if len(coords) >= 2:
                    geom_data['pi'] = {
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
        
        # Parse PVI points (Profile Vertical Intersection points)
        pvi_list = []
        pvi_elements = self.reader._find_all_elements(profalign_elem, 'PVI')
        
        for pvi_elem in pvi_elements:
            pvi_text = pvi_elem.text
            if pvi_text:
                coords = pvi_text.strip().replace(',', ' ').split()
                if len(coords) >= 2:
                    pvi_data = {
                        'station': float(coords[0]),
                        'elevation': float(coords[1])
                    }
                    
                    # Add optional attributes
                    if 'desc' in pvi_elem.attrib:
                        pvi_data['desc'] = pvi_elem.attrib['desc']
                    
                    pvi_list.append(pvi_data)
        
        if pvi_list:
            profalign_data['PVI'] = pvi_list
        
        # Parse geometry elements (CircCurve, ParaCurve, PntList2D)
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
        
        # Parse ProfAlign (vertical alignment)
        profalign_elem = self.reader._find_element(profile_elem, 'ProfAlign')
        if profalign_elem is not None:
            profalign_data = self.parse_profalign(profalign_elem)
            if profalign_data:
                profile_data['ProfAlign'] = profalign_data
        
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
    
    def read_all_profiles(self) -> List[Dict]:
        """
        Read all Profiles from LandXML file.
        Profiles are typically contained within Alignment elements.
        
        Returns:
            List of Profile data dictionaries
        """
        profiles = []
        
        # Profiles are typically under Alignments
        alignments_elem = self.reader._find_element(self.reader.root, 'Alignments')
        
        if alignments_elem is None:
            print("Warning: No Alignments element found in LandXML file")
            return profiles
        
        # Find all Alignment elements
        alignment_elements = self.reader._find_all_elements(alignments_elem, 'Alignment')
        
        for align_elem in alignment_elements:
            # Get alignment name for reference
            align_name = align_elem.attrib.get('name')
            
            # Find Profile element within each Alignment
            profile_elem = self.reader._find_element(align_elem, 'Profile')
            
            if profile_elem is not None:
                try:
                    profile_data = self.parse_profile(profile_elem, align_name)
                    profiles.append(profile_data)
                except Exception as e:
                    print(f"Warning: Failed to parse Profile for alignment '{align_name}': {str(e)}")
                    continue
        
        return profiles
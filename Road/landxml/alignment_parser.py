# SPDX-License-Identifier: LGPL-2.1-or-later

"""
LandXML Alignment Parser
Handles parsing of Alignment and CoordGeom elements from LandXML files.
"""

from typing import Dict, List
import xml.etree.ElementTree as ET
from .profile_parser import ProfileParser
from .landxml_config import (
    GEOMETRY_CONFIG,
    ALIGNMENT_CONFIG,
    ALIGN_PI_CONFIG,
    STATION_EQUATION_CONFIG
)


class AlignmentParser:
    """
    Parser for LandXML Alignment elements.
    Handles horizontal alignment geometry (Line, Curve, Spiral), PIs, and station equations.
    """
    
    def __init__(self, reader):
        """
        Initialize alignment parser with reference to main reader.
        
        Args:
            reader: LandXMLReader instance for accessing helper methods
        """
        self.reader = reader
        self.profile_parser = ProfileParser(reader)
    
    def parse_child_points(self, element: ET.Element, point_tags: List[str]) -> Dict:
        """
        Parse child elements that contain point coordinates.
        
        Args:
            element: Parent XML element
            point_tags: List of child tag names to parse as points
        
        Returns:
            Dictionary with parsed points
        """
        result = {}
        
        for tag in point_tags:
            child_elem = self.reader._find_element(element, tag)
            if child_elem is not None and child_elem.text:
                result[tag] = self.reader._parse_point(child_elem.text.strip())
        
        return result
    
    def parse_geometry_element(self, geom_elem: ET.Element, geom_type: str) -> Dict:
        """
        Generic geometry element parser for Line, Curve, and Spiral.
        
        Args:
            geom_elem: XML element to parse
            geom_type: Type of geometry ('Line', 'Curve', 'Spiral')
        
        Returns:
            Dictionary with parsed geometry data
        """
        if geom_type not in GEOMETRY_CONFIG:
            raise ValueError(f"Unknown geometry type: {geom_type}")
        
        config = GEOMETRY_CONFIG[geom_type]
        geom_data = {'Type': geom_type}
        
        # Parse point children
        points = self.parse_child_points(geom_elem, config['point_tags'])
        geom_data.update(points)
        
        # Parse attributes
        attributes = self.reader._parse_attributes(geom_elem, config['attr_map'])
        geom_data.update(attributes)
        
        return geom_data
    
    def parse_coord_geom(self, alignment_elem: ET.Element) -> List[Dict]:
        """
        Parse CoordGeom elements (Lines, Curves, Spirals).
        
        Args:
            alignment_elem: Alignment XML element
            
        Returns:
            List of geometry element dictionaries
        """
        geom_list = []
        
        coord_geom = self.reader._find_element(alignment_elem, 'CoordGeom')
        if coord_geom is None:
            return geom_list
        
        # Parse all geometry elements in order
        for child in coord_geom:
            # Remove namespace prefix if present
            tag = child.tag
            if '}' in tag:
                tag = tag.split('}')[1]
            
            # Check if this is a known geometry type
            if tag in GEOMETRY_CONFIG:
                try:
                    geom_data = self.parse_geometry_element(child, tag)
                    geom_list.append(geom_data)
                except Exception as e:
                    print(f"Warning: Failed to parse {tag} element: {str(e)}")
                    continue
            else:
                print(f"Warning: Unknown geometry type '{tag}' skipped")
        
        return geom_list
    
    def parse_align_pis(self, alignment_elem: ET.Element) -> List[Dict]:
        """
        Parse alignment PI points.
        
        Args:
            alignment_elem: Alignment XML element
            
        Returns:
            List of PI dictionaries
        """
        pi_list = []
        
        pis_elem = self.reader._find_element(alignment_elem, 'AlignPIs')
        if pis_elem is None:
            return pi_list
        
        pi_elements = self.reader._find_all_elements(pis_elem, 'AlignPI')
        
        # PI attribute mapping
        config = ALIGN_PI_CONFIG
        
        for pi_elem in pi_elements:
            pi_data = {}
            
            # Get PI coordinates from element text
            pi_text = pi_elem.text
            if pi_text:
                pi_data['point'] = self.reader._parse_point(pi_text.strip())
            
            # Parse attributes
            attributes = self.reader._parse_attributes(pi_elem, config['attr_map'])
            pi_data.update(attributes)
            
            if 'point' in pi_data:
                pi_list.append(pi_data)
        
        return pi_list
    
    def parse_station_equations(self, alignment_elem: ET.Element) -> List[Dict]:
        """
        Parse station equations.
        
        Args:
            alignment_elem: Alignment XML element
            
        Returns:
            List of station equation dictionaries
        """
        eq_list = []
        
        sta_equations = self.reader._find_all_elements(alignment_elem, 'StaEquation')
        
        # Station equation attribute mapping
        config = STATION_EQUATION_CONFIG
        
        for eq_elem in sta_equations:
            # Parse attributes
            eq_data = self.reader._parse_attributes(eq_elem, config['attr_map'])
            
            # Only add if required fields are present
            if 'staAhead' in eq_data and 'staBack' in eq_data:
                eq_list.append(eq_data)
        
        return eq_list
    
    def parse_alignment(self, alignment_elem: ET.Element) -> Dict:
        """
        Parse single alignment element.
        
        Args:
            alignment_elem: Alignment XML element
            
        Returns:
            Dictionary with parsed alignment data
        """
        alignment_data = {}
        
        # Alignment attribute mapping
        config = ALIGNMENT_CONFIG
        
        # Parse alignment attributes
        attributes = self.reader._parse_attributes(alignment_elem, config['attr_map'])
        alignment_data.update(attributes)
        
        # Get alignment name for profile reference
        align_name = alignment_data.get('name')
        
        # Get start point (optional)
        start_elem = self.reader._find_element(alignment_elem, 'Start')
        if start_elem is not None and start_elem.text:
            alignment_data['start'] = self.reader._parse_point(start_elem.text.strip())
        
        # Parse alignment PIs
        align_pis = self.parse_align_pis(alignment_elem)
        if align_pis:
            alignment_data['AlignPIs'] = align_pis
        
        # Parse station equations
        sta_equations = self.parse_station_equations(alignment_elem)
        if sta_equations:
            alignment_data['StaEquation'] = sta_equations
        
        # Parse coordinate geometry
        coord_geom = self.parse_coord_geom(alignment_elem)
        if coord_geom:
            alignment_data['CoordGeom'] = coord_geom
        
        # Parse Profile (vertical alignment)
        profile_elem = self.reader._find_element(alignment_elem, 'Profile')
        if profile_elem is not None:
            profile_data = self.profile_parser.parse_profile(profile_elem, align_name)
            if profile_data:
                alignment_data['Profile'] = profile_data
        
        return alignment_data
    
    def read_all_alignments(self) -> List[Dict]:
        """
        Read all alignments from LandXML file.
        
        Returns:
            List of alignment data dictionaries
        """
        alignments = []
        
        # Find Alignments container
        alignments_elem = self.reader._find_element(self.reader.root, 'Alignments')
        
        if alignments_elem is None:
            print("Warning: No Alignments elements found in LandXML file")
            return alignments
        
        # Find all Alignment elements
        alignment_elements = self.reader._find_all_elements(alignments_elem, 'Alignment')
        
        if not alignment_elements:
            print("Warning: No Alignment elements found in LandXML file")
            return alignments
        
        # Parse each alignment
        for align_elem in alignment_elements:
            try:
                alignment_data = self.parse_alignment(align_elem)
                alignments.append(alignment_data)
            except Exception as e:
                print(f"Warning: Failed to parse alignment: {str(e)}")
                continue
        
        return alignments
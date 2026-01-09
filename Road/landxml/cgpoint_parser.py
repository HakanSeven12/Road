# SPDX-License-Identifier: LGPL-2.1-or-later

"""
LandXML CgPoint Parser
Handles parsing of CgPoint elements from LandXML files.
"""

from typing import Dict, List
import xml.etree.ElementTree as ET
from .landxml_config import CGPOINT_CONFIG


class CgPointParser:
    """
    Parser for LandXML CgPoint elements.
    Handles coordinate geometry points organized in groups.
    """
    
    def __init__(self, reader):
        """
        Initialize CgPoint parser with reference to main reader.
        
        Args:
            reader: LandXMLReader instance for accessing helper methods
        """
        self.reader = reader
    
    def parse_cgpoint(self, cgpoint_elem: ET.Element) -> Dict:
        """
        Parse single CgPoint element.
        
        Args:
            cgpoint_elem: XML element representing a CgPoint
            
        Returns:
            Dictionary with parsed CgPoint data
        """
        cgpoint_data = {}
        
        # Parse CgPoint attributes
        config = CGPOINT_CONFIG
        attributes = self.reader._parse_attributes(cgpoint_elem, config['attr_map'])
        cgpoint_data.update(attributes)
        
        # Move 'code' to 'desc' if present (code is actually the description)
        if 'code' in cgpoint_data and 'desc' not in cgpoint_data:
            cgpoint_data['desc'] = cgpoint_data['code']
            del cgpoint_data['code']
        
        # Get point coordinates from element text
        point_text = cgpoint_elem.text
        if point_text:
            coords = self.reader._parse_point(point_text.strip())
            if coords:
                if len(coords) == 3:
                    cgpoint_data['easting'] = coords[1]
                    cgpoint_data['northing'] = coords[0]
                    cgpoint_data['elevation'] = coords[2]
                else:
                    cgpoint_data['easting'] = coords[1]
                    cgpoint_data['northing'] = coords[0]
        
        return cgpoint_data
    
    def read_all_cgpoints(self) -> List[Dict]:
        """
        Read all CgPoints from LandXML file, organized by groups.
        Groups can be defined by <CgPoints name="..."> containers with pntRef references.
        
        Returns:
            List of group dictionaries, each containing group name and list of points
        """
        groups = []
        
        # Find CgPoints container
        cgpoints_elements = self.reader._find_all_elements(self.reader.root, 'CgPoints')
        
        if not cgpoints_elements:
            print("Warning: No CgPoints element found in LandXML file")
            return groups
        
        # First, parse all individual CgPoint elements to create a lookup dictionary
        # Only parse direct children that are actual points (not nested groups)
        all_points = {}
        
        for cgpoints_elem in cgpoints_elements:
            for child in cgpoints_elem:
                tag = child.tag
                if '}' in tag:
                    tag = tag.split('}')[1]
                
                # Only parse CgPoint elements that are NOT CgPoints groups
                if tag == 'CgPoint' and 'name' in child.attrib:
                    try:
                        cgpoint_data = self.parse_cgpoint(child)
                        if 'name' in cgpoint_data:
                            all_points[cgpoint_data['name']] = cgpoint_data
                    except Exception as e:
                        print(f"Warning: Failed to parse CgPoint: {str(e)}")
                        continue
            
        # Track which points are referenced by groups
        referenced_points = set()
        
        # Find all CgPoints group (nested <CgPoints name="...">)
        for cgpoints_elem in cgpoints_elements:
            tag = cgpoints_elem.tag
            if '}' in tag:
                tag = tag.split('}')[1]
            
            # Check if this is a CgPoints group container (has 'name' attribute)
            if tag == 'CgPoints' and 'name' in cgpoints_elem.attrib:
                group_name = cgpoints_elem.attrib['name']
                group_points = []
                
                # Find all point references in this group
                point_refs = self.reader._find_all_elements(cgpoints_elem, 'CgPoint')
                
                for point_ref in point_refs:
                    pnt_ref = point_ref.attrib.get('pntRef')
                    if pnt_ref and pnt_ref in all_points:
                        group_points.append(all_points[pnt_ref])
                        referenced_points.add(pnt_ref)
                
                if group_points:
                    groups.append({
                        'name': group_name,
                        'points': group_points
                    })
            
        # Create a group for unreferenced points
        unreferenced_points = []
        for point_name, point_data in all_points.items():
            if point_name not in referenced_points:
                unreferenced_points.append(point_data)
        
        if unreferenced_points:
            groups.append({
                'name': 'Ungrouped Points',
                'points': unreferenced_points
            })
        
        return groups
# SPDX-License-Identifier: LGPL-2.1-or-later

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Union
from pathlib import Path
from ..geometry.alignment import Alignment
from .landxml_config import (
    GEOMETRY_CONFIG,
    ALIGNMENT_CONFIG,
    ALIGN_PI_CONFIG,
    STATION_EQUATION_CONFIG,
    LANDXML_NAMESPACES
)


class LandXMLReader:
    """
    LandXML 1.2 file reader for horizontal alignments.
    Parses LandXML files and extracts alignment data with geometry elements.
    """

    # LandXML namespace (if present in file)
    NAMESPACES = LANDXML_NAMESPACES

    def __init__(self, filepath: Union[str, Path]):
        """
        Initialize reader with LandXML file path.
        
        Args:
            filepath: Path to LandXML file
        """
        self.filepath = Path(filepath)
        
        if not self.filepath.exists():
            raise FileNotFoundError(f"LandXML file not found: {filepath}")
        
        self.tree = None
        self.root = None
        self.alignments_data = []
        
        # Parse the XML file
        self._parse_xml()
    
    def _parse_xml(self):
        """Parse XML file and get root element"""
        try:
            self.tree = ET.parse(self.filepath)
            self.root = self.tree.getroot()
            
            # Check if namespace is present
            if self.root.tag.startswith('{'):
                # Extract namespace from root tag
                namespace = self.root.tag.split('}')[0] + '}'
                self.namespace = namespace
            else:
                self.namespace = ''
                
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse LandXML file: {str(e)}")
    
    def _find_element(self, parent: ET.Element, tag: str) -> Optional[ET.Element]:
        """
        Find element with or without namespace.
        
        Args:
            parent: Parent XML element
            tag: Tag name to search
            
        Returns:
            Found element or None
        """
        # Try with namespace
        elem = parent.find(f"{self.namespace}{tag}")
        
        # Try without namespace if not found
        if elem is None:
            elem = parent.find(tag)
        
        return elem
    
    def _find_all_elements(self, parent: ET.Element, tag: str) -> List[ET.Element]:
        """
        Find all elements with given tag (with or without namespace).
        
        Args:
            parent: Parent XML element
            tag: Tag name to search
            
        Returns:
            List of found elements
        """
        # Try with namespace
        elems = parent.findall(f"{self.namespace}{tag}")
        
        # Try without namespace if not found
        if not elems:
            elems = parent.findall(tag)
        
        return elems
    
    def _parse_point(self, point_text: str) -> tuple:
        """
        Parse point coordinates from text (space or comma separated).
        
        Args:
            point_text: Point coordinates as string "x y [z]" or "x,y[,z]"
            
        Returns:
            (x, y) tuple, ignoring z if present
        """
        if not point_text:
            return None
        
        # Handle both space and comma separation
        coords = point_text.replace(',', ' ').split()
        
        if len(coords) < 2:
            raise ValueError(f"Invalid point format: {point_text}")
        
        return (float(coords[1]), float(coords[0]))
    
    def _parse_align_pis(self, alignment_elem: ET.Element) -> List[Dict]:
        """Parse alignment PI points"""
        pi_list = []
        
        pis_elem = self._find_element(alignment_elem, 'AlignPIs')
        if pis_elem is None:
            return pi_list
        
        pi_elements = self._find_all_elements(pis_elem, 'AlignPI')
        
        # PI attribute mapping
        config = ALIGN_PI_CONFIG
        
        for pi_elem in pi_elements:
            pi_data = {}
            
            # Get PI coordinates from element text
            pi_text = pi_elem.text
            if pi_text:
                pi_data['point'] = self._parse_point(pi_text.strip())
            
            # Parse attributes
            attributes = self._parse_attributes(pi_elem, config['attr_map'])
            pi_data.update(attributes)
            
            if 'point' in pi_data:
                pi_list.append(pi_data)
        
        return pi_list
    
    def _parse_station_equations(self, alignment_elem: ET.Element) -> List[Dict]:
        """Parse station equations"""
        eq_list = []
        
        sta_equations = self._find_all_elements(alignment_elem, 'StaEquation')
        
        # Station equation attribute mapping
        config = STATION_EQUATION_CONFIG
        
        for eq_elem in sta_equations:
            # Parse attributes
            eq_data = self._parse_attributes(eq_elem, config['attr_map'])
            
            # Only add if required fields are present
            if 'staAhead' in eq_data and 'staBack' in eq_data:
                eq_list.append(eq_data)
        
        return eq_list
    
    def _parse_attributes(self, element: ET.Element, attr_map: Dict) -> Dict:
        """
        Parse element attributes based on mapping.
        
        Args:
            element: XML element
            attr_map: Dict mapping {xml_attr_name: (output_key, converter_func)}
                     converter_func can be: float, int, str, or custom function
        
        Returns:
            Dictionary with parsed attributes
        """
        result = {}
        
        for xml_attr, (output_key, converter) in attr_map.items():
            if xml_attr in element.attrib:
                value = element.attrib[xml_attr]
                
                try:
                    if converter == 'float':
                        result[output_key] = float(value)
                    elif converter == 'int':
                        result[output_key] = int(value)
                    elif converter == 'radius':
                        # Handle INF radius
                        result[output_key] = float('inf') if value == 'INF' else float(value)
                    else:
                        result[output_key] = value
                except (ValueError, AttributeError):
                    continue
        
        return result
    
    def _parse_child_points(self, element: ET.Element, point_tags: List[str]) -> Dict:
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
            child_elem = self._find_element(element, tag)
            if child_elem is not None and child_elem.text:
                result[tag] = self._parse_point(child_elem.text.strip())
        
        return result
    
    def _parse_geometry_element(self, geom_elem: ET.Element, geom_type: str) -> Dict:
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
        points = self._parse_child_points(geom_elem, config['point_tags'])
        geom_data.update(points)
        
        # Parse attributes
        attributes = self._parse_attributes(geom_elem, config['attr_map'])
        geom_data.update(attributes)
        
        return geom_data
    
    def _parse_coord_geom(self, alignment_elem: ET.Element) -> List[Dict]:
        """Parse CoordGeom elements (Lines, Curves, Spirals)"""
        geom_list = []
        
        coord_geom = self._find_element(alignment_elem, 'CoordGeom')
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
                    geom_data = self._parse_geometry_element(child, tag)
                    geom_list.append(geom_data)
                except Exception as e:
                    print(f"Warning: Failed to parse {tag} element: {str(e)}")
                    continue
            else:
                print(f"Warning: Unknown geometry type '{tag}' skipped")
        
        return geom_list
    
    def _parse_alignment(self, alignment_elem: ET.Element) -> Dict:
        """Parse single alignment element"""
        alignment_data = {}
        
        # Alignment attribute mapping
        config = ALIGNMENT_CONFIG
        
        # Parse alignment attributes
        attributes = self._parse_attributes(alignment_elem, config['attr_map'])
        alignment_data.update(attributes)
        
        # Get start point (optional)
        start_elem = self._find_element(alignment_elem, 'Start')
        if start_elem is not None and start_elem.text:
            alignment_data['start'] = self._parse_point(start_elem.text.strip())
        
        # Parse alignment PIs
        align_pis = self._parse_align_pis(alignment_elem)
        if align_pis:
            alignment_data['AlignPIs'] = align_pis
        
        # Parse station equations
        sta_equations = self._parse_station_equations(alignment_elem)
        if sta_equations:
            alignment_data['StaEquation'] = sta_equations
        
        # Parse coordinate geometry
        coord_geom = self._parse_coord_geom(alignment_elem)
        if coord_geom:
            alignment_data['CoordGeom'] = coord_geom
        
        return alignment_data
    
    def read_alignments(self) -> List[Dict]:
        """
        Read all alignments from LandXML file.
        
        Returns:
            List of alignment data dictionaries
        """
        alignments = []
        
        # Find Alignments container
        alignments_elem = self._find_element(self.root, 'Alignments')
        
        if alignments_elem is None:
            raise ValueError("No Alignments element found in LandXML file")
        
        # Find all Alignment elements
        alignment_elements = self._find_all_elements(alignments_elem, 'Alignment')
        
        if not alignment_elements:
            raise ValueError("No Alignment elements found in LandXML file")
        
        # Parse each alignment
        for align_elem in alignment_elements:
            try:
                alignment_data = self._parse_alignment(align_elem)
                alignments.append(alignment_data)
            except Exception as e:
                print(f"Warning: Failed to parse alignment: {str(e)}")
                continue
        
        self.alignments_data = alignments
        return alignments
    
    def get_alignment_by_name(self, name: str) -> Optional[Dict]:
        """
        Get alignment data by name.
        
        Args:
            name: Alignment name to search
            
        Returns:
            Alignment data dictionary or None if not found
        """
        if not self.alignments_data:
            self.read_alignments()
        
        for alignment in self.alignments_data:
            if alignment.get('name') == name:
                return alignment
        
        return None
    
    def get_alignment_names(self) -> List[str]:
        """
        Get list of all alignment names in the file.
        
        Returns:
            List of alignment names
        """
        if not self.alignments_data:
            self.read_alignments()
        
        return [align.get('name', 'Unnamed') for align in self.alignments_data]
    
    def get_alignment_count(self) -> int:
        """
        Get number of alignments in the file.
        
        Returns:
            Count of alignments
        """
        if not self.alignments_data:
            self.read_alignments()
        
        return len(self.alignments_data)
    
    def export_to_dict(self) -> Dict:
        """
        Export all parsed data to dictionary.
        
        Returns:
            Dictionary containing file info and all alignments
        """
        if not self.alignments_data:
            self.read_alignments()
        
        return {
            'filepath': str(self.filepath),
            'alignment_count': len(self.alignments_data),
            'alignments': self.alignments_data
        }


# Example usage function
def read_landxml_file(filepath: str):
    """
    Example function showing how to use LandXMLReader.
    
    Args:
        filepath: Path to LandXML file
    
    Returns:
        List of alignment data dictionaries
    """
    # Create reader instance
    reader = LandXMLReader(filepath)
    
    # Read all alignments
    alignments = reader.read_alignments()
    
    print(f"Found {len(alignments)} alignment(s) in file")
    
    # Print alignment names
    for i, alignment in enumerate(alignments):
        name = alignment.get('name', 'Unnamed')
        length = alignment.get('length', 'Unknown')
        geom_count = len(alignment.get('CoordGeom', []))
        
        print(f"\nAlignment {i+1}: {name}")
        print(f"  Length: {length}")
        print(f"  Geometry elements: {geom_count}")
        
        # Print geometry types
        if 'CoordGeom' in alignment:
            geom_types = [geom['Type'] for geom in alignment['CoordGeom']]
            print(f"  Types: {', '.join(geom_types)}")
    
    return alignments


# Example: Create Alignment objects from parsed data
def create_alignment_objects(filepath: str):
    """
    Example showing how to read LandXML and create Alignment objects.
    
    Args:
        filepath: Path to LandXML file
    
    Returns:
        List of Alignment objects
    """
    
    # Read LandXML file
    reader = LandXMLReader(filepath)
    alignments_data = reader.read_alignments()
    
    # Create Alignment objects
    alignment_objects = []
    
    for align_data in alignments_data:
        try:
            alignment = Alignment(align_data)
            alignment_objects.append(alignment)
            print(f"Created alignment: {alignment}")
        except Exception as e:
            print(f"Error creating alignment: {str(e)}")
            continue
    
    return alignment_objects
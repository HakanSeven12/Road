# SPDX-License-Identifier: LGPL-2.1-or-later

import math
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Union
from pathlib import Path
from .alignment_parser import AlignmentParser
from .cgpoint_parser import CgPointParser
from .surface_parser import SurfaceParser
from .landxml_config import (
    LANDXML_NAMESPACES,
    UNITS_CONFIG,
    ANGULAR_UNITS
)


class LandXMLReader:
    """
    LandXML 1.2 file reader.
    Parses LandXML files and extracts data.
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
        self.alignment_parser = AlignmentParser(self)

        self.cgpoints_data = []
        self.cgpoint_parser = CgPointParser(self)

        self.surfaces_data = []
        self.surface_parser = SurfaceParser(self)
        
        self.angular_unit = 'decimal degrees'  # Default
        self.direction_unit = 'decimal degrees'  # Default
        self.angular_conversion_factor = ANGULAR_UNITS['decimal degrees']
        self.direction_conversion_factor = ANGULAR_UNITS['decimal degrees']
    
        # Parse the XML file and parse units
        self._parse_xml()
        self._parse_units()
    
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
    
    def _parse_attributes(self, element: ET.Element, attr_map: Dict) -> Dict:
        """
        Parse element attributes based on mapping.
        
        Args:
            element: XML element
            attr_map: Dict mapping {xml_attr_name: (output_key, converter_func)}
                    converter_func can be: float, int, str, 'angle', 'radius', or custom function
        
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
                        result[output_key] = float('inf') if value == 'INF' else float(value)
                    elif converter == 'angle':
                        # Convert angle to radians
                        if 'dir' in xml_attr.lower():
                            # This is a direction/azimuth attribute
                            dir_value = float(value)
                            
                            if self.direction_unit == 'radians':
                                # Already in radians and already math angle (Quadri format)
                                result[output_key] = dir_value
                            else:
                                # In degrees and it's azimuth (Civil3D, standard LandXML)
                                # Convert azimuth to math angle
                                azimuth_deg = dir_value
                                math_angle_deg = 90.0 - azimuth_deg
                                result[output_key] = math.radians(math_angle_deg)
                        else:
                            # Other angles (delta, theta) - just convert based on unit
                            result[output_key] = float(value) * self.angular_conversion_factor
                    else:
                        result[output_key] = value
                except (ValueError, AttributeError):
                    continue
        
        return result
    
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
    
    def _parse_units(self):
        """
        Parse Units element to determine angular unit system.
        Sets conversion factors for angle/direction attributes.
        """
        units_elem = self._find_element(self.root, 'Units')
        
        if units_elem is None:
            print("Warning: No Units element found, using default (decimal degrees)")
            return
        
        # Check for Metric or Imperial units
        metric_elem = self._find_element(units_elem, 'Metric')
        imperial_elem = self._find_element(units_elem, 'Imperial')
        
        units_data = None
        if metric_elem is not None:
            units_data = self._parse_attributes(metric_elem, UNITS_CONFIG['Metric']['attr_map'])
        elif imperial_elem is not None:
            units_data = self._parse_attributes(imperial_elem, UNITS_CONFIG['Imperial']['attr_map'])
        
        if units_data:
            # Get angular unit
            if 'angularUnit' in units_data:
                self.angular_unit = units_data['angularUnit']
                if self.angular_unit in ANGULAR_UNITS:
                    self.angular_conversion_factor = ANGULAR_UNITS[self.angular_unit]
                else:
                    print(f"Warning: Unknown angular unit '{self.angular_unit}', using decimal degrees")
            
            # Get direction unit (for azimuth/bearing)
            if 'directionUnit' in units_data:
                self.direction_unit = units_data['directionUnit']
                if self.direction_unit in ANGULAR_UNITS:
                    self.direction_conversion_factor = ANGULAR_UNITS[self.direction_unit]
                else:
                    print(f"Warning: Unknown direction unit '{self.direction_unit}', using decimal degrees")

    def get_units_info(self) -> Dict:
        """
        Get information about the unit system used in the LandXML file.
        
        Returns:
            Dictionary containing unit information
        """
        return {
            'angular_unit': self.angular_unit,
            'direction_unit': self.direction_unit,
            'angular_conversion_factor': self.angular_conversion_factor,
            'direction_conversion_factor': self.direction_conversion_factor
        }
    
    def _parse_point(self, point_text: str) -> tuple:
        """
        Parse point coordinates from text (space or comma separated).
        
        Args:
            point_text: Point coordinates as string "x y [z]" or "x,y[,z]"
            
        Returns:
            (x, y) or (x, y, z) tuple
        """
        if not point_text:
            return None
        
        # Handle both space and comma separation
        coords = point_text.replace(',', ' ').split()
        
        if len(coords) < 2:
            raise ValueError(f"Invalid point format: {point_text}")
        
        # Return (northing, easting) or (northing, easting, elevation)
        if len(coords) >= 3:
            return (float(coords[0]), float(coords[1]), float(coords[2]))
        else:
            return (float(coords[0]), float(coords[1]))
    
    def read_alignments(self) -> List[Dict]:
        """
        Read all alignments from LandXML file.
        
        Returns:
            List of alignment data dictionaries
        """
        self.alignments_data = self.alignment_parser.read_all_alignments()
        return self.alignments_data
    
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
    
    def get_profile_by_alignment(self, alignment_name: str) -> Optional[Dict]:
        """
        Get profile data for a specific alignment.
        
        Args:
            alignment_name: Name of the alignment
            
        Returns:
            Profile data dictionary or None if not found
        """
        alignment = self.get_alignment_by_name(alignment_name)
        if alignment:
            return alignment.get('Profile')
        return None
    
    def get_all_profiles(self) -> List[Dict]:
        """
        Get all profiles from all alignments.
        
        Returns:
            List of profile data dictionaries
        """
        if not self.alignments_data:
            self.read_alignments()
        
        profiles = []
        for alignment in self.alignments_data:
            if 'Profile' in alignment:
                profile = alignment['Profile'].copy()
                # Add alignment reference if not already present
                if 'alignmentName' not in profile:
                    profile['alignmentName'] = alignment.get('name')
                profiles.append(profile)
        
        return profiles
    
    def get_profile_names(self) -> List[str]:
        """
        Get list of all profile names in the file.
        
        Returns:
            List of profile names
        """
        profiles = self.get_all_profiles()
        return [prof.get('name', 'Unnamed') for prof in profiles]
    
    def get_profile_count(self) -> int:
        """
        Get number of profiles in the file.
        
        Returns:
            Count of profiles
        """
        return len(self.get_all_profiles())

    def read_cgpoints(self) -> List[Dict]:
        """
        Read all CgPoints from LandXML file, organized by groups.
        Groups can be defined by <CgPoints name="..."> containers with pntRef references.
        
        Returns:
            List of group dictionaries, each containing group name and list of points
        """
        self.cgpoints_data = self.cgpoint_parser.read_all_cgpoints()
        return self.cgpoints_data
    
    def get_cgpoint_by_name(self, name: str) -> Optional[Dict]:
        """
        Get CgPoint data by name.
        
        Args:
            name: Point name to search
            
        Returns:
            CgPoint data dictionary or None if not found
        """
        if not self.cgpoints_data:
            self.read_cgpoints()
        
        for group in self.cgpoints_data:
            for cgpoint in group.get('points', []):
                if cgpoint.get('name') == name:
                    return cgpoint
        
        return None

    def get_cgpoints_by_group(self, group_name: str) -> List[Dict]:
        """
        Get all CgPoints in a specified group.
        
        Args:
            group_name: Group name to filter by
            
        Returns:
            List of CgPoint data dictionaries in the group
        """
        if not self.cgpoints_data:
            self.read_cgpoints()
        
        for group in self.cgpoints_data:
            if group.get('name') == group_name:
                return group.get('points', [])
        
        return []

    def get_cgpoint_group_names(self) -> List[str]:
        """
        Get list of all CgPoint group names in the file.
        
        Returns:
            List of group names
        """
        if not self.cgpoints_data:
            self.read_cgpoints()
        
        return [group.get('name', 'Unnamed') for group in self.cgpoints_data]

    def get_cgpoint_names(self) -> List[str]:
        """
        Get list of all CgPoint names in the file.
        
        Returns:
            List of point names
        """
        if not self.cgpoints_data:
            self.read_cgpoints()
        
        names = []
        for group in self.cgpoints_data:
            for pt in group.get('points', []):
                names.append(pt.get('name', 'Unnamed'))
        
        return names

    def get_cgpoint_count(self) -> int:
        """
        Get total number of CgPoints in all groups.
        
        Returns:
            Count of points
        """
        if not self.cgpoints_data:
            self.read_cgpoints()
        
        total = 0
        for group in self.cgpoints_data:
            total += len(group.get('points', []))
        
        return total

    def get_cgpoint_group_count(self) -> int:
        """
        Get number of CgPoint groups in the file.
        
        Returns:
            Count of groups
        """
        if not self.cgpoints_data:
            self.read_cgpoints()
        
        return len(self.cgpoints_data)
    
    def read_surfaces(self) -> List[Dict]:
        """
        Read all Surfaces from LandXML file.
        
        Returns:
            List of Surface data dictionaries
        """
        self.surfaces_data = self.surface_parser.read_all_surfaces()
        return self.surfaces_data
    
    def get_surface_by_name(self, name: str) -> Optional[Dict]:
        """
        Get Surface data by name.
        
        Args:
            name: Surface name to search
            
        Returns:
            Surface data dictionary or None if not found
        """
        if not self.surfaces_data:
            self.read_surfaces()
        
        for surface in self.surfaces_data:
            if surface.get('name') == name:
                return surface
        
        return None
    
    def get_surface_names(self) -> List[str]:
        """
        Get list of all Surface names in the file.
        
        Returns:
            List of surface names
        """
        if not self.surfaces_data:
            self.read_surfaces()
        
        return [surf.get('name', 'Unnamed') for surf in self.surfaces_data]
    
    def get_surface_count(self) -> int:
        """
        Get number of Surfaces in the file.
        
        Returns:
            Count of surfaces
        """
        if not self.surfaces_data:
            self.read_surfaces()
        
        return len(self.surfaces_data)

    def export_to_dict(self) -> Dict:
        """
        Export all parsed data to dictionary.
        
        Returns:
            Dictionary containing file info, alignments (with profiles), CgPoints, and Surfaces
        """
        if not self.alignments_data:
            self.read_alignments()
        
        if not self.cgpoints_data:
            self.read_cgpoints()
        
        if not self.surfaces_data:
            self.read_surfaces()
        
        return {
            'filepath': str(self.filepath),
            'alignment_count': len(self.alignments_data),
            'cgpoint_group_count': len(self.cgpoints_data),
            'cgpoint_count': sum(len(g.get('points', [])) for g in self.cgpoints_data),
            'surface_count': len(self.surfaces_data),
            'profile_count': self.get_profile_count(),
            'alignments': self.alignments_data,
            'cgpoint_groups': self.cgpoints_data,
            'surfaces': self.surfaces_data
        }
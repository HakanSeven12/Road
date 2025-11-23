# SPDX-License-Identifier: LGPL-2.1-or-later

import math
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Union
from pathlib import Path
from .landxml_config import (
    LANDXML_NAMESPACES,
    UNITS_CONFIG,
    ANGULAR_UNITS,
    GEOMETRY_CONFIG,
    ALIGNMENT_CONFIG,
    ALIGN_PI_CONFIG,
    STATION_EQUATION_CONFIG,
    CGPOINT_CONFIG,
    SURFACE_CONFIG,
    FACE_CONFIG
)


class LandXMLReader:
    """
    LandXML 1.2 file reader for horizontal alignments and CgPoints.
    Parses LandXML files and extracts alignment data with geometry elements and coordinate points.
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
        self.cgpoints_data = []
        self.surfaces_data = []
        
        self.angular_unit = 'decimal degrees'  # Default
        self.direction_unit = 'decimal degrees'  # Default
        self.angular_conversion_factor = ANGULAR_UNITS['decimal degrees']
        self.direction_conversion_factor = ANGULAR_UNITS['decimal degrees']
    
        # Parse the XML file and parse units
        self._parse_xml()
        self._parse_units()
    
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
    
    def _parse_cgpoint(self, cgpoint_elem: ET.Element) -> Dict:
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
        attributes = self._parse_attributes(cgpoint_elem, config['attr_map'])
        cgpoint_data.update(attributes)
        
        # Move 'code' to 'desc' if present (code is actually the description)
        if 'code' in cgpoint_data and 'desc' not in cgpoint_data:
            cgpoint_data['desc'] = cgpoint_data['code']
            del cgpoint_data['code']
        
        # Get point coordinates from element text
        point_text = cgpoint_elem.text
        if point_text:
            coords = self._parse_point(point_text.strip())
            if coords:
                if len(coords) == 3:
                    cgpoint_data['easting'] = coords[1]
                    cgpoint_data['northing'] = coords[0]
                    cgpoint_data['elevation'] = coords[2]
                else:
                    cgpoint_data['easting'] = coords[1]
                    cgpoint_data['northing'] = coords[0]
        
        return cgpoint_data

    def _parse_surface_points(self, surface_elem: ET.Element) -> List[Dict]:
        """
        Parse P (Point) elements within a Surface Definition element.
        
        Args:
            surface_elem: Surface Definition XML element
            
        Returns:
            List of point dictionaries with id and coordinates
        """
        points = []
        
        # First find the Pnts container element
        pnts_elem = self._find_element(surface_elem, 'Pnts')
        if pnts_elem is None:
            return points
        
        # Find all P elements within Pnts
        p_elements = self._find_all_elements(pnts_elem, 'P')
        
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
                
                coords = self._parse_point(point_text.strip())
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
    
    def _parse_surface_faces(self, surface_elem: ET.Element) -> List[Dict]:
        """
        Parse F (Face) elements within a Surface Definition element.
        
        Args:
            surface_elem: Surface Definition XML element
            
        Returns:
            List of face dictionaries with point references
        """
        faces = []
        
        # First find the Faces container element
        faces_elem = self._find_element(surface_elem, 'Faces')
        if faces_elem is None:
            return faces
        
        # Find all F elements within Faces
        f_elements = self._find_all_elements(faces_elem, 'F')
        
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

    def _parse_surface(self, surface_elem: ET.Element) -> Dict:
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
        attributes = self._parse_attributes(surface_elem, config['attr_map'])
        surface_data.update(attributes)
        
        # Find Definition element (contains Pnts and Faces elements)
        definition_elem = self._find_element(surface_elem, 'Definition')
        
        if definition_elem is not None:
            # Parse surface type
            surf_type = definition_elem.attrib.get('surfType', 'TIN')
            surface_data['surfType'] = surf_type
            
            # Parse points (P elements within Pnts)
            points = self._parse_surface_points(definition_elem)
            if points:
                surface_data['points'] = points
            
            # Parse faces (F elements within Faces) - for TIN surfaces
            faces = self._parse_surface_faces(definition_elem)
            if faces:
                surface_data['faces'] = faces
        
        return surface_data
    
    def read_cgpoints(self) -> List[Dict]:
        """
        Read all CgPoints from LandXML file, organized by groups.
        Groups can be defined by <CgPoints name="..."> containers with pntRef references.
        
        Returns:
            List of group dictionaries, each containing group name and list of points
        """
        groups = []
        
        # Find CgPoints container
        cgpoints_elements = self._find_all_elements(self.root, 'CgPoints')
        
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
                        cgpoint_data = self._parse_cgpoint(child)
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
                point_refs = self._find_all_elements(cgpoints_elem, 'CgPoint')
                
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
        
        self.cgpoints_data = groups
        return groups

    def read_surfaces(self) -> List[Dict]:
        """
        Read all Surfaces from LandXML file.
        
        Returns:
            List of Surface data dictionaries
        """
        surfaces = []
        
        # Find Surfaces container
        surfaces_elem = self._find_element(self.root, 'Surfaces')
        
        if surfaces_elem is None:
            print("Warning: No Surfaces element found in LandXML file")
            return surfaces
        
        # Find all Surface elements
        surface_elements = self._find_all_elements(surfaces_elem, 'Surface')
        
        if not surface_elements:
            print("Warning: No Surface elements found in LandXML file")
            return surfaces
        
        # Parse each Surface
        for surface_elem in surface_elements:
            try:
                surface_data = self._parse_surface(surface_elem)
                # Only add if surface has at least name
                if 'name' in surface_data:
                    surfaces.append(surface_data)
            except Exception as e:
                print(f"Warning: Failed to parse Surface: {str(e)}")
                continue
        
        self.surfaces_data = surfaces
        return surfaces
    
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
            print("Warning: No Alignments elements found in LandXML file")
            return alignments
        
        # Find all Alignment elements
        alignment_elements = self._find_all_elements(alignments_elem, 'Alignment')
        
        if not alignment_elements:
            print("Warning: No Alignment elements found in LandXML file")
            return alignments
        
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
    
    def get_alignment_names(self) -> List[str]:
        """
        Get list of all alignment names in the file.
        
        Returns:
            List of alignment names
        """
        if not self.alignments_data:
            self.read_alignments()
        
        return [align.get('name', 'Unnamed') for align in self.alignments_data]
    
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

    def get_surface_names(self) -> List[str]:
        """
        Get list of all Surface names in the file.
        
        Returns:
            List of surface names
        """
        if not self.surfaces_data:
            self.read_surfaces()
        
        return [surf.get('name', 'Unnamed') for surf in self.surfaces_data]
    
    def get_alignment_count(self) -> int:
        """
        Get number of alignments in the file.
        
        Returns:
            Count of alignments
        """
        if not self.alignments_data:
            self.read_alignments()
        
        return len(self.alignments_data)
    
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
            Dictionary containing file info, alignments, CgPoints, and Surfaces
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
            'alignments': self.alignments_data,
            'cgpoint_groups': self.cgpoints_data,
            'surfaces': self.surfaces_data
        }
# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""LandXML Parser Class for processing LandXML files."""

import FreeCAD
import Part
import Mesh
from ..make import make_terrain, make_alignment
from .alignment import get_geometry

import xml.etree.ElementTree as ET


class LandXMLParser:
    """
    Class for parsing and processing LandXML files.
    """
    
    def __init__(self):
        self.xml_data = None
        self.file_path = None
        self.surfaces = []
        self.alignments = []
        self.cogo_points = []  # CogoPoints listesi eklendi
        self.units = None
        self.project_info = None
        self.application_info = None
        
    def load_file(self, file_path):
        """
        Loads and parses a LandXML file.
        
        Args:
            file_path (str): Path to the LandXML file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            tree = ET.parse(file_path)
            self.xml_data = tree.getroot()
            self.file_path = file_path
            
            # Parse basic information
            self._parse_metadata()
            self._parse_surfaces()
            self._parse_alignments()
            self._parse_cogo_points()  # CogoPoints parsing eklendi
            
            return True
            
        except Exception as e:
            print(f"File loading error: {e}")
            return False
            
    def _parse_metadata(self):
        """Parses metadata from the XML file."""
        if self.xml_data is None:
            return
            
        # Get units information
        units = self.xml_data.find('.//{*}Units')
        if units is not None:
            self.units = units.attrib
            
        # Get project information
        project = self.xml_data.find('.//{*}Project')
        if project is not None:
            self.project_info = {
                'name': project.get('name', 'Unnamed'),
                'attributes': project.attrib
            }
            
        # Get application information
        app = self.xml_data.find('.//{*}Application')
        if app is not None:
            self.application_info = {
                'name': app.get('name', 'Unknown'),
                'description': app.get('desc', ''),
                'attributes': app.attrib
            }
            
    def _parse_surfaces(self):
        """Parses surfaces from the XML file."""
        if self.xml_data is None:
            return
            
        self.surfaces = []
        for surface in self.xml_data.findall('.//{*}Surface'):
            surface_data = {
                'element': surface,
                'name': surface.get('name', 'Unnamed Surface'),
                'attributes': surface.attrib,
                'type': 'surface'
            }
            self.surfaces.append(surface_data)
            
    def _parse_alignments(self):
        """Parses alignments from the XML file."""
        if self.xml_data is None:
            return
            
        self.alignments = []
        for alignment in self.xml_data.findall('.//{*}Alignment'):
            alignment_data = {
                'element': alignment,
                'name': alignment.get('name', 'Unnamed Alignment'),
                'attributes': alignment.attrib,
                'type': 'alignment'
            }
            self.alignments.append(alignment_data)

    def _parse_cogo_points(self):
        """Parses CogoPoints and CgPoints clusters from the XML file."""
        if self.xml_data is None:
            return

        self.cogo_points = []
        points_dict = {}

        # 1. Collect all defined CgPoints with coordinates
        for cg_point in self.xml_data.findall('.//{*}CgPoint'):
            if cg_point.text and cg_point.text.strip():
                coords = cg_point.text.strip().split()
                point_id = cg_point.get('name') or cg_point.get('id') or cg_point.get('pntRef')
                if not point_id:
                    continue

                point_data = {
                    'element': cg_point,
                    'name': cg_point.get('name', f"Point_{point_id}"),
                    'point_id': point_id,
                    'code': cg_point.get('code', ''),
                    'desc': cg_point.get('desc', ''),
                    'attributes': cg_point.attrib,
                    'type': 'cogo_point'
                }

                # Extract coordinate values (Easting, Northing, Elevation)
                if len(coords) >= 3:
                    point_data['x'] = float(coords[1])  # Northing
                    point_data['y'] = float(coords[0])  # Easting
                    point_data['z'] = float(coords[2])  # Elevation
                elif len(coords) == 2:
                    point_data['x'] = float(coords[1])
                    point_data['y'] = float(coords[0])
                    point_data['z'] = 0.0  # Default elevation if missing

                # Store in dictionary for later reference
                points_dict[point_id] = point_data

        # 2. Parse CgPoints clusters with point references
        for cg_points in self.xml_data.findall('.//{*}CgPoints'):
            cogo_point_group = {
                'element': cg_points,
                'name': cg_points.get('name', f"CogoPoints Group {len(self.cogo_points) + 1}"),
                'attributes': cg_points.attrib,
                'type': 'cogo_points_group',
                'points': []
            }

            # Add referenced points to the group
            for cg_point in cg_points.findall('.//{*}CgPoint'):
                ref_id = cg_point.get('pntRef')
                if ref_id and ref_id in points_dict:
                    cogo_point_group['points'].append(points_dict[ref_id])

            if cogo_point_group['points']:
                self.cogo_points.append(cogo_point_group)

        # 3. Handle ungrouped points (not referenced in any cluster)
        grouped_ids = {p['point_id'] for g in self.cogo_points for p in g['points']}
        leftover_points = [p for pid, p in points_dict.items() if pid not in grouped_ids]

        if leftover_points:
            no_group = {
                'element': None,
                'name': 'Ungrouped CogoPoints',
                'attributes': {},
                'type': 'cogo_points_group',
                'points': leftover_points
            }
            self.cogo_points.append(no_group)

    def get_tree_data(self):
        """
        Returns data needed for UI TreeWidget.
        
        Returns:
            dict: Data structure for tree view
        """
        tree_data = {
            'metadata': {
                'units': self.units,
                'project': self.project_info,
                'application': self.application_info
            },
            'surfaces': self.surfaces,
            'alignments': self.alignments,
            'cogo_points': self.cogo_points  # CogoPoints eklendi
        }
        return tree_data
        
    def process_surface(self, surface_data):
        """
        Converts selected surface to FreeCAD Mesh object.
        
        Args:
            surface_data (dict): Parsed surface data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            surface = surface_data['element']
            mesh_obj = Mesh.Mesh()
            
            # Get faces and points for TIN surfaces
            faces = surface.findall('.//{*}Faces/{*}F')
            pnts = surface.findall('.//{*}Pnts/{*}P')
            
            # Create points dictionary
            points_dict = {}
            for pnt in pnts:
                pid = pnt.get('id')
                coords = pnt.text.strip().split()
                if len(coords) >= 3:
                    x, y, z = float(coords[1]), float(coords[0]), float(coords[2])
                    points_dict[pid] = FreeCAD.Vector(x * 1000, y * 1000, z * 1000)
            
            # Add faces
            for face in faces:
                vertices_str = face.text.strip().split()
                if len(vertices_str) >= 3:
                    try:
                        v1 = points_dict[vertices_str[0]]
                        v2 = points_dict[vertices_str[1]]
                        v3 = points_dict[vertices_str[2]]
                        mesh_obj.addFacet(v1, v2, v3)
                    except KeyError:
                        continue
                        
            # Add mesh to FreeCAD
            if mesh_obj.CountFacets > 0:
                terrain = make_terrain.create(label=surface_data['name'])
                terrain.Mesh = mesh_obj
                FreeCAD.ActiveDocument.recompute()
                return True
                
        except Exception as e:
            print(f"Surface processing error: {e}")
            
        return False
        
    def process_alignment(self, alignment_data):
        """
        Converts selected alignment to FreeCAD object.
        
        Args:
            alignment_data (dict): Parsed alignment data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            alignment = alignment_data['element']
            parsed_alignment = self._parse_alignment_geometry(alignment)
            print(parsed_alignment)
            
            if parsed_alignment:
                alignment_obj = make_alignment.create(label=alignment_data['name'])
                alignment_obj.Model = parsed_alignment
                return True
                    
        except Exception as e:
            print(f"Alignment processing error: {e}")
            
        return False

    def process_cogo_points(self, cogo_points_data):
        """
        Converts selected CogoPoints to FreeCAD GeoPoint objects and organizes them in clusters.
        
        Args:
            cogo_points_data (dict): Parsed CogoPoints data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Import required modules
            from ..make import make_geopoint, make_cluster
            
            points_created = 0
            
            # Create cluster for this CogoPoints group
            cluster_name = cogo_points_data.get('name', 'CogoPoints Group')
            cluster_obj = make_cluster.create(label=cluster_name)
            
            # Process each point in the group
            for point_data in cogo_points_data['points']:
                if 'x' in point_data and 'y' in point_data and 'z' in point_data:
                    # GeoPoint parameters
                    name = point_data['name']
                    easting = point_data['x']  # X coordinate is Easting
                    northing = point_data['y']  # Y coordinate is Northing
                    elevation = point_data['z']  # Z coordinate is Elevation
                    
                    # Create description
                    description_parts = []
                    if point_data.get('point_id'):
                        description_parts.append(f"ID: {point_data['point_id']}")
                    if point_data.get('code'):
                        description_parts.append(f"Code: {point_data['code']}")
                    if point_data.get('desc'):
                        description_parts.append(f"Desc: {point_data['desc']}")
                    
                    description = ", ".join(description_parts) if description_parts else ""
                    
                    # Create GeoPoint
                    geopoint_obj = make_geopoint.create(
                        name=name,
                        easting=easting,
                        northing=northing,
                        elevation=elevation,
                        description=description
                    )
                    
                    # Add GeoPoint to cluster using addObject
                    cluster_obj.addObject(geopoint_obj)
                    points_created += 1
            
            if points_created > 0:
                FreeCAD.ActiveDocument.recompute()
                print(f"Successfully created {points_created} GeoPoint objects in cluster '{cluster_name}'")
                return True
            else:
                # If no points were created, remove empty cluster
                clusters = FreeCAD.ActiveDocument.getObjectsByLabel("Clusters")
                if clusters:
                    clusters[0].removeObject(cluster_obj)
                    FreeCAD.ActiveDocument.removeObject(cluster_obj.Name)
                
        except Exception as e:
            print(f"CogoPoints processing error: {e}")
            
        return False
    def _parse_alignment_geometry(self, alignment):
        """
        Parses alignment geometry from LandXML format by grouping consecutive elements
        and finding PI points for each transition group.
        
        Args:
            alignment: XML alignment element
            
        Returns:
            dict: Parsed alignment geometry in the format expected by get_geometry()
        """
        try:
            coord_geom = alignment.find('.//{*}CoordGeom')
            if coord_geom is None:
                print("No CoordGeom found in alignment")
                return None
                
            # Get all geometry elements in order
            geom_elements = []
            for child in coord_geom:
                if child.tag.split('}')[-1] in ['Line', 'Curve', 'Spiral']:
                    geom_elements.append({
                        'type': child.tag.split('}')[-1],
                        'element': child
                    })
            
            if not geom_elements:
                print("No geometry elements found")
                return None
                
            # Dictionary to store PI points
            pi_data = {}
            pi_index = 0
            
            # Add starting point as first PI
            first_elem = geom_elements[0]['element']
            start_coords = self._extract_coordinates(first_elem, 'Start')
            if start_coords:
                pi_data[f'PI{pi_index}'] = {
                    'X': start_coords[0],
                    'Y': start_coords[1],
                    'Spiral Length In': 0.0,
                    'Spiral Length Out': 0.0,
                    'Radius': 0.0,
                    'Curve Type': 'None'
                }
                pi_index += 1
            
            # Process elements by grouping them into transition sequences
            i = 0
            while i < len(geom_elements):
                current_group = []
                
                # Identify the current transition group
                if geom_elements[i]['type'] == 'Line':
                    # Line segments don't create PI points, just continue
                    i += 1
                    continue
                    
                elif geom_elements[i]['type'] == 'Spiral':
                    # Check if it's part of Spiral-Curve-Spiral sequence
                    if (i + 2 < len(geom_elements) and 
                        geom_elements[i + 1]['type'] == 'Curve' and 
                        geom_elements[i + 2]['type'] == 'Spiral'):
                        
                        # Spiral-Curve-Spiral group
                        current_group = [geom_elements[i], geom_elements[i + 1], geom_elements[i + 2]]
                        pi_point = self._process_spiral_curve_spiral_group(current_group)
                        i += 3
                        
                    else:
                        # Single spiral (rare case)
                        current_group = [geom_elements[i]]
                        pi_point = self._process_single_spiral_group(current_group)
                        i += 1
                        
                elif geom_elements[i]['type'] == 'Curve':
                    # Simple curve
                    current_group = [geom_elements[i]]
                    pi_point = self._process_curve_group(current_group)
                    i += 1
                
                # Add the calculated PI point
                if 'pi_point' in locals() and pi_point:
                    pi_data[f'PI{pi_index}'] = pi_point
                    pi_index += 1
                    del pi_point
            
            # Add ending point as final PI
            last_elem = geom_elements[-1]['element']
            end_coords = self._extract_coordinates(last_elem, 'End')
            if end_coords:
                pi_data[f'PI{pi_index}'] = {
                    'X': end_coords[0],
                    'Y': end_coords[1],
                    'Spiral Length In': 0.0,
                    'Spiral Length Out': 0.0,
                    'Radius': 0.0,
                    'Curve Type': 'None'
                }
            
            return pi_data if pi_data else None
            
        except Exception as e:
            print(f"Error parsing alignment geometry: {e}")
            return None

    def _process_spiral_curve_spiral_group(self, group):
        """
        Process Spiral-Curve-Spiral group and calculate PI point.
        
        Args:
            group: List of [spiral_in, curve, spiral_out] elements
            
        Returns:
            dict: PI point data
        """
        try:
            spiral_in_elem = group[0]['element']
            curve_elem = group[1]['element']
            spiral_out_elem = group[2]['element']
            
            # Get curve PI coordinates (this is our main PI point)
            pi_coords = self._extract_coordinates(curve_elem, 'PI')
            if not pi_coords:
                # If no PI in curve, try to calculate from curve center and geometry
                center_coords = self._extract_coordinates(curve_elem, 'Center')
                start_coords = self._extract_coordinates(curve_elem, 'Start')
                end_coords = self._extract_coordinates(curve_elem, 'End')
                
                if center_coords and start_coords and end_coords:
                    # Calculate PI from curve geometry
                    pi_coords = self._calculate_curve_pi(center_coords, start_coords, end_coords)
            
            if not pi_coords:
                print("Could not determine PI coordinates for spiral-curve-spiral group")
                return None
            
            # Get parameters
            spiral_in_length = float(spiral_in_elem.get('length', 0.0))
            spiral_out_length = float(spiral_out_elem.get('length', 0.0))
            radius = float(curve_elem.get('radius', 0.0))

            return {
                'X': pi_coords[0],
                'Y': pi_coords[1],
                'Spiral Length In': spiral_in_length,
                'Spiral Length Out': spiral_out_length,
                'Radius': radius,
                'Curve Type': 'Spiral-Curve-Spiral'
            }
            
        except Exception as e:
            print(f"Error processing spiral-curve-spiral group: {e}")
            return None

    def _process_curve_group(self, group):
        """
        Process simple Curve group and calculate PI point.
        
        Args:
            group: List with single curve element
            
        Returns:
            dict: PI point data
        """
        try:
            curve_elem = group[0]['element']
            
            # Get PI coordinates
            pi_coords = self._extract_coordinates(curve_elem, 'PI')
            if not pi_coords:
                # If no PI in curve, try to calculate from curve center and geometry
                center_coords = self._extract_coordinates(curve_elem, 'Center')
                start_coords = self._extract_coordinates(curve_elem, 'Start')
                end_coords = self._extract_coordinates(curve_elem, 'End')
                
                if center_coords and start_coords and end_coords:
                    pi_coords = self._calculate_curve_pi(center_coords, start_coords, end_coords)
            
            if not pi_coords:
                print("Could not determine PI coordinates for curve group")
                return None
            
            radius = float(curve_elem.get('radius', 0.0))
            
            return {
                'X': pi_coords[0],
                'Y': pi_coords[1],
                'Spiral Length In': 0.0,
                'Spiral Length Out': 0.0,
                'Radius': radius,
                'Curve Type': 'Curve'
            }
            
        except Exception as e:
            print(f"Error processing curve group: {e}")
            return None

    def _process_single_spiral_group(self, group):
        """
        Process single Spiral group.
        
        Args:
            group: List with single spiral element
            
        Returns:
            dict: PI point data
        """
        try:
            spiral_elem = group[0]['element']
            
            # Get PI coordinates
            pi_coords = self._extract_coordinates(spiral_elem, 'PI')
            if not pi_coords:
                # For spirals without PI, use end point
                pi_coords = self._extract_coordinates(spiral_elem, 'End')
            
            if not pi_coords:
                print("Could not determine PI coordinates for spiral group")
                return None
            
            spiral_length = float(spiral_elem.get('length', 0.0))
            radius_end = spiral_elem.get('radiusEnd', 'INF')
            radius_start = spiral_elem.get('radiusStart', 'INF')
            
            # Determine spiral type and parameters
            if radius_start == 'INF' and radius_end != 'INF':
                # Spiral in
                spiral_in_length = spiral_length
                spiral_out_length = 0.0
                radius = float(radius_end)
            elif radius_start != 'INF' and radius_end == 'INF':
                # Spiral out
                spiral_in_length = 0.0
                spiral_out_length = spiral_length
                radius = float(radius_start)
            else:
                spiral_in_length = spiral_length
                spiral_out_length = 0.0
                radius = 0.0
            
            return {
                'X': pi_coords[0],
                'Y': pi_coords[1],
                'Spiral Length In': spiral_in_length,
                'Spiral Length Out': spiral_out_length,
                'Radius': radius,
                'Curve Type': 'Spiral-Curve-Spiral' if radius > 0 else 'None'
            }
            
        except Exception as e:
            print(f"Error processing single spiral group: {e}")
            return None

    def _calculate_curve_pi(self, center_coords, start_coords, end_coords):
        """
        Calculate PI point from curve center and start/end points.
        
        Args:
            center_coords: (x, y) of curve center
            start_coords: (x, y) of curve start
            end_coords: (x, y) of curve end
            
        Returns:
            tuple: (x, y) coordinates of PI point
        """
        try:
            import math
            
            # Calculate tangent lines from start and end points
            # Vector from center to start
            start_vec = (start_coords[0] - center_coords[0], start_coords[1] - center_coords[1])
            # Vector from center to end  
            end_vec = (end_coords[0] - center_coords[0], end_coords[1] - center_coords[1])
            
            # Tangent vectors (perpendicular to radial vectors)
            start_tangent = (-start_vec[1], start_vec[0])
            end_tangent = (-end_vec[1], end_vec[0])
            
            # Calculate intersection of tangent lines (this is the PI point)
            # Line 1: start_coords + t * start_tangent
            # Line 2: end_coords + s * end_tangent
            # Solve for intersection
            
            det = start_tangent[0] * end_tangent[1] - start_tangent[1] * end_tangent[0]
            if abs(det) < 1e-10:
                return None  # Lines are parallel
            
            dx = end_coords[0] - start_coords[0]
            dy = end_coords[1] - start_coords[1]
            
            t = (dx * end_tangent[1] - dy * end_tangent[0]) / det
            
            pi_x = start_coords[0] + t * start_tangent[0]
            pi_y = start_coords[1] + t * start_tangent[1]
            
            return (pi_x, pi_y)
            
        except Exception as e:
            print(f"Error calculating PI from curve geometry: {e}")
            return None

    def _extract_coordinates(self, element, coord_type):
        """
        Extracts coordinates from geometry element.
        
        Args:
            element: XML geometry element
            coord_type: Type of coordinates ('Start', 'End', 'PI', 'Center')
            
        Returns:
            tuple: (x, y) coordinates or None if not found
        """
        try:
            coord_elem = element.find(f'.//{coord_type}')
            if coord_elem is None:
                # Try with wildcard namespace
                coord_elem = element.find(f'.//{{{element.nsmap[None] if hasattr(element, "nsmap") and element.nsmap else "*"}}}{coord_type}')
                
            if coord_elem is not None and coord_elem.text:
                coords = coord_elem.text.strip().split()
                if len(coords) >= 2:
                    return (float(coords[0]), float(coords[1]))
                    
        except Exception as e:
            print(f"Error extracting {coord_type} coordinates: {e}")
            
        return None

    def process_selected_items(self, selected_items):
        """
        Processes selected items in bulk.
        
        Args:
            selected_items (list): List of items to process
            
        Returns:
            dict: Processing results
        """
        results = {
            'surfaces_processed': 0,
            'alignments_processed': 0,
            'cogo_points_processed': 0,  # Total points created
            'cogo_clusters_processed': 0,  # Number of clusters created
            'errors': []
        }
        
        for item_data in selected_items:
            try:
                if item_data['type'] == 'surface':
                    if self.process_surface(item_data):
                        results['surfaces_processed'] += 1
                        
                elif item_data['type'] == 'alignment':
                    if self.process_alignment(item_data):
                        results['alignments_processed'] += 1
                        
                elif item_data['type'] == 'cogo_points_group':  # Process CogoPoints group
                    if self.process_cogo_points(item_data):
                        results['cogo_points_processed'] += len(item_data['points'])
                        results['cogo_clusters_processed'] += 1
                        
            except Exception as e:
                results['errors'].append(f"{item_data['name']}: {str(e)}")
                
        return results
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
        """Parses CogoPoints from the XML file."""
        if self.xml_data is None:
            return
            
        self.cogo_points = []
        
        # CogoPoints genellikle CgPoints veya CgPoint etiketleri altında bulunur
        for cg_points in self.xml_data.findall('.//{*}CgPoints'):
            cogo_point_group = {
                'element': cg_points,
                'name': cg_points.get('name', 'CogoPoints Group'),
                'attributes': cg_points.attrib,
                'type': 'cogo_points_group',
                'points': []
            }
            
            # Grup içindeki her bir CogoPoint'i parse et
            for cg_point in cg_points.findall('.//{*}CgPoint'):
                point_data = {
                    'element': cg_point,
                    'name': cg_point.get('name', f"Point_{cg_point.get('pntRef', 'Unknown')}"),
                    'point_id': cg_point.get('pntRef', 'Unknown'),
                    'code': cg_point.get('code', ''),
                    'desc': cg_point.get('desc', ''),
                    'attributes': cg_point.attrib,
                    'type': 'cogo_point'
                }
                
                # Koordinat bilgilerini al
                coords_text = cg_point.text
                if coords_text and coords_text.strip():
                    coords = coords_text.strip().split()
                    if len(coords) >= 3:
                        point_data['x'] = float(coords[1])  # Northing
                        point_data['y'] = float(coords[0])  # Easting  
                        point_data['z'] = float(coords[2])  # Elevation
                    elif len(coords) == 2:
                        point_data['x'] = float(coords[1])  # Northing
                        point_data['y'] = float(coords[0])  # Easting
                        point_data['z'] = 0.0  # Default elevation
                        
                cogo_point_group['points'].append(point_data)
            
            self.cogo_points.append(cogo_point_group)
        
        # Tek tek CogoPoint'leri de kontrol et (gruplanmamış olanlar)
        for cg_point in self.xml_data.findall('.//{*}CgPoint'):
            # Bu point'in zaten bir grup içinde olup olmadığını kontrol et
            already_grouped = False
            for group in self.cogo_points:
                if any(p['element'] == cg_point for p in group['points']):
                    already_grouped = True
                    break
            
            if not already_grouped:
                point_data = {
                    'element': cg_point,
                    'name': cg_point.get('name', f"Point_{cg_point.get('pntRef', 'Unknown')}"),
                    'point_id': cg_point.get('pntRef', 'Unknown'),
                    'code': cg_point.get('code', ''),
                    'desc': cg_point.get('desc', ''),
                    'attributes': cg_point.attrib,
                    'type': 'cogo_point'
                }
                
                # Koordinat bilgilerini al
                coords_text = cg_point.text
                if coords_text and coords_text.strip():
                    coords = coords_text.strip().split()
                    if len(coords) >= 3:
                        point_data['x'] = float(coords[1])  # Northing
                        point_data['y'] = float(coords[0])  # Easting
                        point_data['z'] = float(coords[2])  # Elevation
                    elif len(coords) == 2:
                        point_data['x'] = float(coords[1])  # Northing
                        point_data['y'] = float(coords[0])  # Easting
                        point_data['z'] = 0.0  # Default elevation
                
                # Tek başına point için bir grup oluştur
                single_point_group = {
                    'element': None,
                    'name': 'Individual CogoPoints',
                    'attributes': {},
                    'type': 'cogo_points_group',
                    'points': [point_data]
                }
                self.cogo_points.append(single_point_group)
            
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
            
            if parsed_alignment:
                # Create geometry (you should adapt this function from original code)
                points, wire = get_geometry(parsed_alignment)
                if wire:
                    # Create alignment object
                    alignment_obj = make_alignment.create(label=alignment_data['name'])
                    Part.show(wire)
                    return True
                    
        except Exception as e:
            print(f"Alignment processing error: {e}")
            
        return False

    def process_cogo_points(self, cogo_points_data):
        """
        Converts selected CogoPoints to FreeCAD objects.
        
        Args:
            cogo_points_data (dict): Parsed CogoPoints data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            points_created = 0
            
            for point_data in cogo_points_data['points']:
                if 'x' in point_data and 'y' in point_data and 'z' in point_data:
                    # FreeCAD'de point oluştur (mm cinsinden)
                    x = point_data['x'] * 1000  # Convert to mm
                    y = point_data['y'] * 1000  # Convert to mm  
                    z = point_data['z'] * 1000  # Convert to mm
                    
                    # Point objesi oluştur
                    point_obj = FreeCAD.ActiveDocument.addObject("Part::Vertex", f"CogoPoint_{point_data['point_id']}")
                    point_obj.X = x
                    point_obj.Y = y
                    point_obj.Z = z
                    
                    # Ek özellikler ekle
                    point_obj.Label = point_data['name']
                    if hasattr(point_obj, 'addProperty'):
                        point_obj.addProperty("App::PropertyString", "PointID", "CogoPoint", "Point ID")
                        point_obj.addProperty("App::PropertyString", "Code", "CogoPoint", "Point Code")
                        point_obj.addProperty("App::PropertyString", "Description", "CogoPoint", "Point Description")
                        
                        point_obj.PointID = point_data['point_id']
                        point_obj.Code = point_data.get('code', '')
                        point_obj.Description = point_data.get('desc', '')
                    
                    points_created += 1
            
            if points_created > 0:
                FreeCAD.ActiveDocument.recompute()
                return True
                
        except Exception as e:
            print(f"CogoPoints processing error: {e}")
            
        return False
        
    def _parse_alignment_geometry(self, alignment):
        """
        Parses alignment geometry.
        
        Args:
            alignment: XML alignment element
            
        Returns:
            dict: Parsed alignment geometry
        """
        alignment_geom = {}
        
        try:
            # Find geometry elements in CoordGeom
            coord_geom = alignment.find('.//{*}CoordGeom')
            if coord_geom is None:
                return None
                
            pi_index = 0
            for element in coord_geom:
                tag = element.tag.split('}')[-1]
                
                if tag == 'Line':
                    # Get start and end points from Line element
                    start = element.find('.//{*}Start')
                    end = element.find('.//{*}End')
                    
                    if start is not None:
                        coords = start.text.strip().split()
                        if len(coords) >= 2:
                            alignment_geom[f'PI_{pi_index}'] = {
                                'X': coords[1],  # Northing
                                'Y': coords[0],  # Easting
                                'Curve Type': 'None',
                                'Spiral Length In': '0',
                                'Spiral Length Out': '0',
                                'Radius': '0'
                            }
                            pi_index += 1
                            
                elif tag == 'Curve':
                    # Process Curve element
                    radius = element.get('radius', '0')
                    alignment_geom[f'PI_{pi_index}'] = {
                        'X': element.get('centerN', '0'),
                        'Y': element.get('centerE', '0'),
                        'Curve Type': 'Curve',
                        'Spiral Length In': '0',
                        'Spiral Length Out': '0',
                        'Radius': radius
                    }
                    pi_index += 1
                    
                elif tag == 'Spiral':
                    # Process Spiral element
                    length = element.get('length', '0')
                    radius_start = element.get('radiusStart', 'INF')
                    radius_end = element.get('radiusEnd', 'INF')
                    
                    alignment_geom[f'PI_{pi_index}'] = {
                        'X': '0',  # Coordinates should be calculated from spiral
                        'Y': '0',
                        'Curve Type': 'Spiral-Curve-Spiral',
                        'Spiral Length In': length,
                        'Spiral Length Out': length,
                        'Radius': radius_end if radius_end != 'INF' else radius_start
                    }
                    pi_index += 1
                    
        except Exception as e:
            print(f"Alignment geometry parsing error: {e}")
            return None
            
        return alignment_geom

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
            'cogo_points_processed': 0,  # CogoPoints sayacı eklendi
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
                        
                elif item_data['type'] == 'cogo_points_group':  # CogoPoints grubu işleme
                    if self.process_cogo_points(item_data):
                        results['cogo_points_processed'] += len(item_data['points'])
                        
            except Exception as e:
                results['errors'].append(f"{item_data['name']}: {str(e)}")
                
        return results
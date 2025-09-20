import xml.etree.ElementTree as ET
import FreeCAD
import Mesh
import numpy as np

def parse_landxml_surface(landxml_file_path):
    """
    Reads surface data from LandXML file
    """
    try:
        # Parse XML file
        tree = ET.parse(landxml_file_path)
        root = tree.getroot()
        
        # Namespace definitions (LandXML usually uses namespaces)
        namespaces = {'': 'http://www.landxml.org/schema/LandXML-1.2'}
        
        # If no namespace, use empty string
        if not root.tag.startswith('{'):
            namespaces = {'': ''}
        
        points = []
        faces = []
        
        # Find Surface elements
        for surface in root.findall('.//Surface', namespaces):
            print(f"Surface found: {surface.get('name', 'Unnamed')}")
            
            # Find Pnts element under Definition
            definition = surface.find('Definition', namespaces)
            if definition is not None:
                pnts = definition.find('Pnts', namespaces)
                if pnts is not None:
                    # Read points from P elements
                    for p in pnts.findall('P', namespaces):
                        coords = p.text.strip().split()
                        if len(coords) >= 3:
                            x, y, z = map(float, coords[:3])
                            points.append([x, y, z])
                
                # Find Faces element - this is mandatory!
                faces_elem = definition.find('Faces', namespaces)
                if faces_elem is not None:
                    for face in faces_elem.findall('F', namespaces):
                        face_indices = list(map(int, face.text.strip().split()))
                        if len(face_indices) >= 3:
                            # LandXML indices might be 1-based, convert to 0-based
                            face_indices = [idx - 1 for idx in face_indices]
                            faces.append(face_indices)
                else:
                    print("WARNING: <Faces> element not found for this surface!")
                    print("Triangulation information is missing in LandXML file!")
        
        print(f"Points read: {len(points)}")
        print(f"Faces read: {len(faces)}")
        
        return np.array(points), faces
        
    except Exception as e:
        print(f"LandXML reading error: {e}")
        return None, None

def parse_landxml_alignment(landxml_file_path):
    """
    Reads alignment data from LandXML file and converts to get_geometry compatible format
    """
    try:
        # Parse XML file
        tree = ET.parse(landxml_file_path)
        root = tree.getroot()
        
        # Namespace definitions
        namespaces = {'': 'http://www.landxml.org/schema/LandXML-1.2'}
        
        # If no namespace, use empty string
        if not root.tag.startswith('{'):
            namespaces = {'': ''}
        
        alignments_data = {}
        
        # Find Alignment elements
        for alignment in root.findall('.//Alignment', namespaces):
            alignment_name = alignment.get('name', 'Unnamed')
            print(f"Alignment found: {alignment_name}")
            
            # Find geometry elements under CoordGeom element
            coord_geom = alignment.find('CoordGeom', namespaces)
            if coord_geom is not None:
                # Advanced processing: detect Spiral-Curve-Spiral groups
                alignment_points = process_spiral_curve_spiral_group(coord_geom, namespaces)
                alignments_data[alignment_name] = alignment_points
        
        return alignments_data
        
    except Exception as e:
        print(f"Alignment reading error: {e}")
        return None

def calculate_curve_center(curve_element):
    """
    Calculates center point from Curve element
    """
    try:
        # Various possible center point attributes
        center_x = (curve_element.get('centerX') or 
                   curve_element.get('cxX') or 
                   curve_element.get('centerNorthing'))
        center_y = (curve_element.get('centerY') or 
                   curve_element.get('cxY') or 
                   curve_element.get('centerEasting'))
        
        if center_x and center_y:
            return [float(center_x), float(center_y)]
    except:
        pass
    
    return None

def calculate_pi_point_for_curve(start_point, end_point, center_point, radius):
    """
    Calculates PI (Point of Intersection) point for curve
    """
    if not start_point or not end_point:
        return None
    
    try:
        # Simple approach: take midpoint of start and end points
        # In real application, need to calculate intersection of tangent lines
        
        if center_point:
            # If center point exists, do geometric calculation
            # This requires more complex calculation
            return center_point
        else:
            # Simple approach: midpoint
            pi_x = (start_point[0] + end_point[0]) / 2
            pi_y = (start_point[1] + end_point[1]) / 2
            return [pi_x, pi_y]
    
    except:
        return None

def parse_point(element, point_type):
    """
    Extracts point coordinates from XML element (Start/End/Center)
    """
    try:
        if point_type == 'Start':
            # Various possible start point attributes
            x = (element.get('staStart') or element.get('x1') or element.get('startX') or 
                 element.get('startNorthing') or element.get('startEasting'))
            y = (element.get('northStart') or element.get('y1') or element.get('startY') or 
                 element.get('startEasting') or element.get('startNorthing'))
        elif point_type == 'End':
            # Various possible end point attributes
            x = (element.get('staEnd') or element.get('x2') or element.get('endX') or 
                 element.get('endNorthing') or element.get('endEasting'))
            y = (element.get('northEnd') or element.get('y2') or element.get('endY') or 
                 element.get('endEasting') or element.get('endNorthing'))
        elif point_type == 'Center':
            # For center point
            x = (element.get('centerX') or element.get('cxX') or element.get('centerNorthing'))
            y = (element.get('centerY') or element.get('cxY') or element.get('centerEasting'))
        
        if x and y:
            return [float(x), float(y)]
    except Exception as e:
        print(f"Point parsing error ({point_type}): {e}")
    
    return None

def process_spiral_curve_spiral_group(coord_geom, namespaces):
    """
    Detects and processes Spiral-Curve-Spiral groups
    """
    elements = list(coord_geom)
    processed_points = {}
    point_counter = 1
    
    i = 0
    previous_end_point = None
    
    while i < len(elements):
        element = elements[i]
        tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        # Check for Spiral-Curve-Spiral combination
        if (i + 2 < len(elements) and 
            tag_name == 'Spiral' and
            elements[i+1].tag.split('}')[-1] == 'Curve' and 
            elements[i+2].tag.split('}')[-1] == 'Spiral'):
            
            # Spiral-Curve-Spiral group found
            spiral_in = elements[i]
            curve = elements[i+1]
            spiral_out = elements[i+2]
            
            # Start point
            start_point = parse_point(spiral_in, 'Start')
            if previous_end_point is None and start_point:
                processed_points[str(point_counter)] = {
                    'X': str(start_point[0]),
                    'Y': str(start_point[1]),
                    'Curve Type': 'None',
                    'Spiral Length In': '0',
                    'Radius': '0',
                    'Spiral Length Out': '0'
                }
                point_counter += 1
                previous_end_point = start_point
            
            # PI point (curve center point or calculated point)
            curve_start = parse_point(curve, 'Start')
            curve_end = parse_point(curve, 'End')
            curve_center = parse_point(curve, 'Center') or calculate_curve_center(curve)
            
            pi_point = calculate_pi_point_for_curve(curve_start, curve_end, curve_center, 
                                                   float(curve.get('radius', '0')))
            
            if pi_point:
                processed_points[str(point_counter)] = {
                    'X': str(pi_point[0]),
                    'Y': str(pi_point[1]),
                    'Curve Type': 'Spiral-Curve-Spiral',
                    'Spiral Length In': str(float(spiral_in.get('length', '0'))),
                    'Radius': str(float(curve.get('radius', '0'))),
                    'Spiral Length Out': str(float(spiral_out.get('length', '0')))
                }
                point_counter += 1
                previous_end_point = parse_point(spiral_out, 'End')
            
            i += 3  # Skip all three elements
            
        else:
            # Single element processing
            if tag_name == 'Line':
                start_point = parse_point(element, 'Start')
                end_point = parse_point(element, 'End')
                
                if previous_end_point is None and start_point:
                    processed_points[str(point_counter)] = {
                        'X': str(start_point[0]),
                        'Y': str(start_point[1]),
                        'Curve Type': 'None',
                        'Spiral Length In': '0',
                        'Radius': '0',
                        'Spiral Length Out': '0'
                    }
                    point_counter += 1
                    previous_end_point = start_point
                
                if end_point:
                    processed_points[str(point_counter)] = {
                        'X': str(end_point[0]),
                        'Y': str(end_point[1]),
                        'Curve Type': 'None',
                        'Spiral Length In': '0',
                        'Radius': '0',
                        'Spiral Length Out': '0'
                    }
                    point_counter += 1
                    previous_end_point = end_point
            
            elif tag_name == 'Curve':
                start_point = parse_point(element, 'Start')
                end_point = parse_point(element, 'End')
                center_point = parse_point(element, 'Center') or calculate_curve_center(element)
                radius = float(element.get('radius', '0'))
                
                if previous_end_point is None and start_point:
                    processed_points[str(point_counter)] = {
                        'X': str(start_point[0]),
                        'Y': str(start_point[1]),
                        'Curve Type': 'None',
                        'Spiral Length In': '0',
                        'Radius': '0',
                        'Spiral Length Out': '0'
                    }
                    point_counter += 1
                    previous_end_point = start_point
                
                pi_point = calculate_pi_point_for_curve(start_point, end_point, center_point, radius)
                if pi_point:
                    processed_points[str(point_counter)] = {
                        'X': str(pi_point[0]),
                        'Y': str(pi_point[1]),
                        'Curve Type': 'Curve',
                        'Spiral Length In': '0',
                        'Radius': str(radius),
                        'Spiral Length Out': '0'
                    }
                    point_counter += 1
                    previous_end_point = end_point
            
            i += 1
    
    return processed_points

def create_triangulation(points):
    """
    This function is no longer used - only triangles from file are used
    """
    print("WARNING: Triangle data should be read from file, no automatic triangulation!")
    return None

def create_freecad_mesh(points, faces=None):
    """
    Creates FreeCAD mesh object from points and faces
    ONLY uses triangle data from file
    """
    if points is None or len(points) == 0:
        print("No point data found to create mesh")
        return None
    
    if faces is None or len(faces) == 0:
        print("ERROR: No face data found! LandXML file must have <Faces> element.")
        print("No automatic triangulation performed, please use valid LandXML surface file.")
        return None
    
    try:
        # Convert to FreeCAD vector format
        vertices = []
        for point in points:
            vertices.append(FreeCAD.Vector(float(point[0]), float(point[1]), float(point[2])))
        
        # Prepare faces
        triangles = []
        for face in faces:
            if len(face) >= 3:
                # Create triangle (if 4 points, split into two triangles)
                if len(face) == 3:
                    triangles.append(face[:3])
                elif len(face) == 4:
                    # Split quadrilateral into two triangles
                    triangles.append([face[0], face[1], face[2]])
                    triangles.append([face[0], face[2], face[3]])
        
        if len(triangles) == 0:
            print("ERROR: No valid triangle data found!")
            return None
        
        print(f"Creating mesh: {len(vertices)} points, {len(triangles)} triangles")
        
        # Create mesh object
        mesh = Mesh.Mesh()
        
        # Add triangles
        for tri in triangles:
            if len(tri) == 3 and all(0 <= idx < len(vertices) for idx in tri):
                v1 = vertices[tri[0]]
                v2 = vertices[tri[1]]
                v3 = vertices[tri[2]]
                mesh.addFacet(v1, v2, v3)
        
        return mesh
    
    except Exception as e:
        print(f"Mesh creation error: {e}")
        return None

def landxml_to_freecad_mesh(landxml_file_path, mesh_name="LandXML_Surface"):
    """
    Main function: Converts LandXML file to FreeCAD mesh object
    """
    print(f"Processing LandXML file: {landxml_file_path}")
    
    # Read data from LandXML
    points, faces = parse_landxml_surface(landxml_file_path)
    
    if points is None:
        print("Could not read surface data from LandXML file")
        return None
    
    # Create mesh
    mesh = create_freecad_mesh(points, faces)
    
    if mesh is None:
        print("Could not create mesh")
        return None
    
    # Add mesh object to FreeCAD
    try:
        mesh_obj = FreeCAD.ActiveDocument.addObject("Mesh::Feature", mesh_name)
        mesh_obj.Mesh = mesh
        mesh_obj.Label = mesh_name
        
        # Update view
        if hasattr(FreeCAD, 'Gui'):
            FreeCAD.Gui.SendMsgToActiveView("ViewFit")
        
        print(f"Mesh object '{mesh_name}' created successfully")
        print(f"Point count: {mesh.CountPoints}")
        print(f"Face count: {mesh.CountFacets}")
        
        return mesh_obj
    
    except Exception as e:
        print(f"Error adding mesh to FreeCAD: {e}")
        return None

def landxml_get_alignments(landxml_file_path):
    """
    Reads alignment data from LandXML file and returns in specified format
    """
    print(f"Reading LandXML alignment data: {landxml_file_path}")
    
    alignments = parse_landxml_alignment(landxml_file_path)
    
    if alignments:
        print("Found Alignments:")
        for name, data in alignments.items():
            print(f"  {name}: {len(data)} points")
        return alignments
    else:
        print("No alignment data found")
        return None

# Usage examples:
def main():
    """
    Usage example - Both surface and alignment reading
    """
    # Enter your file path here
    landxml_file = "/path/to/your/surface.xml"  # Enter your file path
    
    # Check if there's an active FreeCAD document
    if FreeCAD.ActiveDocument is None:
        FreeCAD.newDocument("LandXML_Import")
    
    print("=== SURFACE PROCESSING ===")
    # Convert LandXML to mesh - ONLY with triangles from file
    mesh_obj = landxml_to_freecad_mesh(landxml_file, "Imported_Surface")
    
    if mesh_obj:
        print("Surface processing successful!")
    else:
        print("Surface processing failed!")
    
    print("\n=== ALIGNMENT PROCESSING ===")
    # Read alignment data
    alignments = landxml_get_alignments(landxml_file)
    
    if alignments:
        print("Alignment data read successfully!")
        print("\nAlignment format:")
        for alignment_name, alignment_data in alignments.items():
            print(f"\n{alignment_name}:")
            for point_id, point_data in alignment_data.items():
                print(f"  {point_id}: {point_data}")
        
        return mesh_obj, alignments
    else:
        print("No alignment data found!")
        return mesh_obj, None

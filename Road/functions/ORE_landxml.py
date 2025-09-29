import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math

from .ORE_alignment import GeometryBlock

@dataclass
class LandXMLPoint:
    """
    Represents a point in LandXML format
    """
    x: float
    y: float
    z: Optional[float] = None


@dataclass
class LandXMLCurve:
    """
    Represents a curve element in LandXML
    """
    radius: float
    length: float
    chord: float
    start_point: LandXMLPoint
    end_point: LandXMLPoint
    center_point: Optional[LandXMLPoint] = None
    rot: Optional[str] = None  # "cw" for clockwise, "ccw" for counter-clockwise


@dataclass
class LandXMLSpiral:
    """
    Represents a spiral element in LandXML
    """
    length: float
    radius_start: Optional[float]
    radius_end: Optional[float]
    start_point: LandXMLPoint
    end_point: LandXMLPoint
    rot: Optional[str] = None


@dataclass
class LandXMLLine:
    """
    Represents a line element in LandXML
    """
    length: float
    start_point: LandXMLPoint
    end_point: LandXMLPoint


class LandXMLParser:
    """
    Parser for LandXML files to extract road geometry information
    """
    
    # LandXML namespace constant
    LANDXML_NS = '{http://www.landxml.org/schema/LandXML-1.2}'
    
    def __init__(self):
        """
        Constructor
        """
        self.geometry_blocks: List[GeometryBlock] = []
        self.current_s = 0.0
        
    def parse_file(self, file_path: str) -> List[GeometryBlock]:
        """
        Parse LandXML file and return geometry blocks
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Find alignments in the XML
            alignments = self._find_alignments(root)
            
            for alignment in alignments:
                self._parse_alignment(alignment)
                
            return self.geometry_blocks
            
        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}")
            return []
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
    
    def parse_string(self, xml_string: str) -> List[GeometryBlock]:
        """
        Parse LandXML from string and return geometry blocks
        """
        try:
            root = ET.fromstring(xml_string)
            
            # Find alignments in the XML
            alignments = self._find_alignments(root)
            
            for alignment in alignments:
                self._parse_alignment(alignment)
                
            return self.geometry_blocks
            
        except ET.ParseError as e:
            print(f"Error parsing XML string: {e}")
            return []
    
    def _find_alignments(self, root: ET.Element) -> List[ET.Element]:
        """
        Find all alignment elements in the XML
        """
        alignments = []
        
        # Try with namespace
        for alignment in root.findall(f'.//{self.LANDXML_NS}Alignment'):
            alignments.append(alignment)
        
        # If not found, try without namespace (for flexibility)
        if not alignments:
            for alignment in root.findall('.//Alignment'):
                alignments.append(alignment)
            
        return alignments
    
    def _parse_alignment(self, alignment: ET.Element):
        """
        Parse a single alignment element
        """
        # Get alignment attributes
        alignment_name = alignment.get('name', 'Unknown')
        alignment_length = float(alignment.get('length', 0.0))
        
        print(f"Parsing alignment: {alignment_name}, Length: {alignment_length}")
        
        # Find coordinate geometry elements (try with and without namespace)
        coord_geom = alignment.find(f'{self.LANDXML_NS}CoordGeom')
        if coord_geom is None:
            coord_geom = alignment.find('CoordGeom')
        
        if coord_geom is not None:
            self._parse_coord_geom(coord_geom)
    
    def _parse_coord_geom(self, coord_geom: ET.Element):
        """
        Parse coordinate geometry elements
        """
        current_x = 0.0
        current_y = 0.0
        current_hdg = 0.0
        
        for element in coord_geom:
            # Remove namespace prefix if present
            tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
            
            if tag == 'Line':
                line = self._parse_line(element)
                if line:
                    self._add_line_geometry(line, current_x, current_y, current_hdg)
                    # Update current position
                    current_x = line.end_point.x
                    current_y = line.end_point.y
                    current_hdg = self._calculate_heading(line.start_point, line.end_point)
                    
            elif tag == 'Curve':
                curve = self._parse_curve(element)
                if curve:
                    self._add_curve_geometry(curve, current_x, current_y, current_hdg)
                    # Update current position
                    current_x = curve.end_point.x
                    current_y = curve.end_point.y
                    current_hdg = self._calculate_curve_end_heading(curve, current_hdg)
                    
            elif tag == 'Spiral':
                spiral = self._parse_spiral(element)
                if spiral:
                    self._add_spiral_geometry(spiral, current_x, current_y, current_hdg)
                    # Update current position
                    current_x = spiral.end_point.x
                    current_y = spiral.end_point.y
                    current_hdg = self._calculate_spiral_end_heading(spiral, current_hdg)
    
    def _parse_line(self, line_elem: ET.Element) -> Optional[LandXMLLine]:
        """
        Parse a line element
        """
        try:
            # Try to find Start/End as child elements first
            start_elem = line_elem.find(f'{self.LANDXML_NS}Start')
            if start_elem is None:
                start_elem = line_elem.find('Start')
            
            end_elem = line_elem.find(f'{self.LANDXML_NS}End')
            if end_elem is None:
                end_elem = line_elem.find('End')
            
            # If elements exist, parse coordinates from text content
            if start_elem is not None and end_elem is not None:
                start_coords = start_elem.text.strip().split()
                end_coords = end_elem.text.strip().split()
                
                start_point = LandXMLPoint(
                    x=float(start_coords[0]),
                    y=float(start_coords[1]),
                    z=float(start_coords[2]) if len(start_coords) > 2 else None
                )
                
                end_point = LandXMLPoint(
                    x=float(end_coords[0]),
                    y=float(end_coords[1]),
                    z=float(end_coords[2]) if len(end_coords) > 2 else None
                )
            else:
                return None
            
            # Get length from attribute or calculate
            length = float(line_elem.get('length', 0.0))
            if length == 0.0:
                length = math.sqrt((end_point.x - start_point.x)**2 + 
                                 (end_point.y - start_point.y)**2)
            
            return LandXMLLine(
                length=length,
                start_point=start_point,
                end_point=end_point
            )
            
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing line element: {e}")
            return None
    
    def _parse_curve(self, curve_elem: ET.Element) -> Optional[LandXMLCurve]:
        """
        Parse a curve element
        """
        try:
            radius = float(curve_elem.get('radius', 0.0))
            length = float(curve_elem.get('length', 0.0))
            chord = float(curve_elem.get('chord', 0.0))
            rot = curve_elem.get('rot', 'ccw')  # Default counter-clockwise
            
            # Try to find Start/End as child elements
            start_elem = curve_elem.find(f'{self.LANDXML_NS}Start')
            if start_elem is None:
                start_elem = curve_elem.find('Start')
            
            end_elem = curve_elem.find(f'{self.LANDXML_NS}End')
            if end_elem is None:
                end_elem = curve_elem.find('End')
            
            center_elem = curve_elem.find(f'{self.LANDXML_NS}Center')
            if center_elem is None:
                center_elem = curve_elem.find('Center')
            
            if start_elem is None or end_elem is None:
                return None
            
            # Parse coordinates from text content
            start_coords = start_elem.text.strip().split()
            end_coords = end_elem.text.strip().split()
            
            start_point = LandXMLPoint(
                x=float(start_coords[0]),
                y=float(start_coords[1]),
                z=float(start_coords[2]) if len(start_coords) > 2 else None
            )
            
            end_point = LandXMLPoint(
                x=float(end_coords[0]),
                y=float(end_coords[1]),
                z=float(end_coords[2]) if len(end_coords) > 2 else None
            )
            
            center_point = None
            if center_elem is not None:
                center_coords = center_elem.text.strip().split()
                center_point = LandXMLPoint(
                    x=float(center_coords[0]),
                    y=float(center_coords[1]),
                    z=float(center_coords[2]) if len(center_coords) > 2 else None
                )
            
            return LandXMLCurve(
                radius=radius,
                length=length,
                chord=chord,
                start_point=start_point,
                end_point=end_point,
                center_point=center_point,
                rot=rot
            )
            
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing curve element: {e}")
            return None
    
    def _parse_spiral(self, spiral_elem: ET.Element) -> Optional[LandXMLSpiral]:
        """
        Parse a spiral element
        """
        try:
            length = float(spiral_elem.get('length', 0.0))
            radius_start = spiral_elem.get('radiusStart')
            radius_end = spiral_elem.get('radiusEnd')
            rot = spiral_elem.get('rot', 'ccw')
            
            # Try to find Start/End as child elements
            start_elem = spiral_elem.find(f'{self.LANDXML_NS}Start')
            if start_elem is None:
                start_elem = spiral_elem.find('Start')
            
            end_elem = spiral_elem.find(f'{self.LANDXML_NS}End')
            if end_elem is None:
                end_elem = spiral_elem.find('End')
            
            if start_elem is None or end_elem is None:
                return None
            
            # Parse coordinates from text content
            start_coords = start_elem.text.strip().split()
            end_coords = end_elem.text.strip().split()
            
            start_point = LandXMLPoint(
                x=float(start_coords[0]),
                y=float(start_coords[1]),
                z=float(start_coords[2]) if len(start_coords) > 2 else None
            )
            
            end_point = LandXMLPoint(
                x=float(end_coords[0]),
                y=float(end_coords[1]),
                z=float(end_coords[2]) if len(end_coords) > 2 else None
            )
            
            # Handle "INF" radius values
            if radius_start and radius_start.upper() != 'INF':
                radius_start_val = float(radius_start)
            else:
                radius_start_val = None
            
            if radius_end and radius_end.upper() != 'INF':
                radius_end_val = float(radius_end)
            else:
                radius_end_val = None
            
            return LandXMLSpiral(
                length=length,
                radius_start=radius_start_val,
                radius_end=radius_end_val,
                start_point=start_point,
                end_point=end_point,
                rot=rot
            )
            
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing spiral element: {e}")
            return None
    
    def _add_line_geometry(self, line: LandXMLLine, start_x: float, start_y: float, start_hdg: float):
        """
        Add line geometry to the current block
        """
        block = GeometryBlock()
        block.add_geometry_line(
            s=self.current_s,
            x=start_x,
            y=start_y,
            hdg=start_hdg,
            length=line.length
        )
        self.geometry_blocks.append(block)
        self.current_s += line.length
    
    def _add_curve_geometry(self, curve: LandXMLCurve, start_x: float, start_y: float, start_hdg: float):
        """
        Add curve geometry to the current block
        """
        # Calculate curvature from radius
        curvature = 1.0 / curve.radius if curve.radius != 0 else 0.0
        
        # Adjust curvature sign based on rotation direction
        if curve.rot == 'cw':  # Clockwise
            curvature = -curvature
        
        block = GeometryBlock()
        block.add_geometry_arc(
            s=self.current_s,
            x=start_x,
            y=start_y,
            hdg=start_hdg,
            length=curve.length,
            curvature=curvature
        )
        self.geometry_blocks.append(block)
        self.current_s += curve.length
    
    def _add_spiral_geometry(self, spiral: LandXMLSpiral, start_x: float, start_y: float, start_hdg: float):
        """
        Add spiral geometry to the current block
        """
        # Calculate curvatures from radii
        curvature_start = 0.0
        curvature_end = 0.0
        
        if spiral.radius_start and spiral.radius_start != 0:
            curvature_start = 1.0 / spiral.radius_start
        
        if spiral.radius_end and spiral.radius_end != 0:
            curvature_end = 1.0 / spiral.radius_end
        
        # Adjust curvature signs based on rotation direction
        if spiral.rot == 'cw':  # Clockwise
            curvature_start = -curvature_start
            curvature_end = -curvature_end
        
        block = GeometryBlock()
        block.add_geometry_spiral(
            s=self.current_s,
            x=start_x,
            y=start_y,
            hdg=start_hdg,
            length=spiral.length,
            curvature_start=curvature_start,
            curvature_end=curvature_end
        )
        self.geometry_blocks.append(block)
        self.current_s += spiral.length
    
    def _calculate_heading(self, start_point: LandXMLPoint, end_point: LandXMLPoint) -> float:
        """
        Calculate heading from start point to end point
        """
        dx = end_point.x - start_point.x
        dy = end_point.y - start_point.y
        return math.atan2(dy, dx)
    
    def _calculate_curve_end_heading(self, curve: LandXMLCurve, start_hdg: float) -> float:
        """
        Calculate the heading at the end of a curve
        """
        # Calculate the central angle
        central_angle = curve.length / curve.radius if curve.radius != 0 else 0.0
        
        # Adjust for rotation direction
        if curve.rot == 'cw':
            central_angle = -central_angle
        
        return start_hdg + central_angle
    
    def _calculate_spiral_end_heading(self, spiral: LandXMLSpiral, start_hdg: float) -> float:
        """
        Calculate the heading at the end of a spiral
        """
        # For spiral, the heading change depends on the curvature change
        # This is a simplified calculation
        if spiral.radius_end and spiral.radius_end != 0:
            curvature_end = 1.0 / spiral.radius_end
            if spiral.rot == 'cw':
                curvature_end = -curvature_end
            
            # Approximate heading change
            heading_change = 0.5 * curvature_end * spiral.length
            return start_hdg + heading_change
        
        return start_hdg
    
    def get_total_length(self) -> float:
        """
        Get total length of all geometry blocks
        """
        total_length = 0.0
        for block in self.geometry_blocks:
            total_length += block.get_block_length()
        return total_length
    
    def get_coordinates_at_station(self, station: float) -> Tuple[float, float, float]:
        """
        Get coordinates and heading at a specific station
        """
        for block in self.geometry_blocks:
            if block.check_interval(station):
                x, y, hdg, _ = block.get_coords_with_hdg(station)
                return x, y, hdg
        
        return 0.0, 0.0, 0.0
    
    def export_to_csv(self, filename: str, interval: float = 1.0):
        """
        Export the parsed geometry to CSV format for analysis
        """
        total_length = self.get_total_length()
        
        with open(filename, 'w') as f:
            f.write("Station,X,Y,Heading,GeometryType\n")
            
            station = 0.0
            while station <= total_length:
                x, y, hdg = self.get_coordinates_at_station(station)
                
                # Find geometry type at this station
                geom_type = "Unknown"
                for block in self.geometry_blocks:
                    if block.check_interval(station):
                        _, _, _, type_code = block.get_coords_with_hdg(station)
                        if type_code == 0:
                            geom_type = "Line"
                        elif type_code == 1:
                            geom_type = "Arc"
                        elif type_code == 2:
                            geom_type = "Spiral"
                        elif type_code == 3:
                            geom_type = "Poly3"
                        break
                
                f.write(f"{station:.3f},{x:.3f},{y:.3f},{hdg:.6f},{geom_type}\n")
                station += interval

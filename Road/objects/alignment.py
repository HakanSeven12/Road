# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Alignment objects."""

import FreeCAD, Part

from .geo_object import GeoObject
from ..geometry.alignment import Alignment as AlignmentModel
from ..geometry.line import Line
from ..geometry.curve import Curve
from ..geometry.spiral import Spiral
from ..utils.support import  zero_referance


class Alignment(GeoObject):
    """This class is about Alignment Object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = "Road::Alignment"

        obj.addProperty(
            "App::PropertyEnumeration", "Status", "Base", "Alignment status"
        ).Status = ["existing", "proposed", "abandoned", "destroyed"]

        obj.addProperty(
            "App::PropertyString", "Description", "Base",
            "Alignment description").Description = ""

        obj.addProperty(
            "App::PropertyLength", "StartStation", "Station",
            "Starting station of the alignment").StartStation = 0.0

        obj.addProperty(
            "App::PropertyLength", "EndStation", "Station",
            "Ending station of the alignment").EndStation = 0.0

        obj.addProperty(
            "App::PropertyLength", "Length", "Station",
            "Alignment length", 1).Length = 0.0

        obj.addProperty(
            "App::PropertyVectorList", "PIs", "Geometry",
            "Points of Intersection (PIs) as a list of vectors").PIs = []

        obj.addProperty(
            "App::PropertyPythonObject", "Model", "Geometry",
            "Alignment horizontal geometry model").Model = None

        obj.addProperty(
            "App::PropertyLink", "OffsetAlignment", "Offset",
            "Parent alignment which offset model is referenced").OffsetAlignment

        obj.addProperty(
            "App::PropertyFloat", "OffsetLength", "Offset",
            "Offset length").OffsetLength = 0

        obj.Proxy = self

    def execute(self, obj):
        """Update Object when doing a recomputation."""
        if not obj.Model:
            return
        
        # Generate shape from alignment model
        obj.Shape = self._generate_shape_from_model(obj.Model)
        
        # Extract PI points from alignment
        #obj.PIs = self._get_pi_points(obj.Model)

        # Update geolocation based on alignment start point
        start = obj.Model.start_point
        if start:
            vec = FreeCAD.Vector(start[1], start[0]).multiply(1000)
            if obj.Geolocation.Base != vec:
                obj.Geolocation.Base = vec

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        super().onChanged(obj, prop)

        if prop == "Model":
            if not obj.Model:
                return
            
            # Update properties from model
            obj.Length = obj.Model.get_length() * 1000  # Convert m to mm
            obj.StartStation = obj.Model.get_sta_start() * 1000  # Convert m to mm
            obj.EndStation = obj.Model.get_sta_end() * 1000  # Convert m to mm
            
            # Update description if available
            if obj.Model.description:
                obj.Description = obj.Model.description
            
            # Status is not stored in new alignment model, keep existing or default
            if not obj.Status:
                obj.Status = "existing"

        elif prop == "OffsetLength":
            if obj.getPropertyByName(prop):
                self.onChanged(obj, "OffsetAlignment")

        elif prop == "OffsetAlignment":
            parent = obj.getPropertyByName(prop)
            if parent and parent.Model:
                self.generate_offset_alignment(obj, parent)

    def _generate_shape_from_model(self, model: AlignmentModel) -> Part.Shape:
        """
        Generate FreeCAD shape from alignment model.
        
        Args:
            model: AlignmentModel instance
            
        Returns:
            Part.Shape representing the alignment
        """
        elements = model.get_elements()
        
        # Create wire from points
        if not elements:
            return Part.Shape()
        
        edges = []
        for el in elements:
            _pts = el.get_key_points_transformed()
            points = [FreeCAD.Vector(*pt).multiply(1000) for pt in _pts]

            if isinstance(el, Line):
                edges.append(Part.LineSegment(*points).toShape())

            elif isinstance(el, Curve):
                edges.append(Part.Arc(*points).toShape())

            elif isinstance(el, Spiral):
                bspline = Part.BSplineCurve()
                bspline.interpolate(points)
                edges.append(bspline.toShape())

        if edges:
            try:
                return Part.Wire(edges)
            except:
                return Part.Compound(edges)
        else:
            return Part.Shape()

    def _get_pi_points(self, model: AlignmentModel) -> list:
        """
        Extract PI points from alignment model.
        
        Args:
            model: AlignmentModel instance
            
        Returns:
            List of (x, y) tuples representing PI points
        """
        pi_points = []
        pi_points.append(model.get_start_point())
        
        # Get alignment PI points
        align_pis = model.get_align_pis()
        for pi in align_pis:
            if pi['point']:
                # Convert from meters to mm for FreeCAD
                pi_points.append(pi)
        
        # Also collect PI points from curve and spiral elements
        for element in model.get_elements():
            element_dict = element.to_dict()
            
            # Get PI point from curves and spirals
            if 'PI' in element_dict and element_dict['PI']:
                pi = element_dict['PI']
                # Convert from meters to mm
                pi_points.append(pi)
            
            # For curves with multiple PI points (large arcs)
            if 'pi_points' in element_dict and element_dict['pi_points']:
                for pi in element_dict['pi_points']:
                    # Convert from meters to mm
                    pi_points.append(pi)

        pi_points.append(model.get_end_point())
        
        return [FreeCAD.Vector(*pt).multiply(1000) for pt in pi_points]

    def generate_offset_alignment(self, obj, parent, offset):
        """
        Advanced method to create offset alignment preserving geometry types.
        This method attempts to offset curves and spirals properly.
        
        Args:
            obj: Current alignment object
            parent: Parent alignment object
            offset: Offset distance in meters
        """
        elements = []
        parent_elements = parent.Model.get_elements()
        
        for element in parent_elements:
            element_dict = element.to_dict()
            element_type = element_dict['Type']
            
            if element_type == 'Line':
                # Offset line by moving parallel
                start = element.get_start_point()
                end = element.get_end_point()
                
                # Get orthogonal vector at start
                _, ortho = element.get_orthogonal(0, 'left' if offset > 0 else 'right')
                
                # Offset start and end points
                offset_start = (
                    start[0] + abs(offset) * ortho[0],
                    start[1] + abs(offset) * ortho[1]
                )
                offset_end = (
                    end[0] + abs(offset) * ortho[0],
                    end[1] + abs(offset) * ortho[1]
                )
                
                new_element = {
                    'Type': 'Line',
                    'Start': offset_start,
                    'End': offset_end,
                    'staStart': element_dict['staStart']
                }
                elements.append(new_element)
                
            elif element_type == 'Curve':
                # Offset curve by adjusting radius
                radius = element_dict['radius']
                center = element_dict['center']
                
                # Determine if we're offsetting inward or outward
                # This depends on curve rotation and offset direction
                rotation = element_dict['rot']
                
                if (rotation == 'ccw' and offset > 0) or (rotation == 'cw' and offset < 0):
                    # Offset increases radius (away from center)
                    new_radius = radius + abs(offset)
                else:
                    # Offset decreases radius (toward center)
                    new_radius = radius - abs(offset)
                
                if new_radius <= 0:
                    print(f"Warning: Offset curve radius becomes negative, skipping element")
                    continue
                
                # Calculate new start and end points
                # The center remains the same, but points move along radial directions
                start = element.get_start_point()
                end = element.get_end_point()
                
                # Calculate new start point
                start_angle = element_dict['dirStart']
                if (rotation == 'ccw' and offset > 0) or (rotation == 'cw' and offset < 0):
                    start_offset = abs(offset)
                else:
                    start_offset = -abs(offset)
                
                new_start = (
                    center[0] + new_radius * (start[0] - center[0]) / radius,
                    center[1] + new_radius * (start[1] - center[1]) / radius
                )
                
                new_end = (
                    center[0] + new_radius * (end[0] - center[0]) / radius,
                    center[1] + new_radius * (end[1] - center[1]) / radius
                )
                
                new_element = {
                    'Type': 'Curve',
                    'Start': new_start,
                    'End': new_end,
                    'Center': center,
                    'Direction': element_dict.get('Direction', 1),
                    'staStart': element_dict['staStart']
                }
                elements.append(new_element)
                
            elif element_type == 'Spiral':
                # Spirals are more complex to offset
                # Simplified approach: generate offset points and create line segments
                spiral_length = element_dict['length']
                step = 1.0  # 1 meter
                
                for dist in range(0, int(spiral_length), int(step)):
                    point, ortho = element.get_orthogonal(
                        dist, 
                        'left' if offset > 0 else 'right'
                    )
                    
                    offset_point = (
                        point[0] + abs(offset) * ortho[0],
                        point[1] + abs(offset) * ortho[1]
                    )
                    
                    # Store offset point for line segment creation
                    if dist == 0:
                        prev_point = offset_point
                    else:
                        new_element = {
                            'Type': 'Line',
                            'Start': prev_point,
                            'End': offset_point,
                            'staStart': element_dict['staStart'] + dist - step
                        }
                        elements.append(new_element)
                        prev_point = offset_point
        
        # Create new alignment
        alignment_data = {
            'name': f"{parent.Model.name}_offset_{offset}",
            'desc': f"Advanced offset alignment from {parent.Model.name}",
            'staStart': parent.Model.get_sta_start(),
            'CoordGeom': elements
        }
        
        try:
            obj.Model = AlignmentModel(alignment_data)
        except Exception as e:
            print(f"Error creating advanced offset alignment: {str(e)}")
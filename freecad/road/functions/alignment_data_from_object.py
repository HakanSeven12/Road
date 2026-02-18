# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD, Part
from ..utils.get_group import create_project


def extract_alignment_data(obj, name, description, start_sta, reverse):
    """
    Extract alignment geometry data from FreeCAD object.
    Returns dictionary compatible with Alignment class initialization.
    """
    try:
        shape = obj.Shape.copy()
        shape.translate(create_project(obj.Placement.Base).Base)

        if not shape.Wires:
            FreeCAD.Console.PrintError("Selected object has no wires.\n")
            return None
        
        # Get ordered edges
        wire = shape.Wires[0]
        edges = wire.OrderedEdges

        if reverse:
            edges = list(reversed(edges))

        # Extract elements
        coord_geom = []
        current_station = start_sta

        for i, edge in enumerate(edges):
            element_data = edge_to_geometry(edge, current_station, i)
            if element_data:
                coord_geom.append(element_data)
                current_station += edge.Length * 0.001

        return {
            'name': name,
            'desc': description,
            'staStart': start_sta,
            'CoordGeom': coord_geom,
            'coordinateSystem': {
                'system_type': 'global'
            }
        }

    except Exception as e:
        FreeCAD.Console.PrintError(f"Error extracting alignment data: {str(e)}\n")
        return None

def edge_to_geometry(edge, station, index):
    """Convert FreeCAD edge to alignment geometry element dictionary."""
    try:
        curve = edge.Curve

        # Start and end points as FreeCAD Vectors
        start_point = edge.Vertexes[0].Point.multiply(0.001)
        end_point = edge.Vertexes[-1].Point.multiply(0.001)

        # Determine geometry type
        if isinstance(curve, Part.Line) or isinstance(curve, Part.LineSegment):
            return {
                'Type': 'Line',
                'name': f'Line_{index}',
                'staStart': station,
                'Start': (start_point.y, start_point.x),
                'End': (end_point.y, end_point.x)
            }
        elif isinstance(curve, Part.Circle):
            return curve_data(edge, station, start_point, end_point, index)

        elif isinstance(curve, (Part.BSplineCurve, Part.BezierCurve)):
            FreeCAD.Console.PrintWarning(f"Edge {index}: Complex curve approximated as line.\n")
            return {
                'Type': 'Line',
                'name': f'Line_{index}',
                'staStart': station,
                'Start': (start_point.y, start_point.x),
                'End': (end_point.y, end_point.x)
            }

        else:
            FreeCAD.Console.PrintWarning(
                f"Edge {index}: Unknown curve type {type(curve).__name__}.\n"
            )
            return None

    except Exception as e:
        FreeCAD.Console.PrintError(f"Error converting edge {index}: {str(e)}\n")
        return None

def curve_data(edge, station, start_point, end_point, index):
    """Create Curve geometry dictionary using FreeCAD Vectors"""
    curve = edge.Curve

    # Center as FreeCAD Vector
    center = FreeCAD.Vector(curve.Center.x, curve.Center.y, 0).multiply(0.001)

    # Get a point slightly after start to determine actual travel direction
    u_start = edge.FirstParameter
    u_end = edge.LastParameter
    u_mid = u_start + (u_end - u_start) * 0.01  # 1% along the curve
    
    mid_point_3d = edge.valueAt(u_mid)
    mid_point = FreeCAD.Vector(mid_point_3d.x, mid_point_3d.y, 0).multiply(0.001)

    # Convert to swapped coordinate system (y, x) for rotation calculation
    # In the alignment system: first coord is FreeCAD's Y, second is FreeCAD's X
    start_align = FreeCAD.Vector(start_point.y, start_point.x, 0)
    mid_align = FreeCAD.Vector(mid_point.y, mid_point.x, 0)
    end_align = FreeCAD.Vector(end_point.y, end_point.x, 0)
    center_align = FreeCAD.Vector(center.y, center.x, 0)

    # Calculate vectors from center (not from start)
    vec_start = start_align.sub(center_align)
    vec_mid = mid_align.sub(center_align)
    
    # Cross product to determine rotation direction
    cross = vec_start.cross(vec_mid)
    
    # Positive Z means counter-clockwise in the alignment coordinate system
    rotation = 'ccw' if cross.z < 0 else 'cw'

    return {
        'Type': 'Curve',
        'name': f'Curve_{index}',
        'staStart': station,
        'rot': rotation,
        'Start': (start_point.y, start_point.x),
        'Center': (center.y, center.x),
        'End': (end_point.y, end_point.x)
    }
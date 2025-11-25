# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD, Part
from ..utils.get_group import georigin
import math


def extract_alignment_data(obj, name, description, start_sta, tolerance, reverse):
    """
    Extract alignment geometry data from FreeCAD object.
    Returns dictionary compatible with Alignment class initialization.
    """
    try:
        shape = obj.Shape.copy()
        shape.translate(georigin(obj.Placement.Base).Base)

        # Get ordered edges
        if len(shape.Wires) > 0:
            wire = shape.Wires[0]
            edges = wire.OrderedEdges
        else:
            edges = order_edges(shape.Edges, tolerance)

        if reverse:
            edges = list(reversed(edges))

        # Extract elements
        coord_geom = []
        current_station = start_sta

        for i, edge in enumerate(edges):
            element_data = edge_to_geometry(edge, current_station, i)
            if element_data:
                coord_geom.append(element_data)
                current_station += element_data.get('length', 0)

        if len(coord_geom) == 0:
            raise ValueError("No valid geometry elements extracted")

        # Total length
        total_length = sum(elem.get('length', 0) for elem in coord_geom)

        # Start point
        if not reverse:
            start_vertex = edges[0].Vertexes[0]
        else:
            start_vertex = edges[0].Vertexes[-1]

        start_point = (start_vertex.Y/1000, start_vertex.X/1000)

        return {
            'name': name,
            'desc': description,
            'length': total_length,
            'staStart': start_sta,
            'start': start_point,
            'CoordGeom': coord_geom,
            'coordinateSystem': {
                'system_type': 'global'
            }
        }

    except Exception as e:
        FreeCAD.Console.PrintError(f"Error extracting alignment data: {str(e)}\n")
        return None


def order_edges(edges, tolerance):
    """Order disconnected edges into continuous path"""
    if len(edges) <= 1:
        return edges

    ordered = [edges[0]]
    remaining = list(edges[1:])

    while remaining:
        last_edge = ordered[-1]
        last_point = last_edge.Vertexes[-1].Point

        found = False
        for i, edge in enumerate(remaining):
            sp = edge.Vertexes[0].Point
            ep = edge.Vertexes[-1].Point

            if last_point.distanceToPoint(sp) < tolerance:
                ordered.append(edge)
                remaining.pop(i)
                found = True
                break
            elif last_point.distanceToPoint(ep) < tolerance:
                reversed_edge = edge.reversed()
                ordered.append(reversed_edge)
                remaining.pop(i)
                found = True
                break

        if not found:
            FreeCAD.Console.PrintWarning("Gap detected in geometry - continuing anyway.\n")
            ordered.extend(remaining)
            break

    return ordered


def edge_to_geometry(edge, station, index):
    """Convert FreeCAD edge to alignment geometry element dictionary."""
    try:
        curve = edge.Curve

        # Start and end points as FreeCAD Vectors
        start_point = FreeCAD.Vector(edge.Vertexes[0].X, edge.Vertexes[0].Y, 0).multiply(0.001)
        end_point = FreeCAD.Vector(edge.Vertexes[-1].X, edge.Vertexes[-1].Y, 0).multiply(0.001)

        # Determine geometry type
        if isinstance(curve, Part.Line) or isinstance(curve, Part.LineSegment):
            return line_data(edge, station, start_point, end_point, index)

        elif isinstance(curve, Part.Circle):
            return curve_data(edge, station, start_point, end_point, index)

        elif isinstance(curve, (Part.BSplineCurve, Part.BezierCurve)):
            FreeCAD.Console.PrintWarning(f"Edge {index}: Complex curve approximated as line.\n")
            return line_data(edge, station, start_point, end_point, index)

        else:
            FreeCAD.Console.PrintWarning(
                f"Edge {index}: Unknown curve type {type(curve).__name__}.\n"
            )
            return None

    except Exception as e:
        FreeCAD.Console.PrintError(f"Error converting edge {index}: {str(e)}\n")
        return None


def line_data(edge, station, start_point, end_point, index):
    """Create Line geometry dictionary using FreeCAD Vectors"""
    length = edge.Length

    # Direction vector
    direction_vec = end_point.sub(start_point)
    direction = math.atan2(direction_vec.y, direction_vec.x)

    return {
        'Type': 'Line',
        'name': f'Line_{index}',
        'staStart': station,
        'length': length,
        'dir': direction,
        'Start': (start_point.y, start_point.x),
        'End': (end_point.y, end_point.x)
    }


def curve_data(edge, station, start_point, end_point, index):
    """Create Curve geometry dictionary using FreeCAD Vectors"""
    curve = edge.Curve

    # Center as FreeCAD Vector
    center = FreeCAD.Vector(curve.Center.x, curve.Center.y, 0).multiply(0.001)

    radius = curve.Radius
    length = edge.Length

    # Get a point slightly after start to determine actual travel direction
    u_start = edge.FirstParameter
    u_end = edge.LastParameter
    u_mid = u_start + (u_end - u_start) * 0.01  # 1% along the curve
    
    mid_point_3d = edge.valueAt(u_mid)
    mid_point = FreeCAD.Vector(mid_point_3d.x, mid_point_3d.y, 0)

    # Calculate rotation using cross product
    # Vectors from start to mid and start to end
    vec_to_mid = mid_point.sub(start_point)
    vec_to_end = end_point.sub(start_point)
    
    # Cross product (only Z component matters for 2D)
    cross = vec_to_mid.cross(vec_to_end)
    
    # Positive Z means counter-clockwise
    rotation = 'ccw' if cross.z > 0 else 'cw'

    # Vectors from center to start and end
    vec_start = start_point.sub(center)
    vec_end = end_point.sub(center)

    # Angles
    start_angle = math.atan2(vec_start.y, vec_start.x)
    end_angle = math.atan2(vec_end.y, vec_end.x)

    delta = end_angle - start_angle

    # Normalize delta based on rotation direction
    if rotation == 'ccw':
        if delta < 0:
            delta += 2 * math.pi
    else:  # cw
        if delta > 0:
            delta -= 2 * math.pi

    delta = abs(delta)

    # Tangent directions at start and end points
    if rotation == 'ccw':
        dir_start = start_angle + math.pi / 2
        dir_end = end_angle + math.pi / 2
    else:  # cw
        dir_start = start_angle - math.pi / 2
        dir_end = end_angle - math.pi / 2

    return {
        'Type': 'Curve',
        'name': f'Curve_{index}',
        'staStart': station,
        'length': length,
        'radius': radius,
        'delta': delta,
        'rot': rotation,
        'dirStart': dir_start,
        'dirEnd': dir_end,
        'Start': (start_point.y, start_point.x),
        'Center': (center.y, center.x),
        'End': (end_point.y, end_point.x)
    }
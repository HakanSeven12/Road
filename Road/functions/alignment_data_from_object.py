# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD, Part
from ..utils.get_group import georigin
import math

# =============================
#  Helper scaling function
# =============================

def scale2d(pt):
    """Scale 2D point by /1000"""
    return (pt[1] / 1000.0, pt[0] / 1000.0)


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

        # Start point (scaled!)
        if not reverse:
            sp = (
                edges[0].Vertexes[0].X,
                edges[0].Vertexes[0].Y
            )
        else:
            sp = (
                edges[0].Vertexes[-1].X,
                edges[0].Vertexes[-1].Y
            )

        start_point = scale2d(sp)

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
        curve = edge.CCurve if hasattr(edge, "CCurve") else edge.Curve

        # Scaled start/end points
        start_point = scale2d((edge.Vertexes[0].X, edge.Vertexes[0].Y))
        end_point = scale2d((edge.Vertexes[-1].X, edge.Vertexes[-1].Y))

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
    """Create Line geometry dictionary (points already scaled)"""
    length = edge.Length

    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    direction = math.atan2(dy, dx)

    return {
        'Type': 'Line',
        'name': f'Line_{index}',
        'staStart': station,
        'length': length,
        'dir': direction,
        'Start': start_point,
        'End': end_point
    }


def curve_data(edge, station, start_point, end_point, index):
    """Create Curve geometry dictionary (points scaled)"""
    curve = edge.Curve

    # Center scaled
    center = scale2d((curve.Center.x, curve.Center.y))

    radius = curve.Radius
    length = edge.Length

    # Determine rotation direction
    start_vec = FreeCAD.Vector(
        start_point[0] - center[0],
        start_point[1] - center[1],
        0
    )
    end_vec = FreeCAD.Vector(
        end_point[0] - center[0],
        end_point[1] - center[1],
        0
    )

    cross = start_vec.cross(end_vec)
    rotation = 'ccw' if cross.z > 0 else 'cw'

    # Angles
    start_angle = math.atan2(start_point[1] - center[1], start_point[0] - center[0])
    end_angle = math.atan2(end_point[1] - center[1], end_point[0] - center[0])

    delta = end_angle - start_angle

    if rotation == 'ccw':
        if delta < 0:
            delta += 2 * math.pi
    else:
        if delta > 0:
            delta -= 2 * math.pi

    delta = abs(delta)

    # Directions
    dir_start = start_angle + (math.pi / 2 if rotation == 'ccw' else -math.pi / 2)
    dir_end = end_angle + (math.pi / 2 if rotation == 'ccw' else -math.pi / 2)

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
        'Start': start_point,
        'Center': center,
        'End': end_point
    }

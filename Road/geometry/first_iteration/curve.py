# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import Part
import math

# Function to create an arc
def makeCurve(start, end, radius, direction):
    # Calculate the midpoint and the distance between the points
    chord_middle = (start + end) / 2
    chord_length = start.distanceToPoint(end)

    # Calculate the distance from the midpoint to the center
    dist_to_center = math.sqrt(abs(radius**2 - (chord_length / 2)**2))

    # Calculate the vector perpendicular to the line segment between the points
    perp_vector = FreeCAD.Vector(0,0,1).cross(end.sub(start)).normalize().multiply(dist_to_center)

    # Select the correct center based on direction
    center = chord_middle.add(perp_vector) if direction > 0 else chord_middle.sub(perp_vector)
    middle = chord_middle.sub(center).normalize().multiply(radius).add(center)
    curve = Part.Arc(start, middle, end)

    return curve.toShape()
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Parabola generation tools."""

import FreeCAD
import Part
import numpy as np

def makeParabola(previous, pvi, next, length, num_points=50):
    """
    Compute a vertical parabolic curve between BVCS and EVCS.

    Args:
        previous: The point before the vertical curve.
        pvi: Point of Vertical Intersection (PVI).
        next: The point after the vertical curve.
        length: The total length of the parabolic curve.
        num_points: Number of points to generate along the curve.
    Returns:
        Part.Shape: The parabolic curve shape.
    """

    # Slopes
    slope_in = (pvi.y - previous.y) / (pvi.x - previous.x)
    slope_out = (next.y - pvi.y) / (next.x - pvi.x)

    start = FreeCAD.Vector(pvi.x - length / 2, 
                    pvi.y - slope_in * (length / 2))

    # Parabol formula
    x_values = np.linspace(0, length, num_points)
    points = [FreeCAD.Vector(start.x + x,
            start.y + slope_in * x + ((slope_out - slope_in) / (2 * length)) * x**2
            ) for x in x_values]

    parabola = Part.BSplineCurve(points)
    return parabola.toShape()
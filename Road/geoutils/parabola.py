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
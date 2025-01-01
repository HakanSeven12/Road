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

import FreeCAD as App
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
    perp_vector = App.Vector(0,0,1).cross(end.sub(start)).normalize().multiply(dist_to_center)

    # Select the correct center based on direction
    center = chord_middle.add(perp_vector) if direction > 0 else chord_middle.sub(perp_vector)
    middle = chord_middle.sub(center).normalize().multiply(radius).add(center)
    curve = Part.Arc(start, middle, end)

    return curve.toShape()
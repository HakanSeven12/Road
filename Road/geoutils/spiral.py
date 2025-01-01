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

"""Spiral generation tools."""

import math
import numpy as np
from scipy.special import fresnel
from scipy.optimize import fsolve

import FreeCAD as App
import Part

# Clothoid Spiral class
class ClothoidSpiral:
    def __init__(self, length, radius, direction, delta, num_points=100):
        self.length = length
        self.radius = radius
        self.direction = direction
        self.delta = delta
        self.num_points = num_points
        placement=App.Vector(0, 0, 0)
        angle=0

        self.points = []
        self.finish = []
        self.tangent = None

    def calculate_points(self):
        # Calculate Fresnel parameters
        A = math.sqrt(self.length * self.radius * math.pi)
        t_values = np.linspace(0, self.length / A, self.num_points)

        S, C = fresnel(t_values)

        # Calculate coordinates with the direction and scaling factor
        x_coords = A * C
        y_coords = A * S * self.direction
        self.finish = [x_coords[-1], y_coords[-1]]
        self.points = list(zip(x_coords, y_coords))

    def calculate_tangent_distance(self):
        x = abs(self.finish[0])
        y = abs(self.finish[1])
        theta = self.length / (2 * self.radius)
        center_x = x - self.radius * math.sin(theta)
        center_y = y + self.radius * math.cos(theta)
        self.tangent = center_y * math.tan(self.delta / 2) + center_x

    def toShape(self, placement=App.Vector(0, 0, 0), angle=0, type="in"):
        if not self.points:
            return None

        # Create a rotation object for the given angle around the Z-axis
        rotation = App.Rotation(App.Vector(0, 0, 1), Radian=angle)

        # Apply translation and rotation to the points
        points = [placement + rotation.multVec(App.Vector(x, y, 0))
                  for x, y in self.points]
        if type != "in": 
            points.reverse()

        bspline = Part.BSplineCurve()
        bspline.interpolate(points)
        return bspline.toShape()

# Function to create a Clothoid spiral
def makeSpiral(length, radius, direction, delta):
    spiral = ClothoidSpiral(length, radius, direction, delta)
    spiral.calculate_points()
    spiral.calculate_tangent_distance()
    return spiral
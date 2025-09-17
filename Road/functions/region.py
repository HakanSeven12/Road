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

"""Provides functions to object and viewprovider classes of Region."""

import FreeCAD
import Part
import copy

from ..functions.alignment import transformation


def get_lines(alignment, increment, offset_left, offset_right):
    """Create guide lines at given increment along the alignment."""
    lines = []
    stations = transformation(alignment, increment)
    for station, transform in stations.items():
        point = transform["Location"]
        normal = transform["Normal"]

        left_side = point + normal * offset_left
        right_side = point - normal * offset_right
        lines.append(Part.makePolygon([left_side, point, right_side]))

    return Part.makeCompound(lines)
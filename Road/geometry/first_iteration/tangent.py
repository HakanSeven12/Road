# SPDX-License-Identifier: LGPL-2.1-or-later

import Part

# Function to create a tangent line
def makeTangent(start, end):
    tangent = Part.LineSegment(start, end)
    return tangent.toShape()
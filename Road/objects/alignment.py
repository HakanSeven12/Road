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

"""Provides the object code for Alignment objects."""

import FreeCAD
import Part

import copy

from ..functions import alignment
from ..functions.offset import offsetWire


class Alignment:
    """This class is about Alignment Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::Alignment"

        # Metadata properties.
        obj.addProperty(
            "App::PropertyString", "Description", "Base",
            "Alignment description").Description = ""

        obj.addProperty(
            "App::PropertyEnumeration", "Style", "Base",
            "Alignment type").Style = ["Basic", "Existing"]

        obj.addProperty(
            "App::PropertyVectorList", "Reference", "Station",
            "Points of reference").Reference = []

        obj.addProperty(
            "App::PropertyLength", "StartStation", "Station",
            "Starting station of the alignment").StartStation = 0.0

        obj.addProperty(
            "App::PropertyLength", "EndStation", "Station",
            "Starting station of the alignment").EndStation = 0.0

        obj.addProperty(
            "App::PropertyLength", "Length", "Base",
            "Alignment length", 1).Length = 0.0

        obj.addProperty(
            "App::PropertyPythonObject", "ModelKeeper", "Base",
            "Alignment horizontal geometry model").ModelKeeper = {}

        obj.addProperty(
            "App::PropertyLink", "OffsetAlignment", "Offset",
            "Parent alignment which offset model is referenced").OffsetAlignment

        obj.addProperty(
            "App::PropertyFloat", "OffsetLength", "Offset",
            "Offset length").OffsetLength = 0

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyVectorList", "PIs", "Base",
            "Points of Intersection (PIs) as a list of vectors").PIs = []

        obj.Proxy = self

    def execute(self, obj):
        """Do something when doing a recomputation."""
        if obj.OffsetAlignment: self.onChanged(obj, "OffsetAlignment")

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        if prop == "ModelKeeper":
            alignment_model = obj.getPropertyByName(prop)
            obj.PIs, obj.Shape = alignment.get_geometry(alignment_model)
            obj.EndStation = sum([sub.Length for sub in obj.Shape.SubShapes])
            obj.Length = sum([sub.Length for sub in obj.Shape.SubShapes])

        if prop == "OffsetAlignment":
            parent = obj.getPropertyByName(prop)
            if parent:
                wire = Part.makePolygon(parent.PIs)
                offset = obj.OffsetLength
                line = parent.PIs[0].sub(parent.PIs[1])
                normal = FreeCAD.Vector(-line.y, line.x, line.z)
                pi_offset = offsetWire(wire, normal.normalize().multiply(offset))
                points = [vertex.Point for vertex in pi_offset.Vertexes]

                model = copy.deepcopy(parent.ModelKeeper)
                for i, (pi, values) in enumerate(model.items()):
                    values['X'] = points[i].x/1000
                    values['Y'] = points[i].y/1000
                    if 0 < i < len(points)-1:
                        v1 = points[i].sub(points[i-1])
                        v2 = points[i+1].sub(points[i])
                        crossz = v1.cross(v2).z

                        if 'Radius' in values: 
                            R=float(values['Radius'])
                            factor = 1 
                            if (crossz > 0 and offset < 0) or (crossz < 0 and offset > 0):
                                factor = -1
                            values['Radius'] = float(values['Radius']) + factor * abs(offset) / 1000
                            if 'Spiral Length In' in values: values['Spiral Length In'] = float(values['Spiral Length In']) * ( 1 + factor * ((abs(offset) / 1000) / (2 * R)))
                            if 'Spiral Length Out' in values: values['Spiral Length Out'] = float(values['Spiral Length Out']) * ( 1 + factor * ((abs(offset) / 1000) / (2 * R)))

                obj.ModelKeeper = model

        if prop == "OffsetLength":
            if obj.getPropertyByName(prop): self.onChanged(obj, "OffsetAlignment")
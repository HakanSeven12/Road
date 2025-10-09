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

from ..functions.alignment.alignment_model import AlignmentModel
from ..functions.offset import offsetWire


class Alignment:
    """This class is about Alignment Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::Alignment"

        obj.addProperty(
            "App::PropertyPlacement", "Placement", "Base",
            "Placement").Placement = FreeCAD.Placement()

        obj.addProperty(
            "Part::PropertyPartShape", "Shape", "Base",
            "Alignment Shape").Shape = Part.Shape()

        obj.addProperty(
            "App::PropertyEnumeration", "Status", "Base", "Alignment status"
        ).Status = ["existing", "proposed", "abandoned", "destroyed"]

        obj.addProperty(
            "App::PropertyString", "Description", "Base",
            "Alignment description").Description = ""

        obj.addProperty(
            "App::PropertyLength", "StartStation", "Station",
            "Starting station of the alignment").StartStation = 0.0

        obj.addProperty(
            "App::PropertyLength", "EndStation", "Station",
            "Starting station of the alignment").EndStation = 0.0

        obj.addProperty(
            "App::PropertyLength", "Length", "Station",
            "Alignment length", 1).Length = 0.0

        obj.addProperty(
            "App::PropertyVectorList", "PIs", "Geometry",
            "Points of Intersection (PIs) as a list of vectors").PIs = []

        obj.addProperty(
            "App::PropertyPythonObject", "Meta", "Geometry",
            "Alignment horizontal geometry model").Meta = {}

        obj.addProperty(
            "App::PropertyPythonObject", "Station", "Geometry",
            "Alignment horizontal geometry model").Station = {}

        obj.addProperty(
            "App::PropertyPythonObject", "Geometry", "Geometry",
            "Alignment horizontal geometry model").Geometry = {}

        obj.addProperty(
            "App::PropertyLink", "OffsetAlignment", "Offset",
            "Parent alignment which offset model is referenced").OffsetAlignment

        obj.addProperty(
            "App::PropertyFloat", "OffsetLength", "Offset",
            "Offset length").OffsetLength = 0

        subdivision_desc = """
            Method of Curve Subdivision\n\n
            Tolerance - ensure error between segments and curve is (n)\n
            Interval - Subdivide curve into segments of fixed length\n
            Segment - Subdivide curve into equal-length segments
            """

        obj.addProperty(
            'App::PropertyEnumeration', 'Method', 'Segment', subdivision_desc
        ).Method = ['Tolerance', 'Interval', 'Segment']

        obj.addProperty(
            "App::PropertyFloat", "Seg_Value", "Segment",
            "Set the curve segments to control accuracy").Seg_Value = 10

        obj.Proxy = self
        self.Object = obj
        self.model = None

    def execute(self, obj):
        """Update Object when doing a recomputation."""
        if hasattr(self, "model"):
            if self.model: obj.Shape = self.model.get_shape()

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        if prop == "Geometry":
            geometry = obj.getPropertyByName(prop)
            start = geometry[0].get('Start')
            if start:
                vec = FreeCAD.Vector(start)
                placement = FreeCAD.Placement()
                placement.move(vec)
                obj.Placement = placement

        if prop == "Meta":
            meta = obj.getPropertyByName(prop)

            obj.StartStation = meta.get("StartStation", 0) * 1000
            obj.Length = meta.get("Length", 0)
            obj.EndStation = meta.get("EndStation", 0) * 1000

            obj.Description = meta.get("Description") if meta.get("Description") else ""
            obj.Status = meta.get("Status") if meta.get("Status") else "existing"

        elif prop == "OffsetLength":
            if obj.getPropertyByName(prop): self.onChanged(obj, "OffsetAlignment")

        elif prop == "OffsetAlignment":
            parent = obj.getPropertyByName(prop)
            if parent:
                wire = Part.makePolygon(parent.PIs)
                offset = obj.OffsetLength
                line = parent.PIs[0].sub(parent.PIs[1])
                normal = FreeCAD.Vector(-line.y, line.x, line.z)
                pi_offset = offsetWire(wire, normal.normalize().multiply(offset))
                points = [vertex.Point for vertex in pi_offset.Vertexes]

                model = copy.deepcopy(parent.Model)
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

                obj.Model = model

    def onDocumentRestored(self, obj):
        """Restore Object references on reload."""
        self.model = AlignmentModel(obj.Meta, obj.Station, obj.Geometry)
        if self.model.errors:
            for _err in self.model.errors:
                print('Error in alignment {0}: {1}'.format(obj.Label, _err))
            self.model.errors.clear()

        meta = self.model.meta
        if meta.get('Description'):
            obj.Description = meta.get('Description')

        if meta.get('Length'):
            obj.Length = meta.get('Length')

        if meta.get('Status'):
            obj.Status = meta.get('Status')

        if meta.get('StartStation'):
            obj.StartStation = str(meta.get('StartStation'))

        if meta.get('EndStation'):
            obj.EndStation = str(meta.get('EndStation'))

    def dumps(self):
        """Called during document saving."""
        self.model = None
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Alignment objects."""

import FreeCAD
import Part

import copy

from.geo_object import GeoObject
from ..functions.alignment.alignment_model import AlignmentModel
from ..functions.offset import offsetWire


class Alignment(GeoObject):
    """This class is about Alignment Object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = "Road::Alignment"

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
            "App::PropertyPythonObject", "Model", "Geometry",
            "Alignment horizontal geometry model").Model = None

        obj.addProperty(
            "App::PropertyLink", "OffsetAlignment", "Offset",
            "Parent alignment which offset model is referenced").OffsetAlignment

        obj.addProperty(
            "App::PropertyFloat", "OffsetLength", "Offset",
            "Offset length").OffsetLength = 0

        obj.Proxy = self

    def execute(self, obj):
        """Update Object when doing a recomputation."""
        if not obj.Model: return
        obj.Shape = obj.Model.get_shape()
        pis = obj.Model.get_pi_coords()
        obj.PIs = [FreeCAD.Vector(pi) for pi in pis if pi]

        start = obj.Model.meta.get('Start')
        if start:
            vec = FreeCAD.Vector(start)
            if obj.Geolocation.Base == vec: return
            obj.Geolocation.Base = vec

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        super().onChanged(obj, prop)

        if prop == "Model":
            if obj.Model.errors:
                for _err in obj.Model.errors:
                    print('Error in alignment {0}: {1}'.format(obj.Label, _err))
                obj.Model.errors.clear()

            meta = obj.Model.meta
            obj.Length = meta.get("Length", 0)
            obj.StartStation = meta.get("StartStation", 0) * 1000
            obj.EndStation = meta.get("EndStation", 0) * 1000
            obj.Status = meta.get("Status") if meta.get("Status") else "existing"
            obj.Description = meta.get("Description") if meta.get("Description") else ""


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

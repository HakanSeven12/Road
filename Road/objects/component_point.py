# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Component Point objects."""
import FreeCAD
import Part

import math
from .geo_object import GeoObject


class ComponentPoint(GeoObject):
    """This class is about Component Point Object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = "Road::ComponentPoint"

        obj.addProperty(
            "App::PropertyEnumeration", "Type", "Base",
            "Type of transformation that will be applied to the point").Type = [
                "Delta X and Delta Y",
                "Delta X and Angle",
                "Delta Y and Angle",
                "Delta X and Slope",
                "Delta Y and Slope",
                "Delta X on Terrain",
                "Slope to Terrain",
                "Distance and Angle"]

        obj.addProperty(
            "App::PropertyLink", "Start", "Geometry",
            "Origin point.")

        obj.addProperty(
            "App::PropertyBool", "Reverse", "Geometry",
            "Reverse vector direction.")

        obj.addProperty(
            "App::PropertyFloat", "Distance", "Geometry",
            "Distance from start point.").Distance = 0

        obj.addProperty(
            "App::PropertyFloat", "DeltaX", "Geometry",
            "Displacement along the X axis.").DeltaX = 0

        obj.addProperty(
            "App::PropertyFloat", "DeltaY", "Geometry",
            "Displacement along the Y axis.").DeltaY = 0

        obj.addProperty(
            "App::PropertyAngle", "Angle", "Geometry",
            "The angle with the X axis.").Angle = 0

        obj.addProperty(
            "App::PropertyFloat", "Slope", "Geometry",
            "The slope with the X axis.").Slope = 0

        obj.addProperty(
            "App::PropertyLink", "Terrain", "Geometry",
            "Target Terrain.")

        obj.addProperty(
            "App::PropertyLink", "Alignment", "Geometry",
            "Target Alignment.")

        obj.Proxy = self
        obj.Shape = Part.makeCircle(100)
        self.onChanged(obj, "Type")

    def execute(self, obj):
        """Do something when doing a recomputation."""
        if obj.Type == "Delta X and Delta Y":
            displacement = FreeCAD.Vector(obj.DeltaX*1000, obj.DeltaY*1000)
    
        elif obj.Type == "Delta X and Angle":
            angle = obj.Angle % 360
            dir = -1 if 90 < angle < 270 else 1
            if angle in [90, 270]: dir = 0
            dy = obj.DeltaX * math.tan(math.radians(angle))
            displacement = FreeCAD.Vector(dir*obj.DeltaX * 1000, dir*dy * 1000)

        elif obj.Type == "Delta Y and Angle":
            angle = obj.Angle % 360
            dir = 1 if 0 < angle < 180 else -1
            if angle in [0, 180]: dir = 0
            dx = obj.DeltaY / math.tan(math.radians(angle)) if angle else 0
            displacement = FreeCAD.Vector(dir * dx * 1000, dir * obj.DeltaY * 1000)

        elif obj.Type == "Delta X and Slope":
            dy = obj.DeltaX * (obj.Slope / 100)
            displacement = FreeCAD.Vector(obj.DeltaX*1000, dy*1000)

        elif obj.Type == "Delta Y and Slope":
            dx = obj.DeltaY / (obj.Slope / 100)
            displacement = FreeCAD.Vector(dx*1000, obj.DeltaY*1000)

        elif obj.Type == "Delta X on Terrain":pass
        elif obj.Type == "Slope to Terrain":pass

        elif obj.Type == "Distance and Angle":
            rad = math.radians(obj.Angle)
            dx = obj.Distance * math.cos(rad)
            dy = obj.Distance * math.sin(rad)
            displacement = FreeCAD.Vector(dx*1000, dy*1000)

        if obj.Reverse: displacement = displacement.negative()

        component = obj.getParentGroup()
        structure = component.getParentGroup()
        placement = structure.Placement.copy()
        
        side = -1 if component.Side == "Left" else 1
        displacement.x *= side
        placement.move(displacement)
        obj.Placement = placement

    def onChanged(self, obj, prop):
        super().onChanged(obj, prop)

        if prop == "Type":
            type = obj.getPropertyByName(prop)
            
            if type == "Delta X and Delta Y":
                visible =["DeltaX", "DeltaY"]
                
            elif type == "Delta X and Angle":
                visible =["DeltaX", "Angle"]
                
            elif type == "Delta Y and Angle":
                visible =["DeltaY", "Angle"]
                
            elif type == "Delta X and Slope":
                visible =["DeltaX", "Slope"]
                
            elif type == "Delta Y and Slope":
                visible =["DeltaY", "Slope"]
                
            elif type == "Delta X on Terrain":
                visible =["DeltaX", "Terrain"]
                
            elif type == "Slope to Terrain":
                visible =["Slope", "Terrain"]
                
            elif type == "Distance and Angle":
                visible =["Distance", "Angle"]
                
            untouch =["Reverse", "Start", "Type"]

            for property in obj.PropertiesList:
                if obj.getGroupOfProperty(property) == "Geometry":
                    if property in visible or property in untouch:
                        obj.setEditorMode(property, 0)
                    else:
                        obj.setEditorMode(property, 2)
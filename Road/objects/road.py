# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Road objects."""

import FreeCAD
import Part
import math
from .geo_object import GeoObject


class Road(GeoObject):
    """This class is about Road object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)
        self.Type = "Road::Road"

        obj.addProperty(
            "App::PropertyLink", "Alignment", "Model",
            "Base line Alignment").Alignment = None

        obj.addProperty(
            "App::PropertyString", "Profile", "Model",
            "Elevation profile").Profile = ''

        obj.addProperty(
            "App::PropertyLink", "Structure", "Model",
            "Road structure").Structure = None

        obj.Proxy = self
            
    def execute(self, obj):
        """Do something when doing a recomputation."""
        com_list = []
        for component in obj.Structure.Group:
            for part in component.Group:
                if part.Proxy.Type == "Road::ComponentPoint": continue
                part_copy = part.Shape.copy()
                part_copy.Placement.move(obj.Structure.Placement.Base.negative())
                com_list.append(part_copy)

        sec_list = []
        base_shp = Part.makeCompound(com_list)
        stations = obj.Alignment.Model.generate_stations()

        for sta in stations:
            try:
                # Get the 3D position and the orthogonal (normal) vector from alignment
                point = obj.Alignment.Model.get_3d_point_at_station(obj.Profile, sta)
                p, normal_vec = obj.Alignment.Model.get_orthogonal_at_station(sta)
                
                # normal_vec is (x, y), we need it in 3D
                norm = FreeCAD.Vector(normal_vec[0], normal_vec[1], 0)
                # Tangent vector is perpendicular to the normal in 2D
                tangent = FreeCAD.Vector(-normal_vec[1], normal_vec[0], 0)
                # Vertical axis
                up = FreeCAD.Vector(0, 0, 1)

                # Create a rotation matrix where:
                # X-axis of cross-section follows the Normal (sideways)
                # Y-axis of cross-section follows the Up vector (elevation)
                # Z-axis of cross-section follows the Tangent (forward)
                matrix = FreeCAD.Matrix(
                    norm.x, tangent.x, up.x, 0,
                    norm.y, tangent.y, up.y, 0,
                    norm.z, tangent.z, up.z, 0,
                    0, 0, 0, 1
                )

                new_placement = FreeCAD.Placement(matrix)
                # FreeCAD uses mm, ensure scale is consistent with your data
                new_placement.Base = FreeCAD.Vector(*point).multiply(1000)

                section = base_shp.copy()
                section.Placement = new_placement
                sec_list.append(section)
            except: 
                continue
        
        shp_list = []
        for i in range(len(base_shp.Edges)):
            l = [sec.Edges[i] for sec in sec_list]
            shp = Part.makeLoft(l)
            shp_list.append(shp)
        
        obj.Shape = Part.makeCompound(shp_list)

    def onChanged(self, obj, prop):
        """Update Object when a property changed."""
        super().onChanged(obj, prop)
        
        if prop == "Alignment":
            alignment = obj.getPropertyByName(prop)
            obj.Placement = alignment.Placement if alignment else FreeCAD.Placement()
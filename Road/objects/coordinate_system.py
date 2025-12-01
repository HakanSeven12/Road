# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Geo Origin objects."""

import FreeCAD
import FreeCADGui
from ..variables import zone_list
from .group import Group
from ..guitools.widgets import GeoWidget
from ..utils.coordinate_system import CoordinateSystem as Model


class GeoOrigin(Group):
    """This class is about Point Group Object data features."""

    def __init__(self, obj, type):
        """Set data properties."""
        super().__init__(obj, type)

        obj.addProperty(
            "App::PropertyEnumeration", "UtmZone", "Base",
            "UTM zone").UtmZone = zone_list

        obj.addProperty(
            "App::PropertyVector", "Base", "Base",
            "Base point.").Base
        
        # Add coordinate system properties
        obj.addProperty(
            "App::PropertyString", "EpsgCode", "Coordinate System",
            "EPSG code of the coordinate system").EpsgCode = ""
        
        obj.addProperty(
            "App::PropertyString", "Name", "Coordinate System",
            "Name of the coordinate system").Name = ""
        
        obj.addProperty(
            "App::PropertyString", "HorizontalDatum", "Coordinate System",
            "Horizontal datum").HorizontalDatum = ""
        
        obj.addProperty(
            "App::PropertyString", "VerticalDatum", "Coordinate System",
            "Vertical datum").VerticalDatum = ""
        
        obj.addProperty(
            "App::PropertyBool", "IsGeographic", "Coordinate System",
            "True if coordinate system is geographic (lat/lon)").IsGeographic = False
        
        obj.addProperty(
            "App::PropertyBool", "IsProjected", "Coordinate System",
            "True if coordinate system is projected").IsProjected = False
        
        obj.addProperty(
            "App::PropertyPythonObject", "Model", "Internal",
            "Coordinate system object for transformations").Model = Model()

    def execute(self, obj):
        """Update Object when doing a recomputation."""
        mw = FreeCADGui.getMainWindow()
        statusbar = mw.statusBar()
        
        # Check all widgets in statusbar
        for widget in statusbar.children():
            if isinstance(widget, GeoWidget):
                widget.show()
                return
        
        GeoWidget()
    
    def onChanged(self, obj, prop):
        """Handle property changes."""
        if prop == "EpsgCode" and obj.EpsgCode:
            # Update coordinate system when EPSG code changes
            try:
                coord_sys = Model()
                coord_sys.set_crs_from_epsg(obj.EpsgCode)
                
                # Update properties
                obj.Model = coord_sys
                obj.Name = coord_sys.get_name()
                obj.IsGeographic = coord_sys.is_geographic()
                obj.IsProjected = coord_sys.is_projected()
                
                FreeCAD.Console.PrintMessage(
                    f"Coordinate system set to: {coord_sys.get_name()} (EPSG:{obj.EpsgCode})\n"
                )
            except Exception as e:
                FreeCAD.Console.PrintError(
                    f"Failed to set coordinate system from EPSG code: {str(e)}\n"
                )

    def get_coordinate_system(self):
        """
        Get the CoordinateSystem object.
        
        Returns:
            CoordinateSystem object or None
        """
        obj = self.Object
        return obj.Model if hasattr(obj, 'Model') else None

    def transform_to_local(self, x, y, z=None):
        """
        Transform coordinates from coordinate system to local FreeCAD coordinates.
        
        Args:
            x: X coordinate (easting or longitude)
            y: Y coordinate (northing or latitude)
            z: Z coordinate (elevation), optional
        
        Returns:
            Transformed coordinates as tuple (x, y) or (x, y, z)
        """
        obj = self.Object
        coord_sys = self.get_coordinate_system()
        
        if coord_sys and coord_sys.is_valid():
            # Apply base point offset
            base = obj.Base
            if z is not None:
                return (x - base.x, y - base.y, z - base.z)
            else:
                return (x - base.x, y - base.y)
        else:
            # No coordinate system, just apply offset
            base = obj.Base
            if z is not None:
                return (x - base.x, y - base.y, z - base.z)
            else:
                return (x - base.x, y - base.y)

    def transform_from_local(self, x, y, z=None):
        """
        Transform coordinates from local FreeCAD coordinates to coordinate system.
        
        Args:
            x: Local X coordinate
            y: Local Y coordinate
            z: Local Z coordinate, optional
        
        Returns:
            Transformed coordinates as tuple (x, y) or (x, y, z)
        """
        obj = self.Object
        base = obj.Base
        
        if z is not None:
            return (x + base.x, y + base.y, z + base.z)
        else:
            return (x + base.x, y + base.y)
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Geo Origin objects."""

import FreeCADGui
from ..variables import zone_list
from ..objects.group import Group
from ..guitools.widgets import GeoWidget



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


    def execute(self, obj):
        """Update Object when doing a recomputation. """
        mw = FreeCADGui.getMainWindow()
        statusbar = mw.statusBar()
        
        # Check all widgets in statusbar
        for widget in statusbar.children():
            if isinstance(widget, GeoWidget):
                widget.show()
                return
        
        GeoWidget()

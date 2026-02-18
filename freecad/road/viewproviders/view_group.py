# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Surface objects."""

import os
from .. import ICONPATH


class ViewProviderGroup:
    """
    This class is about Group view features.
    """

    def __init__(self, vobj, icon_name):
        """Set view properties."""

        self.icon = os.path.join(ICONPATH, f"{icon_name}.svg")
        self.Object = vobj.Object
        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        self.Object = vobj.Object
        return

    def getIcon(self):
        """Return object treeview icon."""
        return self.icon
    
    def claimChildren(self):
        """Provides object grouping."""
        return self.Object.Group

    def setEdit(self, vobj, mode=0):
        """Enable edit."""
        return True

    def unsetEdit(self, vobj, mode=0):
        """Disable edit."""
        return False

    def doubleClicked(self, vobj):
        """Detect double click."""
        pass

    def setupContextMenu(self, obj, menu):
        """Context menu construction."""
        pass

    def edit(self):
        """Edit callback."""
        pass

    def dumps(self):
        """Called during document saving"""
        return self.Icon

    def loads(self, state):
        """Called during document restore."""
        if state:
            self.Icon = state

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

"""Provides the viewprovider code for Surface objects."""


class ViewProviderGroup:
    """
    This class is about Group view features.
    """

    def __init__(self, vobj, icon):
        """Set view properties."""

        self.Object = vobj.Object
        vobj.Proxy = self
        self.Icon = icon

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        self.Object = vobj.Object
        return

    def getIcon(self):
        """Return object treeview icon."""
        return self.Icon

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

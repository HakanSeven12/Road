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

"""Provides functions to create Region objects."""

import FreeCAD

from ..objects.region import Region
from ..viewproviders.view_region import ViewProviderRegion
from . import make_sections, make_volumes, make_tables

def create(alignment, name="Region"):
    """Factory method for Region object."""

    for item in alignment.Group:
        if item.Proxy.Type == "Road::Regions":
            regions = item
            break

    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Region")
    regions.addObject(obj)

    Region(obj)
    ViewProviderRegion(obj.ViewObject)

    # Add Cross Sections group.
    sections = make_sections.create()
    obj.addObject(sections)

    # Add Volumes group.
    volumes = make_volumes.create()
    obj.addObject(volumes)

    # Add Tables group.
    tables = make_tables.create()
    obj.addObject(tables)

    obj.Label = name

    return obj
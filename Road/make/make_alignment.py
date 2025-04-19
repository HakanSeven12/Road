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

"""Provides functions to create Alignment objects."""

import FreeCAD

from . import make_regions, make_profiles
from ..utils import get_group
from ..objects.alignment import Alignment
from ..viewproviders.view_alignment import ViewProviderAlignment

def create(label="Alignment"):
    """Class construction method"""
    obj=FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Alignment")

    Alignment(obj)
    ViewProviderAlignment(obj.ViewObject)
    obj.Label = label

    profiles = make_profiles.create()
    regions = make_regions.create()
    sections = make_sections.create()
    volumes = make_volumes.create()
    tables = make_tables.create()

    obj.addObject(profiles)
    obj.addObject(regions)
    obj.addObject(sections)
    obj.addObject(volumes)
    obj.addObject(tables)

    group = get_group.get("Alignments")
    group.addObject(obj)

    return obj
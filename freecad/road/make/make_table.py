# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Table objects."""

import FreeCAD

from ..objects.table import Table
from ..viewproviders.view_table import ViewProviderTable

def create(tables, position, volume, name='Table'):
    obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Table")
    tables.addObject(obj)

    Table(obj)
    ViewProviderTable(obj.ViewObject)

    obj.Label = name
    obj.Position = position
    obj.VolumeAreas = volume

    return obj
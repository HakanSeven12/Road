# SPDX-License-Identifier: LGPL-2.1-or-later

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

    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Region")
    obj.addExtension("App::GroupExtensionPython")
    obj.ViewObject.addExtension("Gui::ViewProviderGroupExtensionPython")
    regions.addObject(obj)

    Region(obj)
    ViewProviderRegion(obj.ViewObject)

    sections = make_sections.create()
    volumes = make_volumes.create()
    tables = make_tables.create()

    obj.addObject(sections)
    obj.addObject(volumes)
    obj.addObject(tables)

    obj.Label = name

    return obj
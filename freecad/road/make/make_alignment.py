# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Alignment objects."""

import FreeCAD

from . import make_regions, make_profiles
from ..utils import get_group
from ..objects.alignment import Alignment
from ..viewproviders.view_alignment import ViewProviderAlignment

def create(label="Alignment"):
    """Class construction method"""
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Alignment")
    obj.addExtension("App::GroupExtensionPython")
    obj.ViewObject.addExtension("Gui::ViewProviderGroupExtensionPython")

    Alignment(obj)
    ViewProviderAlignment(obj.ViewObject)
    obj.Label = label

    profiles = make_profiles.create()
    regions = make_regions.create()

    obj.addObject(profiles)
    obj.addObject(regions)

    group = get_group.get("Alignments")
    group.addObject(obj)

    return obj
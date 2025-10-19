# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Profile Frame object."""

import FreeCAD

from ..objects.profile_frame import ProfileFrame
from ..viewproviders.view_profile_frame import ViewProviderProfileFrame

def create():
    """Factory method for Region group."""

    obj = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "ProfileFrame")

    ProfileFrame(obj)
    ViewProviderProfileFrame(obj.ViewObject)
    obj.Label = "Profile Frame"

    return obj
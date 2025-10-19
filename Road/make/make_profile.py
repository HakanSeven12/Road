# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Profile objects."""

import FreeCAD

from ..objects.profile import Profile
from ..viewproviders.view_profile import ViewProviderProfile

def create(name="Profile"):
    obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Profile")

    Profile(obj)
    ViewProviderProfile(obj.ViewObject)

    obj.Label = name

    return obj
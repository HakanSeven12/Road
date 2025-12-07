# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Profile Frame object."""

import FreeCAD

from ..objects.profile_new import Profile
from ..viewproviders.view_profile_new import ViewProviderProfile

def create():
    """Factory method for Region group."""

    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Profile")

    Profile(obj)
    ViewProviderProfile(obj.ViewObject)

    return obj
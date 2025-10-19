# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to get Sections object."""

import FreeCAD

from ..variables import icons_path
from ..objects.sections import Sections
from ..viewproviders.view_sections import ViewProviderSections


def create():
    obj=FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroupPython", "Sections")

    Sections(obj)
    ViewProviderSections(obj.ViewObject)

    obj.Label = "Sections"
    obj.ViewObject.Proxy.Icon = icons_path + '/CreateSections.svg'

    return obj
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Section objects."""

import FreeCAD

from ..objects.section import Section
from ..viewproviders.view_section import ViewProviderSection

def create():
    obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Section")

    Section(obj)
    ViewProviderSection(obj.ViewObject)

    return obj
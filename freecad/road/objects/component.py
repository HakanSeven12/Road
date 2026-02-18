# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Component objects."""


class Component:
    """This class is about Component Object data features."""

    def __init__(self, obj):
        """Set data properties."""

        self.Type = "Road::Component"

        obj.addProperty(
            "App::PropertyEnumeration", "Side", "Base",
            "Side of component").Side = ["Right", "Left"]

        obj.Proxy = self
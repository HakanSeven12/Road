# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Group objects."""

class Group:
    """This class is about Group object data features."""

    def __init__(self, obj, type):

        obj.Proxy = self
        self.Type = type
# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""Provides functions and lists of commands to set up Road menus and toolbars."""

def get_point_commands():
    """Return the point commands list."""
    return ["Cluster Create",
            "GeoPoint Create",
            "GeoPoint Import",
            "GeoPoint Export"]

def get_surface_commands():
    """Return the surface commands list."""
    return ["Create Terrain",
            "Terrain Data",
            "Terrain Edit",
            "Terrain Demolish"]

def get_alignment_commands():
    """Return the alignment commands list."""
    return ["Alignment Create",
            "Alignment Edit",
            "Alignment Offset",
            "Profile Frame Create",
            "Profile Create",
            "Profile Edit",
            "Profile Add"]

def get_road_commands():
    """Return the section commands list."""
    return ["Road Create",
            "Structure Create",
            "Component Add",
            "Component Point",
            "Component Line",
            "Component Shape"]

def get_section_commands():
    """Return the section commands list."""
    return ["Create Region",
            "Create Sections",
            "Compute Areas",
            "Create Table"]

def get_geoline_commands():
    """Return the geoline commands list."""
    return ["Create Pad"]

def get_io_commands():
    """Return the input/output commands list."""
    return []

def init_toolbar(workbench, toolbar, cmd_list):
    """Initialize a toolbar.

    Parameters
    ----------
    workbench: Gui.Workbench
        The workbench. The commands from cmd_list must be available.

    toolbar: string
        The name of the toolbar.

    cmd_list: list of strings or list of strings and tuples
        See f.e. the return value of get_draft_drawing_commands.
    """
    for cmd in cmd_list:
        if isinstance(cmd, tuple):
            if len(cmd) == 1:
                workbench.appendToolbar(toolbar, [cmd[0]])
        else:
            workbench.appendToolbar(toolbar, [cmd])


def init_menu(workbench, menu_list, cmd_list):
    """Initialize a menu.

    Parameters
    ----------
    workbench: Gui.Workbench
        The workbench. The commands from cmd_list must be available.

    menu_list: list of strings
        The main and optional submenu(s). The commands, and additional
        submenus (if any), are added to the last (sub)menu in the list.

    cmd_list: list of strings or list of strings and tuples
        See f.e. the return value of get_draft_drawing_commands.
    """
    for cmd in cmd_list:
        if isinstance(cmd, tuple):
            if len(cmd) == 2:
                workbench.appendMenu(menu_list + cmd[0], cmd[1])
        else:
            workbench.appendMenu(menu_list, [cmd])

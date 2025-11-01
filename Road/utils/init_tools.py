# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions and lists of commands to set up Road menus and toolbars."""

def get_io_commands():
    """Return the input/output commands list."""
    return ["GeoPoints Import",
            "GeoPoints Export",
            "LandXML Import"]

def get_point_commands():
    """Return the point commands list."""
    return ["GeoPoints Create",
            "GeoPoints Add"]

def get_surface_commands():
    """Return the surface commands list."""
    return ["Create Terrain",
            "Terrain Object",
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
    return ["Region Create",
            "Section Create",
            "Compute Areas",
            "Create Table"]

def get_geoline_commands():
    """Return the geoline commands list."""
    return ["Create Pad"]

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

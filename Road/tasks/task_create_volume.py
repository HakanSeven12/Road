# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for the Create Volume tool."""

import FreeCAD, FreeCADGui
from pivy import coin

from ..variables import ui_path
from .task_panel import TaskPanel
from ..utils import get_group
from ..make import make_volume


class TaskCreateVolume(TaskPanel):
    def __init__(self):
        # Set UI.
        self.form = FreeCADGui.PySideUic.loadUi(ui_path + "/create_volume.ui")
        self.form.cb_alignment.currentIndexChanged.connect(self.list_regions)
        self.form.cb_region.currentIndexChanged.connect(self.list_sections)

        self.list_alignments()

    def list_alignments(self):
        # Add sections to QListWidget
        self.form.cb_alignment.clear()
        self.alignment_dict = {}
        alignments = get_group.get("Alignments")
        for alignment in alignments.Group:
            self.alignment_dict[alignment.Label] = alignment
            self.form.cb_alignment.addItem(alignment.Label)

    def list_regions(self):
        self.form.cb_region.clear()
        text = self.form.cb_alignment.currentText()
        alignment = self.alignment_dict[text]

        for item in alignment.Group:
            if item.Proxy.Type == 'Trails::Regions':
                regions = item
                break

        self.region_dict = {}
        for region in regions.Group:
            self.region_dict[region.Label] = region
            self.form.cb_region.addItem(region.Label)

    def list_sections(self):
        self.form.lw_tops.clear()
        self.form.lw_bottoms.clear()
        text = self.form.cb_region.currentText()
        region = self.region_dict[text]
        
        for item in region.Group:
            if item.Proxy.Type == 'Trails::Sections':
                sections = item
                break

        self.section_dict = {}
        for section in sections.Group:
            self.section_dict[section.Label] = section
            self.form.lw_tops.addItem(section.Label)
            self.form.lw_bottoms.addItem(section.Label)

    def accept(self):
        """
        Start event to detect mouse click
        """
        text = self.form.cb_region.currentText()
        region = self.region_dict[text]

        tops = []
        for item in self.form.lw_tops.selectedItems():
            tops.append(self.section_dict[item.text()])

        bottoms = []
        for item in self.form.lw_bottoms.selectedItems():
            bottoms.append(self.section_dict[item.text()])

        volume = make_volume.create(region)
        volume.TopSections = tops
        volume.BottomSections = bottoms

        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.Control.closeDialog()
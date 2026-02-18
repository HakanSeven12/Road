# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the task panel code for Task Panels."""

class TaskPanel:
    def __init__(self,widget=None):
        self.form = widget

    def accept(self):
        return True

    def reject(self):
        return True

    def clicked(self, index):
        pass

    def open(self):
        pass

    def needsFullSpace(self):
        return True

    def isAllowedAlterSelection(self):
        return True

    def isAllowedAlterView(self):
        return True

    def isAllowedAlterDocument(self):
        return True

    def helpRequested(self):
        pass

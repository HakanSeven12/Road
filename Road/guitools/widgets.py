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

import FreeCAD, FreeCADGui

from PySide.QtWidgets import QLineEdit

from ..utils.trackers import ViewTracker


class GeoWidget(QLineEdit):
    def __init__(self):
        mw = FreeCADGui.getMainWindow()
        super().__init__(mw)

        mw.statusBar().addPermanentWidget(self)
        self.view = FreeCADGui.ActiveDocument.ActiveView

        self.tracker = ViewTracker("Location", function=self.coordinate_update, cancelable=False)

    def show(self):
        super().show()
        self.tracker.start()

    def hide(self):
        super().hide()
        self.tracker.stop()

    def coordinate_update(self, callback):
        try:
            obj = self.view.getObjectInfo(self.view.getCursorPos())
            coordinate = FreeCAD.Vector(obj["x"], obj["y"], obj["z"])

        except Exception:
            event = callback.getEvent()
            position = event.getPosition() #Window position
            coordinate = self.view.getPoint(tuple(position.getValue()))
            coordinate.z = 0

        origin = FreeCAD.ActiveDocument.getObject("GeoOrigin")
        if origin:
            coordinate = coordinate.add(origin.Base)

        infoText = ", ".join([f"{value/1000:.3f}" for value in coordinate])

        self.setText(infoText)
        self.setMinimumWidth(200)

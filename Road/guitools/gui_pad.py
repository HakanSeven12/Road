# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to create Pad objects."""

import FreeCAD, FreeCADGui
import Part

from ..variables import icons_path
from ..make import make_terrain, make_cluster
from ..utils.get_group import georigin


class CreatePad:
    """
    Command to create a new pad
    """

    def __init__(self):
        """
        Constructor
        """
        pass

    def GetResources(self):
        """
        Return the command resources dictionary
        """
        return {
            'Pixmap': icons_path + '/CreatePad.svg',
            'MenuText': "Create Pad",
            'ToolTip': "Create pad from selected closed polyline."
            }

    def IsActive(self):
        """
        Define tool button activation situation
        """
        # Check for document
        if FreeCAD.ActiveDocument:
            return True
        return False

    def Activated(self):
        """
        Command activation method
        """
        slope = 1
        length = 30000
        self.origin = georigin()

        polyline = FreeCADGui.Selection.getSelection()[-2]
        self.target = FreeCADGui.Selection.getSelection()[-1]

        self.copy_shape = polyline.Shape.copy()
        self.copy_shape.Placement.move(self.origin.Origin)
        self.points = self.copy_shape.discretize(Distance=5000)

        self.pg = make_cluster.create()
        self.terrain = make_terrain.create()

        maxz = self.target.Mesh.BoundBox.ZMax
        minz = self.target.Mesh.BoundBox.ZMin
        fill_points = self.get_secpts(slope, minz)
        cut_points = self.get_secpts(slope, maxz)

        self.pg.Vectors = self.points + fill_points + cut_points
        self.terrain.PointGroups = [self.pg]

        FreeCAD.ActiveDocument.recompute()

    def get_secpts(self,slope, z):
        shape = self.copy_shape.copy()
        length = z - shape.Placement.Base.z
        shape.Placement.move(FreeCAD.Vector(0,0, slope*length))
        offpoints = shape.makeOffset2D(
            abs(length)).discretize(Angular=1,Curvature=100,Minimum=2)

        self.pg.Vectors = offpoints + self.points
        self.terrain.PointGroups = [self.pg]

        intersec = self.terrain.Mesh.section(
            self.target.Mesh, MinDist=0.01)

        border = []
        for point in intersec[0]:
            if point.z == self.copy_shape.Placement.Base.z: continue
            border.append(point.add(self.origin.Origin))

        intsec = Part.makePolygon(border)
        intpts = intsec.discretize(Distance=5000)

        return intpts

FreeCADGui.addCommand('Create Pad', CreatePad())

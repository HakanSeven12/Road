# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Region objects."""

import FreeCAD
from pivy import coin
import math
from ..geoutils.alignment_old import transformation
from .view_geo_object import ViewProviderGeoObject


class ViewProviderRegion(ViewProviderGeoObject):
    """This class is about Region Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "Region")
        vobj.addProperty(
            "App::PropertyBool", "Labels", "Base",
            "Show/hide labels").Labels = True

        vobj.addProperty(
            "App::PropertyColor", "LabelColor", "Label Style",
            "Color of station label").LabelColor = (1.0, 1.0, 1.0)

        vobj.addProperty(
            "App::PropertyFloat", "LabelSize", "Label Style",
            "Size of station label").LabelSize = 1

        vobj.addProperty(
            "App::PropertyFont", "FontName", "Label Style",
            "Font name of station label").FontName

        vobj.addProperty(
            "App::PropertyEnumeration", "Justification", "Label Placement",
            "Justification of station label").Justification = ["Left", "Center", "Right"]

        vobj.addProperty(
            "App::PropertyFloat", "OffsetX", "Label Placement",
            "Horizontal offset between station label and tick").OffsetX = 1

        vobj.addProperty(
            "App::PropertyFloat", "OffsetY", "Label Placement",
            "Vertical offset between point station and tick").OffsetY = 0

        vobj.addProperty(
            "App::PropertyVector", "LabelOffset", "Label Placement",
            "Points of reference for station label").LabelOffset = FreeCAD.Vector(vobj.OffsetX, vobj.OffsetY)

        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        super().attach(vobj)
        self.Object = vobj.Object

        self.draw_style = coin.SoDrawStyle()
        self.draw_style.style = coin.SoDrawStyle.LINES


        #-----------------------------------------------------------------
        # Lines
        #-----------------------------------------------------------------

        # Line view
        self.line_color = coin.SoBaseColor()

        line_view = coin.SoGroup()
        line_view.addChild(self.draw_style)
        line_view.addChild(self.line_color)

        # Line data
        self.line_coords = coin.SoCoordinate3()
        self.line_lines = coin.SoIndexedLineSet()

        line_data = coin.SoGroup()
        line_data.addChild(self.line_coords)
        line_data.addChild(self.line_lines)

        # Line group
        lines = coin.SoAnnotation()
        lines.addChild(line_view)
        lines.addChild(line_data)


        #-----------------------------------------------------------------
        # Labels
        #-----------------------------------------------------------------

        # Text
        self.font = coin.SoFont()
        self.label_color = coin.SoBaseColor()

        self.texts = coin.SoGroup()

        self.labels = coin.SoSeparator()
        self.labels.addChild(self.font)
        self.labels.addChild(self.label_color)
        self.labels.addChild(self.texts)

        #-----------------------------------------------------------------
        # Region
        #-----------------------------------------------------------------

        # Standard group
        standard_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        standard_selection.style = 'EMISSIVE_DIFFUSE'
        standard_selection.addChild(lines)
        standard_selection.addChild(self.labels)

        self.standard.addChild(standard_selection)

        vobj.addDisplayMode(self.standard, "Standard")

        self.onChanged(vobj, "Labels")
        self.onChanged(vobj, "LabelColor")
        self.onChanged(vobj, "LabelSize")
        self.onChanged(vobj, "FontName")
        self.onChanged(vobj, "Justification")


    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        if prop == "Labels":
            self.texts.removeAllChildren()
            regions = vobj.Object.getParentGroup()
            alignment = regions.getParentGroup()

            tangent = vobj.Object.IncrementAlongTangents
            curve = vobj.Object.IncrementAlongCurves
            spiral = vobj.Object.IncrementAlongSpirals
            horizontal = vobj.Object.AtHorizontalGeometry

            stations = transformation(alignment, tangent, curve, spiral, horizontal)
            for station, transform in stations.items():
                point = transform["Location"]
                angle = transform["Rotation"]

                transform = coin.SoTransform()
                location = coin.SoTranslation()
                text = coin.SoAsciiText()


                if vobj.Justification == "Left":
                    text.justification = coin.SoAsciiText.LEFT
                elif vobj.Justification == "Right":
                    text.justification = coin.SoAsciiText.RIGHT
                else:
                    text.justification = coin.SoAsciiText.CENTER

                if math.pi / 2 < angle < 3 * math.pi /2:
                    text.justification = 2 if text.justification == 1 else 1
                    angle = (angle + math.pi) % (2 * math.pi)

                transform.translation = point
                transform.rotation.setValue(coin.SbVec3f(0, 0, 1), angle)
                location.translation = vobj.LabelOffset 

                station = str(station).zfill(6)
                integer = station.split('.')[0]
                new_integer = integer[:-3] + "+" + integer[-3:]

                text.string.setValues([new_integer + "." + station.split('.')[1]])

                group = coin.SoTransformSeparator()
                group.addChild(transform)
                group.addChild(location)
                group.addChild(text)
                self.texts.addChild(group)


        elif prop == "LabelColor":
            color = vobj.getPropertyByName(prop)
            self.label_color.rgb = (color[0], color[1], color[2])

        elif prop == "LabelSize":
            self.font.size = vobj.getPropertyByName(prop) * 1000
            self.onChanged(vobj, "OffsetY")

        elif prop == "FontName":
            self.font.name = vobj.getPropertyByName(prop).encode("utf8")

        elif prop == "Justification":
            self.onChanged(vobj, "OffsetX")

        elif prop == "OffsetX":
            justification = -1 if vobj.Justification == "Right" else 1
            vobj.LabelOffset.x = vobj.getPropertyByName(prop) * 1000 * justification
            self.onChanged(vobj, "LabelOffset")

        elif prop == "OffsetY":
            y_offset = vobj.getPropertyByName(prop)
            vobj.LabelOffset.y = -vobj.LabelSize / 2 + y_offset * 1000
            self.onChanged(vobj, "LabelOffset")

        elif prop == "LabelOffset":
            self.onChanged(vobj, "Labels")

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)
        if prop == "Shape":
            line_coords, line_index = [], []
            for edge in obj.Shape.Edges:
                start = len(line_coords)
                line_coords.extend(edge.discretize(2))
                end = len(line_coords)

                line_index.extend(range(start,end))
                line_index.append(-1)

            self.line_coords.point.values = line_coords
            self.line_lines.coordIndex.values = line_index

    def claimChildren(self):
        """Provides object grouping"""
        return self.Object.Group
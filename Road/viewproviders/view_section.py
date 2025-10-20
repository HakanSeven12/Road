# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Profile Frame objects."""

import FreeCAD, FreeCADGui
from pivy import coin

from ..variables import icons_path
from ..utils.get_group import georigin


class ViewProviderSection:
    """This class is about Profile Frame Object view features."""
    def __init__(self, vobj):
        """Set view properties."""

        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        self.Object = vobj.Object

        self.draw_style = coin.SoDrawStyle()
        self.draw_style.style = coin.SoDrawStyle.LINES

        #-----------------------------------------------------------------
        # Title
        #-----------------------------------------------------------------

        #-----------------------------------------------------------------
        # Frame Border
        #-----------------------------------------------------------------

        # View
        self.border_color = coin.SoBaseColor()
        self.border_color.rgb = (0.0, 0.0, 1.0)

        border_view = coin.SoGroup()
        border_view.addChild(self.draw_style)
        border_view.addChild(self.border_color)

        # Data
        self.border_coords = coin.SoCoordinate3()
        self.border_lines = coin.SoLineSet()

        border_data = coin.SoGroup()
        border_data.addChild(self.border_coords)
        border_data.addChild(self.border_lines)

        # Group
        border = coin.SoSeparator()
        border.addChild(border_view)
        border.addChild(border_data)

        #-----------------------------------------------------------------
        # Frame Grid
        #-----------------------------------------------------------------

        # View
        self.grid_color = coin.SoBaseColor()
        self.grid_color.rgb = (0.5, 0.5, 0.5)

        # Horizontal lines
        self.horizontal_coords = coin.SoCoordinate3()
        horizontal_lines = coin.SoIndexedLineSet()

        self.horizontal_copy = coin.SoMultipleCopy()
        self.horizontal_copy.addChild(self.horizontal_coords)
        self.horizontal_copy.addChild(horizontal_lines)

        horizontals = coin.SoSeparator()
        horizontals.addChild(self.grid_color)
        horizontals.addChild(self.horizontal_copy)

        # Vertical lines
        self.vertical_coords = coin.SoCoordinate3()
        vertical_lines = coin.SoLineSet()

        self.vertical_copy = coin.SoMultipleCopy()
        self.vertical_copy.addChild(self.vertical_coords)
        self.vertical_copy.addChild(vertical_lines)

        verticals = coin.SoSeparator()
        verticals.addChild(self.grid_color)
        verticals.addChild(self.vertical_copy)

        grid = coin.SoSeparator()
        grid.addChild(horizontals)
        grid.addChild(verticals)

        #-----------------------------------------------------------------
        # Sections
        #-----------------------------------------------------------------

        # Section view
        self.section_color = coin.SoBaseColor()

        section_view = coin.SoGroup()
        section_view.addChild(self.draw_style)
        section_view.addChild(self.section_color)

        # Section data
        self.section_coords = coin.SoCoordinate3()
        self.section_lines = coin.SoLineSet()

        section_data = coin.SoGroup()
        section_data.addChild(self.section_coords)
        section_data.addChild(self.section_lines)

        # Section group
        sections = coin.SoAnnotation()
        sections.addChild(section_view)
        sections.addChild(section_data)

        #-----------------------------------------------------------------
        # Labels
        #-----------------------------------------------------------------

        # View
        font = coin.SoFont()
        font.size = 1000

        # Horizon Label
        self.horizon = coin.SoAsciiText()
        self.horizon.justification = coin.SoAsciiText.RIGHT

        # Elevation Labels
        self.elevations = coin.SoSeparator()

        # Station Labels
        self.offsets = coin.SoSeparator()

        # Label Group
        labels = coin.SoSeparator()
        labels.addChild(font)
        labels.addChild(self.horizon)
        labels.addChild(self.elevations)
        labels.addChild(self.offsets)

        #-----------------------------------------------------------------
        # Profile Frame
        #-----------------------------------------------------------------

        # Frame group
        self.drag = coin.SoSeparator()
        self.frames = coin.SoGeoSeparator()
        self.frames.addChild(border)
        self.frames.addChild(grid)
        self.frames.addChild(sections)
        self.frames.addChild(labels)
        self.frames.addChild(self.drag)

        root = coin.SoType.fromName('SoFCSelection').createInstance()
        root.style = 'EMISSIVE_DIFFUSE'
        root.addChild(self.frames)

        vobj.addDisplayMode(root, "Frame")

    def onChanged(self, vobj, prop):
        """Update Object visuals when a view property changed."""
        pass

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "Placement":
            placement = obj.getPropertyByName(prop)
            origin = georigin(placement.Base)
            geo_system = ["UTM", origin.UtmZone, "FLAT"]

            self.frames.geoSystem.setValues(geo_system)
            self.frames.geoCoords.setValue(*placement.Base)

            """
            self.offsets.geoSystem.setValues(geo_system)
            self.offsets.geoCoords.setValue(*placement.Base)
            """

        if prop == "Shape":
            shape = obj.getPropertyByName(prop)
            if not shape.Compounds: return
            shape.Placement.move(obj.Placement.Base.negative())

            border_coords = []
            border_count = []
            borders = shape.SubShapes[0].SubShapes
            for border in borders:
                border_points = [ver.Point for ver in border.Vertexes]
                border_points.append(border_points[0])
                border_coords.extend(border_points)
                border_count.append(len(border_points))

            self.border_coords.point.values = border_coords
            self.border_lines.numVertices.values = border_count

            section_coords = []
            section_count = []
            sections = shape.SubShapes[1].SubShapes
            for section in sections:
                section_points = [ver.Point for ver in section.Vertexes]
                section_coords.extend(section_points)
                section_count.append(len(section_points))

            self.section_coords.point.values = section_coords
            self.section_lines.numVertices.values = section_count

        if prop == "Model":
            model = obj.getPropertyByName(prop)
            self.elevations.removeAllChildren()
            self.offsets.removeAllChildren()

            return
            for sta, data in model.items():
                vertical_matrices = []
                for pos in range(10000, int(obj.Width), 10000):
                    matrix = coin.SbMatrix()
                    location = coin.SoTranslation()
                    station = coin.SoAsciiText()

                    matrix.setTransform(
                        coin.SbVec3f(pos, 0, -1), 
                        coin.SbRotation(), 
                        coin.SbVec3f(1.0, 1.0, 1.0))
                    vertical_matrices.append(matrix)

                    location.translation = coin.SbVec3f(pos, obj.Height+500, 0)
                    station.justification = coin.SoAsciiText.CENTER

                    text = str(round(pos / 1000, 2)).zfill(6)
                    integer = text.split('.')[0]
                    new_integer = integer[:-3] + "+" + integer[-3:]

                    station.string.setValues([new_integer + "." + text.split('.')[1]])

                    group = coin.SoTransformSeparator()
                    group.addChild(location)
                    group.addChild(station)
                    self.offsets.addChild(group)

                self.vertical_coords.point.values = [corners[0], corners[3]]
                self.vertical_copy.matrix.values = vertical_matrices

                horizontal_matrices = []
                start = (horizon + 9999) // 10000 * 10000
                for pos in range(int(start), int(horizon+obj.Height), 10000):
                    matrix = coin.SbMatrix()
                    location = coin.SoTranslation()
                    elevation = coin.SoAsciiText()

                    matrix.setTransform(
                        coin.SbVec3f(0, pos-horizon, -1), 
                        coin.SbRotation(), 
                        coin.SbVec3f(1.0, 1.0, 1.0))
                    horizontal_matrices.append(matrix)

                    location.translation = coin.SbVec3f(-500, pos-horizon, 0)
                    elevation.justification = coin.SoAsciiText.RIGHT
                    elevation.string.setValues([round(pos/1000, 3)])

                    group = coin.SoTransformSeparator()
                    group.addChild(location)
                    group.addChild(elevation)
                    self.elevations.addChild(group)

                self.horizontal_coords.point.values = [corners[0], corners[1]]
                self.horizontal_copy.matrix.values = horizontal_matrices

    def getDisplayModes(self,vobj):
        """Return a list of display modes."""
        modes = ["Frame"]
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "Frame"

    def setDisplayMode(self,mode):
        """Map the display mode defined in attach with 
        those defined in getDisplayModes."""
        return mode

    def getIcon(self):
        """Return object treeview icon."""
        return icons_path + "/ProfileFrame.svg"

    def doubleClicked(self, vobj):
        """Detect double click"""
        dragger = coin.SoTranslate2Dragger()
        marker = coin.SoMarkerSet()
        scale = coin.SoScale()

        scale.scaleFactor.setValue(1000.0, 1000.0, 1000.0)
        dragger.translation.setValue(0, 0, 1)
        marker.markerIndex = 81

        translator = dragger.getPart("translator", False)
        geometry = translator.getChildren()[1]
        geometry.removeAllChildren()
        geometry.addChild(marker)

        self.drag.addChild(scale)
        self.drag.addChild(dragger)

        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.view.addDraggerCallback(dragger, "addFinishCallback", self.update_placement)

        return True

    def update_placement(self, dragger):
        displacement = FreeCAD.Vector(dragger.translation.getValue().getValue())
        self.Object.Placement.move(displacement)
        self.drag.removeAllChildren()
        FreeCAD.ActiveDocument.recompute()

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
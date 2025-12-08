# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Profile Frame objects."""

import FreeCAD, FreeCADGui, Part
from pivy import coin
from .view_geo_object import ViewProviderGeoObject


class ViewProviderProfile(ViewProviderGeoObject):
    """This class is about Profile Frame Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "CreateProfileFrame")
        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        super().attach(vobj)
        self.Object = vobj.Object
        self.view = vobj

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
        horizontal_grid_template = coin.SoSeparator()
        self.horizontal_coords = coin.SoCoordinate3()
        horizontal_lines = coin.SoLineSet()
        horizontal_grid_template.addChild(self.horizontal_coords)
        horizontal_grid_template.addChild(horizontal_lines)

        self.horizontal_copy = coin.SoMultipleCopy()
        self.horizontal_copy.addChild(horizontal_grid_template)

        horizontals = coin.SoSeparator()
        horizontals.addChild(self.grid_color)
        horizontals.addChild(self.horizontal_copy)

        # Vertical lines
        vertical_grid_template = coin.SoSeparator()
        self.vertical_coords = coin.SoCoordinate3()
        vertical_lines = coin.SoLineSet()
        vertical_grid_template.addChild(self.vertical_coords)
        vertical_grid_template.addChild(vertical_lines)

        self.vertical_copy = coin.SoMultipleCopy()
        self.vertical_copy.addChild(vertical_grid_template)

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
        draw_style = coin.SoDrawStyle()
        draw_style.style = coin.SoDrawStyle.LINES
        draw_style.lineWidth = 2

        section_view = coin.SoGroup()
        section_view.addChild(draw_style)
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

        self.sel1 = coin.SoType.fromName('SoFCSelection').createInstance()
        self.sel1.style = 'EMISSIVE_DIFFUSE'
        self.sel1.addChild(border)

        self.sel2 = coin.SoType.fromName('SoFCSelection').createInstance()
        self.sel2.style = 'EMISSIVE_DIFFUSE'
        self.sel2.addChild(sections)

        # Frame group
        self.drag = coin.SoSeparator()
        self.standard.addChild(self.sel1)
        self.standard.addChild(grid)
        self.standard.addChild(self.sel2)
        self.standard.addChild(labels)
        self.standard.addChild(self.drag)

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)

        if prop == "Shape":
            if not len(obj.Shape.SubShapes) == 2: return
            border_coords = []
            border_count = []
            borders = obj.Shape.SubShapes[0].SubShapes
            for border in borders:
                border_points = [ver.Point for ver in border.Vertexes]
                border_points.append(border_points[0])
                border_coords.extend(border_points)
                border_count.append(len(border_points))

            self.border_coords.point.values = border_coords
            self.border_lines.numVertices.values = border_count

            section_coords = []
            section_count = []
            sections = obj.Shape.SubShapes[1].SubShapes
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

            # Starting position
            vertical_matrices = []
            horizontal_matrices = []
            for sta, data in model.items():
                # Calculate grid position for this item
                origin = obj.Placement.Base
                for pos in range(0, int(obj.Length*1000), 2000):
                    position = origin.add(FreeCAD.Vector(pos, 0))
                    position2 = origin.add(FreeCAD.Vector(pos, obj.Height*1000+500))
                    matrix = coin.SbMatrix()
                    location = coin.SoTranslation()
                    offset = coin.SoAsciiText()

                    matrix.setTransform(
                        coin.SbVec3f(*position), 
                        coin.SbRotation(), 
                        coin.SbVec3f(1.0, 1.0, 1.0))
                    vertical_matrices.append(matrix)

                    location.translation = coin.SbVec3f(*position2)
                    offset.justification = coin.SoAsciiText.CENTER
                    offset.string.setValues([int(pos / 1000)])

                    group = coin.SoTransformSeparator()
                    group.addChild(location)
                    group.addChild(offset)
                    self.offsets.addChild(group)

                horizon = obj.Horizon * 1000
                for pos in range(0, int(obj.Height*1000), 2000):
                    position = origin.add(FreeCAD.Vector(0, pos))
                    matrix = coin.SbMatrix()
                    location = coin.SoTranslation()
                    elevation = coin.SoAsciiText()

                    matrix.setTransform(
                        coin.SbVec3f(*position), 
                        coin.SbRotation(), 
                        coin.SbVec3f(1.0, 1.0, 1.0))
                    horizontal_matrices.append(matrix)

                    location.translation = coin.SbVec3f(*position)
                    elevation.justification = coin.SoAsciiText.RIGHT
                    elevation.string.setValues([round((horizon+pos)/1000, 3)])

                    group = coin.SoTransformSeparator()
                    group.addChild(location)
                    group.addChild(elevation)
                    self.elevations.addChild(group)

            self.vertical_coords.point.values = [FreeCAD.Vector(), FreeCAD.Vector(0,obj.Height*1000)]
            self.vertical_copy.matrix.values = vertical_matrices

            self.horizontal_coords.point.values = [FreeCAD.Vector(obj.Length*1000,0) , FreeCAD.Vector()]
            self.horizontal_copy.matrix.values = horizontal_matrices

    def getDetailPath(self, subname, path, append):
        vobj = self.view
        if append:
            path.append(vobj.RootNode)
            path.append(vobj.SwitchNode)

            mode = vobj.SwitchNode.whichChild.getValue()
            if mode >= 0:
                mode = vobj.SwitchNode.getChild(mode)
                path.append(mode)
                sub = Part.splitSubname(subname)[-1]
                if sub == 'Atom1':
                    path.append(self.sel1)
                elif sub == 'Atom2':
                    path.append(self.sel2)
                else:
                    path.append(mode.getChild(0))
        return True

    def getElementPicked(self, pp):
        path = pp.getPath()
        if path.findNode(self.sel1) >= 0:
            return 'Atom1'
        if path.findNode(self.sel2) >= 0:
            return 'Atom2'
        raise NotImplementedError

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
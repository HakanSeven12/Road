# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Profile Frame objects."""

import FreeCAD, FreeCADGui, Part
from pivy import coin
from .view_geo_object import ViewProviderGeoObject
from ..utils.label_manager import LabelManager
from ..utils.frame_manager import FrameManager


class ViewProviderSection(ViewProviderGeoObject):
    """This class is about Profile Frame Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "CreateSections")
        vobj.Proxy = self
    
    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        super().attach(vobj)
        self.Object = vobj.Object
        self.view = vobj

        self.draw_style = coin.SoDrawStyle()
        self.draw_style.style = coin.SoDrawStyle.LINES

        #-----------------------------------------------------------------
        # Frame and Grid (using FrameManager)
        #-----------------------------------------------------------------
        from ..utils.frame_manager import FrameManager
        self.frame_manager = FrameManager(self.standard)

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
        # Labels (using LabelManager)
        #-----------------------------------------------------------------
        from ..utils.label_manager import LabelManager
        label_root = coin.SoSeparator()
        self.label_manager = LabelManager(label_root)

        #-----------------------------------------------------------------
        # Complete Scene
        #-----------------------------------------------------------------
        self.sel2 = coin.SoType.fromName('SoFCSelection').createInstance()
        self.sel2.style = 'EMISSIVE_DIFFUSE'
        self.sel2.addChild(sections)

        self.drag = coin.SoSeparator()
        self.standard.addChild(self.sel2)
        self.standard.addChild(label_root)
        self.standard.addChild(self.drag)

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)

        if prop == "Shape":
            if not len(obj.Shape.SubShapes) == 2: return
            
            section_coords = []
            section_count = []
            sections = obj.Shape.SubShapes[1].SubShapes
            for section in sections:
                section_points = [ver.Point for ver in section.Vertexes]
                section_coords.extend(section_points)
                section_count.append(len(section_points))

            self.section_coords.point.values = section_coords
            self.section_lines.numVertices.values = section_count
            
            # Update frames when Shape is updated (if Model is ready)
            if obj.Model:
                self._update_frames_and_labels(obj)

        if prop == "Model":
            if not obj.Model: return
            # Update frames when Model is updated (if Shape is ready)
            if obj.Shape and len(obj.Shape.SubShapes) == 2:
                self._update_frames_and_labels(obj)

    def _update_frames_and_labels(self, obj):
        """Helper method to update frames and labels"""
        # Create frames
        frames = self.frame_manager.create_section_frames(
            obj.Model, obj.Placement, obj.Width, obj.Height,
            obj.Horizontal, obj.Vertical)
        
        # Update frame visualization
        self.frame_manager.update_borders(frames)
        self.frame_manager.update_grid(frames)
        
        # Clear and create labels
        self.label_manager.clear_labels()
        
        for frame in frames:
            origin = frame['origin']
            horizon = frame['horizon']
            
            # Vertical labels (offsets)
            for i, pos in enumerate(frame['vertical_positions']):
                label_pos = origin.add(FreeCAD.Vector(pos * 1000, obj.Height * 1000 + 500, 0))
                self.label_manager.add_label(label_pos, str(int(pos)), "Center")
            
            # Horizontal labels (elevations)
            for i, pos in enumerate(frame['horizontal_positions']):
                label_pos = origin.add(FreeCAD.Vector(-obj.Width * 1000 / 2, pos * 1000, 0))
                elevation = round(horizon + pos, 3)
                self.label_manager.add_label(label_pos, str(elevation), "Right")
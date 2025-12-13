# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Profile Frame objects."""

from pivy import coin
from .view_geo_object import ViewProviderGeoObject


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
        # Complete Scene
        #-----------------------------------------------------------------
        self.sel2 = coin.SoType.fromName('SoFCSelection').createInstance()
        self.sel2.style = 'EMISSIVE_DIFFUSE'
        self.sel2.addChild(sections)

        self.drag = coin.SoSeparator()
        self.standard.addChild(self.sel2)
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
        
        # Update all visualizations
        self.frame_manager.update(frames, obj.Width, obj.Height)
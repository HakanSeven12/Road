# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Profile Frame objects."""

from pivy import coin
from .view_geo_object import ViewProviderGeoObject


class ViewProviderProfileFrame(ViewProviderGeoObject):
    """This class is about Profile Frame Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "ProfileFrame")
        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        super().attach(vobj)
        self.Object = vobj.Object
        self.view = vobj

        #-----------------------------------------------------------------
        # Frame and Grid (using FrameManager)
        #-----------------------------------------------------------------
        from ..utils.frame_manager import FrameManager
        self.frame_manager = FrameManager(self.standard)

        #-----------------------------------------------------------------
        # Surface Profiles
        #-----------------------------------------------------------------
        surface_draw_style = coin.SoDrawStyle()
        surface_draw_style.style = coin.SoDrawStyle.LINES
        surface_draw_style.lineWidth = 2

        self.surface_color = coin.SoBaseColor()
        self.surface_color.rgb = (0.0, 1.0, 0.0)  # Green

        self.surface_coords = coin.SoCoordinate3()
        self.surface_lines = coin.SoLineSet()

        surface_group = coin.SoGroup()
        surface_group.addChild(surface_draw_style)
        surface_group.addChild(self.surface_color)
        surface_group.addChild(self.surface_coords)
        surface_group.addChild(self.surface_lines)

        self.surface_profiles = coin.SoAnnotation()
        self.surface_profiles.addChild(surface_group)

        #-----------------------------------------------------------------
        # Design Profiles (with per-element coloring)
        #-----------------------------------------------------------------
        design_draw_style = coin.SoDrawStyle()
        design_draw_style.style = coin.SoDrawStyle.LINES
        design_draw_style.lineWidth = 3

        self.design_material = coin.SoMaterial()
        self.design_colors = coin.SoMaterialBinding()
        self.design_colors.value = coin.SoMaterialBinding.PER_PART

        self.design_coords = coin.SoCoordinate3()
        self.design_lines = coin.SoLineSet()

        design_group = coin.SoGroup()
        design_group.addChild(design_draw_style)
        design_group.addChild(self.design_material)
        design_group.addChild(self.design_colors)
        design_group.addChild(self.design_coords)
        design_group.addChild(self.design_lines)

        self.design_profiles = coin.SoAnnotation()
        self.design_profiles.addChild(design_group)

        #-----------------------------------------------------------------
        # Complete Scene
        #-----------------------------------------------------------------
        self.sel2 = coin.SoType.fromName('SoFCSelection').createInstance()
        self.sel2.style = 'EMISSIVE_DIFFUSE'
        self.sel2.addChild(self.surface_profiles)
        self.sel2.addChild(self.design_profiles)

        self.drag = coin.SoSeparator()
        self.standard.addChild(self.sel2)
        self.standard.addChild(self.drag)
        
    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)

        if prop == "Shape":
            if not obj.Shape or not obj.Shape.SubShapes:
                return
            
            # Shape structure: [frame_border, surface_compound, design_compound]
            if len(obj.Shape.SubShapes) < 3:
                return
            
            # Extract compounds
            frame_border = obj.Shape.SubShapes[0]
            surface_compound = obj.Shape.SubShapes[1]
            design_compound = obj.Shape.SubShapes[2]
            
            # Update surface profiles
            self._update_surface_profiles_from_shape(surface_compound)
            
            # Update design profiles with coloring
            self._update_design_profiles_from_shape(design_compound)
            
            # Update frame
            self._update_frame(obj)

    def _update_surface_profiles_from_shape(self, surface_compound):
        """Update surface profile visualization from Shape."""
        
        all_coords = []
        all_counts = []
        
        if surface_compound.SubShapes:
            for shape in surface_compound.SubShapes:
                # Each shape is a line/curve representing a tangent segment
                if hasattr(shape, 'Vertexes'):
                    points = [v.Point for v in shape.Vertexes]
                    if len(points) > 1:
                        all_coords.extend(points)
                        all_counts.append(len(points))
        
        # Update Coin3D nodes
        if all_coords:
            self.surface_coords.point.setValues(0, len(all_coords), all_coords)
            self.surface_lines.numVertices.setValues(0, len(all_counts), all_counts)

    def _update_design_profiles_from_shape(self, design_compound):
        """Update design profile visualization from Shape with element-based coloring."""
        
        all_coords = []
        all_counts = []
        all_colors = []
        
        # Get parent alignment to access profile model
        profiles = self.Object.getParentGroup()
        if profiles is None:
            return
        
        alignment = profiles.getParentGroup()
        if alignment is None:
            return
        
        alignment_model = alignment.Model
        if not alignment_model or not alignment_model.has_profile():
            return
        
        profile = alignment_model.get_profile()
        
        # Color mapping
        color_map = {
            'Tangent': (1.0, 0.0, 0.0),    # Red
            'ParaCurve': (0.55, 0.35, 0.95),  # Purple
            'CircCurve': (0.0, 0.0, 1.0)   # Blue
        }
        
        if design_compound.SubShapes:
            # Get geometry elements to match with shapes
            profalign_names = profile.get_profalign_names()
            
            shape_index = 0
            for profalign_name in profalign_names:
                geometry_elements = profile.get_geometry_elements(profalign_name)
                
                for elem in geometry_elements:
                    if shape_index >= len(design_compound.SubShapes):
                        break
                    
                    shape = design_compound.SubShapes[shape_index]
                    
                    # Extract points from shape
                    if hasattr(shape, 'Vertexes'):
                        points = [v.Point for v in shape.Vertexes]
                        if len(points) > 1:
                            all_coords.extend(points)
                            all_counts.append(len(points))
                            
                            # Determine color based on element type
                            elem_dict = elem.to_dict()
                            elem_type = elem_dict.get('Type', 'Tangent')
                            color = color_map.get(elem_type, (1.0, 1.0, 1.0))
                            all_colors.append(color)
                    
                    shape_index += 1
        
        # Update Coin3D nodes
        if all_coords:
            self.design_coords.point.setValues(0, len(all_coords), all_coords)
            self.design_lines.numVertices.setValues(0, len(all_counts), all_counts)
            self.design_material.diffuseColor.setValues(0, len(all_colors), all_colors)

    def _update_frame(self, obj):
        """Update frame visualization using FrameManager."""
        
        # Create frame
        frame = self.frame_manager.create_profile_frame(
            obj.Placement, obj.Length, obj.Height)
        
        # Add horizon to frame data
        frame['horizon'] = obj.Horizon
        
        # Update all visualizations
        self.frame_manager.update(frame, obj.Length, obj.Height)
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
            
        if prop in ["Placement", "Length", "Height", "Horizon"]:
            # Update frame
            # Create frame
            frame = self.frame_manager.create_profile_frame(
                obj.Placement, obj.Length, obj.Height)
            
            # Add horizon to frame data
            frame['horizon'] = obj.Horizon
            
            # Update all visualizations
            self.frame_manager.update(frame, obj.Length, obj.Height)

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
        
        # Discretization map
        discretize_map = {
            'Part::GeomLine':         2,  # Tangent
            'Part::GeomBSplineCurve': 50, # ParaCurve
            'Part::GeomCircle':       50  # CircCurve
        }
        # Color mapping
        color_map = {
            'Part::GeomLine':         (1.0, 0.0, 0.0), # Red
            'Part::GeomBSplineCurve': (0.0, 0.0, 1.0), # Blue
            'Part::GeomCircle':       (0.0, 0.0, 1.0)  # Blue
        }

        
        # Get geometry elements to match with shapes
        for shape in design_compound.SubShapes:
            for edge in shape.Edges:
                points = edge.discretize(discretize_map[edge.Curve.TypeId])
                all_coords.extend(points)
                all_counts.append(len(points))
                all_colors.extend([color_map[edge.Curve.TypeId] ] * (len(points)-1))
        
        # Update Coin3D nodes
        if all_coords:
            self.design_coords.point.setValues(0, len(all_coords), all_coords)
            self.design_lines.numVertices.setValues(0, len(all_counts), all_counts)
            self.design_material.diffuseColor.setValues(0, len(all_colors), all_colors)
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
Frame manager for Profile and Section views
"""

import FreeCAD
from pivy import coin
import math


class FrameManager:
    """
    Centralized frame and grid management for profile and section views
    """
    
    def __init__(self, root_node):
        """
        Initialize frame manager
        
        Args:
            root_node: Parent coin3d node to attach frames
        """
        self.root_node = root_node
        
        # Border components
        self.border_coords = coin.SoCoordinate3()
        self.border_lines = coin.SoLineSet()
        self.border_color = coin.SoBaseColor()
        self.border_color.rgb = (0.0, 0.0, 1.0)
        
        # Grid components
        self.grid_color = coin.SoBaseColor()
        self.grid_color.rgb = (0.5, 0.5, 0.5)
        self.horizontal_coords = coin.SoCoordinate3()
        self.vertical_coords = coin.SoCoordinate3()
        self.horizontal_copy = coin.SoMultipleCopy()
        self.vertical_copy = coin.SoMultipleCopy()
        
        self._setup_scene_graph()
    
    def _setup_scene_graph(self):
        """Create the coin3d scene graph structure"""
        draw_style = coin.SoDrawStyle()
        draw_style.style = coin.SoDrawStyle.LINES
        
        # Border setup
        border_view = coin.SoGroup()
        border_view.addChild(draw_style)
        border_view.addChild(self.border_color)
        
        border_data = coin.SoGroup()
        border_data.addChild(self.border_coords)
        border_data.addChild(self.border_lines)
        
        border = coin.SoSeparator()
        border.addChild(border_view)
        border.addChild(border_data)
        
        # Grid setup - Horizontal lines
        horizontal_grid_template = coin.SoSeparator()
        horizontal_grid_template.addChild(self.horizontal_coords)
        horizontal_grid_template.addChild(coin.SoLineSet())
        
        self.horizontal_copy.addChild(horizontal_grid_template)
        
        horizontals = coin.SoSeparator()
        horizontals.addChild(self.grid_color)
        horizontals.addChild(self.horizontal_copy)
        
        # Grid setup - Vertical lines
        vertical_grid_template = coin.SoSeparator()
        vertical_grid_template.addChild(self.vertical_coords)
        vertical_grid_template.addChild(coin.SoLineSet())
        
        self.vertical_copy.addChild(vertical_grid_template)
        
        verticals = coin.SoSeparator()
        verticals.addChild(self.grid_color)
        verticals.addChild(self.vertical_copy)
        
        grid = coin.SoSeparator()
        grid.addChild(horizontals)
        grid.addChild(verticals)
        
        # Selection node for border
        self.sel1 = coin.SoType.fromName('SoFCSelection').createInstance()
        self.sel1.style = 'EMISSIVE_DIFFUSE'
        self.sel1.addChild(border)
        
        # Add to root
        self.root_node.addChild(self.sel1)
        self.root_node.addChild(grid)
    
    def create_frame(self, origin, width, height, spacing=2000, center_origin=False):
        """
        Create a single frame with grid
        
        Args:
            origin: FreeCAD.Vector for frame origin
            width: Frame width in meters
            height: Frame height in meters
            spacing: Grid spacing in mm (default 2000mm = 2m)
            center_origin: If True, origin is at center bottom; if False, at left bottom
            
        Returns:
            dict: Frame data with origin, width, height, and grid positions
        """
        # Convert to mm
        width_mm = width * 1000
        height_mm = height * 1000
        
        # Calculate frame corners based on origin type
        if center_origin:
            # Origin at center bottom (for sections)
            p1 = origin
            p2 = origin.add(FreeCAD.Vector(-width_mm / 2, 0, 0))
            p3 = origin.add(FreeCAD.Vector(-width_mm / 2, height_mm, 0))
            p4 = origin.add(FreeCAD.Vector(width_mm / 2, height_mm, 0))
            p5 = origin.add(FreeCAD.Vector(width_mm / 2, 0, 0))
            
            # Vertical grid positions (centered around origin)
            v_start = int(-width_mm/2)
            v_end = int(width_mm/2) + 1
        else:
            # Origin at left bottom (for profile)
            p1 = origin
            p2 = origin
            p3 = origin.add(FreeCAD.Vector(0, height_mm, 0))
            p4 = origin.add(FreeCAD.Vector(width_mm, height_mm, 0))
            p5 = origin.add(FreeCAD.Vector(width_mm, 0, 0))
            
            # Vertical grid positions (starting from origin)
            v_start = 0
            v_end = int(width_mm) + 1
        
        border_points = [p1, p2, p3, p4, p5, p1]
        
        # Calculate grid matrices for vertical lines
        vertical_matrices = []
        vertical_positions = []
        for pos in range(v_start, v_end, spacing):
            position = origin.add(FreeCAD.Vector(pos, 0, 0))
            vertical_positions.append(pos / 1000)  # Store in meters for labels
            
            matrix = coin.SbMatrix()
            matrix.setTransform(
                coin.SbVec3f(*position), 
                coin.SbRotation(), 
                coin.SbVec3f(1.0, 1.0, 1.0))
            vertical_matrices.append(matrix)
        
        # Calculate grid matrices for horizontal lines
        horizontal_matrices = []
        horizontal_positions = []
        for pos in range(0, int(height_mm) + 1, spacing):
            position = origin.add(FreeCAD.Vector(0, pos, 0))
            horizontal_positions.append(pos / 1000)  # Store in meters for labels
            
            matrix = coin.SbMatrix()
            matrix.setTransform(
                coin.SbVec3f(*position), 
                coin.SbRotation(), 
                coin.SbVec3f(1.0, 1.0, 1.0))
            horizontal_matrices.append(matrix)
        
        return {
            'origin': origin,
            'width': width,
            'height': height,
            'border_points': border_points,
            'vertical_matrices': vertical_matrices,
            'horizontal_matrices': horizontal_matrices,
            'vertical_positions': vertical_positions,
            'horizontal_positions': horizontal_positions,
            'center_origin': center_origin
        }

    def create_profile_frame(self, model, placement, length, height, spacing=2000):
        """
        Create single frame for profile view
        
        Args:
            model: Profile model data
            placement: Object placement
            length: Profile length in meters
            height: Profile height in meters
            spacing: Grid spacing in mm
            
        Returns:
            dict: Frame data
        """
        origin = placement.Base
        
        # Profile uses length as width (horizontal axis is station)
        # Origin at left bottom
        return self.create_frame(origin, length, height, spacing, center_origin=False)

    def create_section_frames(self, model, placement, width, height, 
                            horizontal_spacing, vertical_spacing, grid_spacing=2000):
        """
        Create multiple frames for section view in grid layout
        
        Args:
            model: Section model data (dict with station keys)
            placement: Object placement
            width: Section width in meters
            height: Section height in meters
            horizontal_spacing: Horizontal distance between frames in meters
            vertical_spacing: Vertical distance between frames in meters
            grid_spacing: Grid spacing in mm
            
        Returns:
            list: List of frame data dicts with added 'station' and 'horizon' keys
        """
        frames = []
        total_items = len(model)
        grid_size = math.ceil(math.sqrt(total_items))
        
        current_col = 0
        current_row = 0
        
        for station, data in model.items():
            # Calculate grid position
            offset = FreeCAD.Vector(
                current_col * horizontal_spacing * 1000,
                current_row * vertical_spacing * 1000,
                0
            )
            origin = placement.Base.add(offset)
            
            # Create frame with centered origin
            frame = self.create_frame(origin, width, height, grid_spacing, center_origin=True)
            
            # Add station-specific data
            frame['station'] = station
            frame['horizon'] = data.get('horizon', 0)
            
            frames.append(frame)
            
            # Update grid position
            current_row += 1
            if current_row >= grid_size:
                current_row = 0
                current_col += 1
        
        return frames

    def update_borders(self, frames):
        """
        Update border visualization
        
        Args:
            frames: Single frame dict or list of frame dicts
        """
        if not isinstance(frames, list):
            frames = [frames]
        
        border_coords = []
        border_count = []
        
        for frame in frames:
            border_coords.extend(frame['border_points'])
            border_count.append(len(frame['border_points']))
        
        self.border_coords.point.values = border_coords
        self.border_lines.numVertices.values = border_count
    
    def update_grid(self, frames):
        """
        Update grid visualization
        
        Args:
            frames: Single frame dict or list of frame dicts
        """
        if not isinstance(frames, list):
            frames = [frames]
        
        # Collect all matrices
        all_vertical_matrices = []
        all_horizontal_matrices = []
        
        for frame in frames:
            all_vertical_matrices.extend(frame['vertical_matrices'])
            all_horizontal_matrices.extend(frame['horizontal_matrices'])
        
        # Update vertical lines (use first frame's height for line template)
        first_frame = frames[0]
        height_mm = first_frame['height'] * 1000
        self.vertical_coords.point.values = [
            FreeCAD.Vector(), 
            FreeCAD.Vector(0, height_mm, 0)
        ]
        self.vertical_copy.matrix.values = all_vertical_matrices
        
        # Update horizontal lines based on origin type
        width_mm = first_frame['width'] * 1000
        if first_frame['center_origin']:  # Section view (centered)
            self.horizontal_coords.point.values = [
                FreeCAD.Vector(-width_mm/2, 0, 0),
                FreeCAD.Vector(width_mm/2, 0, 0)
            ]
        else:  # Profile view (left aligned)
            self.horizontal_coords.point.values = [
                FreeCAD.Vector(),
                FreeCAD.Vector(width_mm, 0, 0)
            ]
        self.horizontal_copy.matrix.values = all_horizontal_matrices
    
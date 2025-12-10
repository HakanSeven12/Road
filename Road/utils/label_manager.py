# SPDX-License-Identifier: LGPL-2.1-or-later

"""
Base class for managing 3D labels in FreeCAD viewproviders
"""

import FreeCAD
from pivy import coin
import math


class LabelManager:
    """
    Centralized label management system for FreeCAD 3D view
    """
    
    def __init__(self, root_node):
        """
        Initialize label manager
        
        Args:
            root_node: Parent coin3d node to attach labels
        """
        # Default styling
        self.vertical_offset = 0.0
        self.horizontal_offset = 0.0

        self.labels = []
        
        self.font = coin.SoFont()
        self.material = coin.SoMaterial()
        self.label_group = coin.SoGroup()

        root_node.addChild(self.font)
        root_node.addChild(self.material)
        root_node.addChild(self.label_group)

    def add_label(self, position, text, side = "Left", spacing = 1, transformation = FreeCAD.Placement()):
        """
        Add a new 3D label with default styling
        
        Args:
            position: Tuple (x, y, z) for label position
            text: Label text to display
            justification: New justification value or None to keep current
            spacing: New spacing value or None to keep current
            
        Returns:
            dict: Label data including nodes for future updates
        """
        # Create label separator
        label_sep = coin.SoTransformSeparator()
        
        placement = position.add(
            transformation.Base)
        rot = coin.SbRotation(
            transformation.Rotation.Q)
        
        # Position transform
        transform = coin.SoTransform()
        transform.translation.setValue(placement)
        transform.rotation.setValue(rot)
        label_sep.addChild(transform)
        
        if not isinstance(text, list):
            text = [text]

        if side == "Left":
            justification = coin.SoAsciiText.LEFT
        elif side == "Right":
            justification = coin.SoAsciiText.RIGHT
        else:
            justification = coin.SoAsciiText.CENTER

        # Text node
        text_node = coin.SoAsciiText()
        text_node.string.setValues(text)
        text_node.justification.setValue(justification)   
        text_node.spacing.setValue(spacing)
        label_sep.addChild(text_node)

        empty = coin.SoTransformSeparator()

        lod = coin.SoLevelOfDetail()
        lod.addChild(label_sep)
        lod.addChild(empty)

        lod.screenArea.values = [250]

        # Add to group
        self.label_group.addChild(lod)
    
        # Store reference
        label_data = {
            'node': label_sep,
            'text': text_node,
            'transform': transform,
        }
        self.labels.append(label_data)
        
        return label_data
    
    def clear_labels(self):
        """Remove all labels"""
        self.label_group.removeAllChildren()
        self.labels.clear()
    
    def get_label_count(self):
        """
        Get number of labels
        
        Returns:
            int: Number of labels
        """
        return len(self.labels)

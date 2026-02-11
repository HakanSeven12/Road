# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Shape objects."""

from pivy import coin
from .view_geo_object import ViewProviderGeoObject

from ..variables import icons_path
from ..utils.get_group import create_project


class ViewProviderComponentShape(ViewProviderGeoObject):
    """This class is about Shape Object view features."""
    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "ComponentShape")

        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        super().attach(vobj)

        self.Object = vobj.Object

        self.draw_style = coin.SoDrawStyle()
        self.draw_style.style = coin.SoDrawStyle.FILLED
        self.draw_style.lineWidth = 1

        #-----------------------------------------------------------------
        # Faces
        #-----------------------------------------------------------------

        # Face view
        self.face_color = coin.SoBaseColor()
        self.face_color.rgb = (1.0, 1.0, 1.0)

        face_view = coin.SoGroup()
        face_view.addChild(self.draw_style)
        face_view.addChild(self.face_color)

        # Face data
        self.face_coords = coin.SoCoordinate3()
        self.faces = coin.SoIndexedFaceSet()

        face_data = coin.SoGroup()
        face_data.addChild(self.face_coords)
        face_data.addChild(self.faces)

        # Face group
        faces = coin.SoSeparator()
        faces.addChild(face_view)
        faces.addChild(face_data)

        #-------------------------------------------------------------
        # Labels
        #-------------------------------------------------------------

        self.font = coin.SoFont()
        self.font.size = 250
        self.location = coin.SoTranslation()
        self.label_color = coin.SoBaseColor()
        self.label_color.rgb = (1.0, 0.0, 0.0)
        self.text = coin.SoAsciiText()

        self.label = coin.SoAnnotation()
        self.label.addChild(self.font)
        self.label.addChild(self.location)
        self.label.addChild(self.label_color)
        self.label.addChild(self.text)

        #-----------------------------------------------------------------
        # Face
        #-----------------------------------------------------------------

        # Terrain group
        structure_selection = coin.SoType.fromName('SoFCSelection').createInstance()
        structure_selection.style = 'EMISSIVE_DIFFUSE'
        structure_selection.addChild(faces)
        structure_selection.addChild(self.label)

        self.standard.addChild(structure_selection)

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)
        
        if prop == "Shape":
            if obj.Shape.Faces:
                index = 0
                points, indexes = [], []
                for face in obj.Shape.Faces:
                    vertices, triangles = face.tessellate(1)
                    points.extend(vertices)
                    for tri in triangles:
                        indexes.extend([i + index for i in tri])
                        indexes.append(-1)
                    index += len(vertices)

                #Set contour system.
                self.face_coords.point.values = points
                self.faces.coordIndex.values = indexes

                component = obj.getParentGroup()
                if component:
                    side = coin.SoAsciiText.LEFT if component.Side == "Right" else coin.SoAsciiText.RIGHT
                    self.text.justification = side
                    self.location.translation = obj.Shape.CenterOfMass
                    self.text.string.setValues([obj.Label])
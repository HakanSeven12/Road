# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Shape objects."""

import FreeCAD
from pivy import coin

from ..variables import icons_path
from ..utils.get_group import georigin


class ViewProviderComponentShape:
    """This class is about Shape Object view features."""
    def __init__(self, vobj):
        """Set view properties."""

        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
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

        self.structure = coin.SoGeoSeparator()
        self.structure.addChild(structure_selection)

        vobj.addDisplayMode(self.structure, "Faces")

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        if prop == "Placement":
            placement = obj.getPropertyByName(prop)
            origin = georigin()
            geo_system = ["UTM", origin.UtmZone, "FLAT"]

            self.structure.geoSystem.setValues(geo_system)
            self.structure.geoCoords.setValue(placement.Base.x, placement.Base.y, placement.Base.z)

        elif prop == "Shape":
            shape = obj.getPropertyByName(prop).copy()
            shape.Placement.move(obj.Placement.Base.negative())

            index = 0
            points, indexes = [], []
            for face in shape.Faces:
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
                self.location.translation = shape.CenterOfMass
                self.text.string.setValues([obj.Label])


    def getDisplayModes(self,vobj):
        """Return a list of display modes."""
        modes = ["Faces"]
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "Faces"

    def setDisplayMode(self,mode):
        """Map the display mode defined in attach with 
        those defined in getDisplayModes."""
        return mode

    def getIcon(self):
        """Return object treeview icon."""
        return icons_path + "/ComponentShape.svg"

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
